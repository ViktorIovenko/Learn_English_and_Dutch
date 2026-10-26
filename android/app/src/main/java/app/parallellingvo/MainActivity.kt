package app.parallellingvo

import app.parallellingvo.data.api.UserInfo
import app.parallellingvo.ui.settings.LanguageSettingsFragment

import android.graphics.Matrix
import android.graphics.RectF
import androidx.core.view.doOnLayout
import android.Manifest
import android.content.Intent
import android.net.Uri
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.appcompat.app.AppCompatDelegate
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.content.ContextCompat
import androidx.core.os.LocaleListCompat
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.NavOptions
import androidx.navigation.NavController
import androidx.navigation.fragment.NavHostFragment
import androidx.navigation.ui.setupWithNavController
import com.google.android.material.bottomnavigation.BottomNavigationView
import app.parallellingvo.R
import app.parallellingvo.utils.NetworkResult
import app.parallellingvo.databinding.ActivityMainBinding
import app.parallellingvo.utils.familyErrorMessage
import app.parallellingvo.utils.ChildLearningReminder
import app.parallellingvo.utils.navigateToTab
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.collect
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.delay
import app.parallellingvo.utils.PendingAndroidAuth
import app.parallellingvo.utils.newAuthVerifier
import app.parallellingvo.utils.authChallenge
import app.parallellingvo.utils.normalizedAuthServer
import app.parallellingvo.utils.SessionBoundary
import app.parallellingvo.data.api.AndroidAuthStartRequest
import app.parallellingvo.data.api.AndroidAuthExchangeRequest
import app.parallellingvo.data.api.TelegramNativeRequest
import org.telegram.login.TelegramLogin
import kotlinx.coroutines.launch

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private lateinit var navController: NavController
    /** Family invitation opened before sign-in; resumed once the user is logged in. */
    private var pendingFamilyInvitation: String? = null
    private var startingBrowserAuth = false
    private var nativeCallbackFlowId: String? = null
    private var hasResumedOnce = false
    private val notificationPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        if (granted) ChildLearningReminder.scheduleNext(this)
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        val prefs = (application as ParallelLingvoApp).preferencesManager
        AppCompatDelegate.setDefaultNightMode(kotlinx.coroutines.runBlocking { prefs.themeMode.first() })
        applyStoredLocale()
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        setupThemeButton()
        setupBrandImages()

        val navHostFragment = supportFragmentManager
            .findFragmentById(R.id.nav_host_fragment) as NavHostFragment
        navController = navHostFragment.navController

        val bottomNav: BottomNavigationView = binding.bottomNavigation
        bottomNav.setupWithNavController(navController)
        setParentNavigationVisible(false)
        binding.adminPreviewIndicator.setOnClickListener { navController.navigateToTab(R.id.languageSettingsFragment) }
        lifecycleScope.launch {
            repeatOnLifecycle(Lifecycle.State.STARTED) {
                kotlinx.coroutines.flow.combine((application as ParallelLingvoApp).repository.currentUser,
                    prefs.userId) { user, uid -> user?.takeIf { it.userId == uid } }.collect { user ->
                    if (user != null) updateParentNavigation(user)
                    else {
                        binding.adminPreviewIndicator.visibility = android.view.View.GONE
                        setParentNavigationVisible(false)
                    }
                }
            }
        }

        // Hide bottom nav on study/auth screens
        navController.addOnDestinationChangedListener { _, destination, _ ->
            binding.appHeader.visibility = if (destination.id == R.id.authFragment) {
                android.view.View.GONE
            } else android.view.View.VISIBLE
            when (destination.id) {
                R.id.learnFragment, R.id.difficultFragment, R.id.authFragment,
                R.id.accountTypeFragment ->
                    bottomNav.visibility = android.view.View.GONE
                else ->
                    bottomNav.visibility = android.view.View.VISIBLE
            }
            if (destination.id != R.id.authFragment) resumePendingFamilyInvitation()
        }

        val handledDeepLink = handleIncomingIntent(intent)
        observePendingAuth()

        // Check if user is logged in, redirect to auth if not
        lifecycleScope.launch {
            val prefs = (application as ParallelLingvoApp).preferencesManager
            val userId = prefs.userId.first()
            val hasSession = userId.isNotBlank() && prefs.authToken.first().isNotBlank()
            // A pending browser attempt is not a session, including after process recreation.
            if (!hasSession) {
                ChildLearningReminder.setEnabled(this@MainActivity, false)
                navigateAfterAuth(R.id.authFragment)
                return@launch
            }
            if (!handledDeepLink && prefs.pendingAuth.first() == null) {
                if (userId.isBlank() && navController.currentDestination?.id != R.id.authFragment) {
                    ChildLearningReminder.setEnabled(this@MainActivity, false)
                    navController.navigate(R.id.authFragment)
                } else if (userId.isNotBlank()) {
                    val me = (application as ParallelLingvoApp).repository.getMe()
                    if (me is NetworkResult.Success) {
                        syncChildLearningReminder(me.data.accountType)
                        updateParentNavigation(me.data)
                        val target = when {
                            me.data.needsAccountType -> R.id.accountTypeFragment
                            navController.currentDestination?.id == R.id.authFragment -> R.id.lessonsFragment
                            else -> null
                        }
                        if (target != null && navController.currentDestination?.id != target) {
                            navController.navigate(target)
                        }
                    } else if (me is NetworkResult.Error && me.code == 401) {
                        prefs.clearUser()
                        (application as ParallelLingvoApp).repository.clearAuthCookies()
                        navigateAfterAuth(R.id.authFragment)
                    } else {
                        showAuthFailure()
                    }
                }
            }
        }
    }

    fun setupBrandImages(
        mark: android.widget.ImageView = binding.imgBrandMark,
        name: android.widget.ImageView = binding.imgBrandName,
        wordmarkHeightDp: Float = 23f
    ) {
        fun fitArtwork(image: android.widget.ImageView, artworkBounds: RectF, visibleHeightDp: Float? = null) {
            image.doOnLayout { view ->
                val targetHeight = visibleHeightDp?.let { it * resources.displayMetrics.density }
                    ?.coerceAtMost(view.height.toFloat()) ?: view.height.toFloat()
                image.imageMatrix = Matrix().apply {
                    setRectToRect(
                        artworkBounds,
                        RectF(0f, (view.height - targetHeight) / 2f,
                            view.width.toFloat(), (view.height + targetHeight) / 2f),
                        Matrix.ScaleToFit.CENTER
                    )
                }
            }
        }
        // Visible artwork bounds ignore transparent margins and faint shadows.
        fitArtwork(mark, RectF(4f, 159f, 378f, 541f))
        val isNight = resources.configuration.uiMode and
            android.content.res.Configuration.UI_MODE_NIGHT_MASK == android.content.res.Configuration.UI_MODE_NIGHT_YES
        fitArtwork(name, if (isNight) {
            RectF(36f, 200f, 2145f, 528f)
        } else {
            RectF(52f, 217f, 2124f, 530f)
        }, visibleHeightDp = wordmarkHeightDp)
    }

    private fun setupThemeButton() {
        val modes = intArrayOf(
            AppCompatDelegate.MODE_NIGHT_FOLLOW_SYSTEM,
            AppCompatDelegate.MODE_NIGHT_NO,
            AppCompatDelegate.MODE_NIGHT_YES
        )
        val labels = arrayOf(getString(R.string.theme_system), getString(R.string.theme_light), getString(R.string.theme_dark))
        val selected = modes.indexOf(AppCompatDelegate.getDefaultNightMode()).coerceAtLeast(0)
        val icons = intArrayOf(
            R.drawable.ic_theme_system_24,
            R.drawable.ic_theme_light_24,
            R.drawable.ic_theme_dark_24
        )
        binding.btnTheme.setImageResource(icons[selected])
        binding.btnTheme.contentDescription = getString(R.string.theme_current, labels[selected])
        binding.btnTheme.setOnClickListener {
            val nextMode = modes[(selected + 1) % modes.size]
            binding.btnTheme.isEnabled = false
            lifecycleScope.launch {
                try {
                    (application as ParallelLingvoApp).preferencesManager.saveThemeMode(nextMode)
                    AppCompatDelegate.setDefaultNightMode(nextMode)
                    setupThemeButton()
                } finally {
                    binding.btnTheme.isEnabled = true
                }
            }
        }
    }

    private fun applyStoredLocale() {
        val prefs = (application as ParallelLingvoApp).preferencesManager
        val languageCode = kotlinx.coroutines.runBlocking { prefs.uiLanguageOverride.first() }
        val locales = if (languageCode.isBlank()) {
            LocaleListCompat.getEmptyLocaleList()
        } else {
            LocaleListCompat.forLanguageTags(languageCode)
        }
        AppCompatDelegate.setApplicationLocales(locales)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        handleIncomingIntent(intent)
    }

    private fun handleIncomingIntent(intent: Intent?): Boolean =
        handleNativeTelegramIntent(intent) || handleTelegramAuthIntent(intent) || handleFamilyLinkIntent(intent)

    private fun handleNativeTelegramIntent(intent: Intent?): Boolean {
        val uri = intent?.data ?: return false
        val expectedHost = BuildConfig.TELEGRAM_LOGIN_HOST
        if (uri.scheme != "https" || uri.host != expectedHost || uri.path != "/tglogin" ||
            uri.port != -1 || uri.userInfo != null) return false
        intent.data = null
        lifecycleScope.launch {
            val prefs = (application as ParallelLingvoApp).preferencesManager
            val flow = prefs.pendingAuth.first()
            if (flow == null || flow.nativeClientId != BuildConfig.TELEGRAM_CLIENT_ID ||
                flow.provider != "telegram" || System.currentTimeMillis() - flow.createdAt > 3600000L) {
                showAuthFailure(R.string.invalid_auth_link)
                return@launch
            }
            if (nativeCallbackFlowId == flow.flowId || !flow.nativeIdToken.isNullOrBlank()) return@launch
            nativeCallbackFlowId = flow.flowId
            // The adapted SDK restores PKCE from the encrypted pending attempt.
            try {
                TelegramLogin.init(BuildConfig.TELEGRAM_CLIENT_ID, "https://$expectedHost/tglogin", listOf("profile"))
                TelegramLogin.handleLoginResponse(uri, onSuccess = { data ->
                    lifecycleScope.launch {
                        if (prefs.pendingAuth.first()?.flowId == flow.flowId) {
                            prefs.savePendingAuth(flow.copy(nativeIdToken = data.idToken))
                        }
                    }
                }, onError = {
                    lifecycleScope.launch {
                        if (prefs.pendingAuth.first()?.flowId == flow.flowId) {
                            prefs.savePendingAuth(null)
                            showAuthFailure()
                        }
                    }
                }, savedVerifier = flow.verifier)
            } catch (_: IllegalArgumentException) {
                prefs.savePendingAuth(null)
                showAuthFailure(R.string.auth_expired)
            }
        }
        return true
    }

    private fun handleTelegramAuthIntent(intent: Intent?): Boolean {
        val data = intent?.data ?: return false
        val appReturn = data.scheme == "https" && data.host == Uri.parse(BuildConfig.BASE_URL).host &&
            data.path == "/auth/android/return"
        if (!appReturn && (data.scheme != "learnwords" || data.host != "auth")) return false
        // Do not replay a callback on rotation or a restored Activity.
        intent.data = null
        val flowId = data.getQueryParameter("flow").orEmpty()
        if (appReturn) return flowId.isNotBlank()
        if (flowId.isNotBlank()) return true // The resumed observer exchanges only our persisted attempt.
        if (data.getQueryParameter("error") != null) {
            showAuthFailure()
            return true
        }
        // Only a locally initiated attempt with its persisted verifier may sign in.
        // A valid bearer supplied by another app/link proves no login intent here.
        showAuthFailure(R.string.invalid_auth_link)
        return true
    }

    fun startBrowserAuth(provider: String, mode: String, serverUrl: String) {
        if (startingBrowserAuth) return
        val server = normalizedAuthServer(serverUrl)
        if (server == null) {
            showAuthFailure(R.string.invalid_auth_link)
            return
        }
        startingBrowserAuth = true
        lifecycleScope.launch {
            val app = application as ParallelLingvoApp
            try {
                app.preferencesManager.savePendingAuth(null)
                val verifier = newAuthVerifier()
                val request = AndroidAuthStartRequest(provider, authChallenge(verifier), resources.configuration.locales[0].language, mode,
                    if (provider == "telegram") "native" else "browser")
                when (val result = app.repository.startAndroidAuth(server, request)) {
                    is NetworkResult.Success -> {
                        val flow = result.data.flowId.orEmpty()
                        val url = Uri.parse(result.data.browserUrl.orEmpty())
                        val origin = normalizedAuthServer("${url.scheme}://${url.authority}")
                        if (!result.data.ok || flow.isBlank() || origin != server || url.path != "/auth/$provider") {
                            showAuthFailure()
                            return@launch
                        }
                        if (provider == "telegram" && (result.data.clientId != BuildConfig.TELEGRAM_CLIENT_ID ||
                            result.data.redirectUri != "https://${BuildConfig.TELEGRAM_LOGIN_HOST}/tglogin")) {
                            showAuthFailure()
                            return@launch
                        }
                        app.preferencesManager.savePendingAuth(PendingAndroidAuth(
                            flow, verifier, server, provider, linking = mode == "link",
                            ownerUserId = if (mode == "link") app.preferencesManager.userId.first() else "",
                            nativeClientId = if (provider == "telegram") result.data.clientId else null
                        ))
                        if (provider == "telegram") {
                            TelegramLogin.init(BuildConfig.TELEGRAM_CLIENT_ID, result.data.redirectUri!!, listOf("profile"))
                            TelegramLogin.startLogin(this@MainActivity, verifier, onError = {
                                lifecycleScope.launch {
                                    if (app.preferencesManager.pendingAuth.first()?.flowId == flow) {
                                        app.preferencesManager.savePendingAuth(null)
                                        showAuthFailure(R.string.telegram_unavailable)
                                    }
                                }
                            })
                            return@launch
                        }
                        val browser = Intent(Intent.ACTION_VIEW, url).apply {
                            // Request a browser Custom Tab without adding a dependency.
                            putExtras(Bundle().apply { putBinder("android.support.customtabs.extra.SESSION", null) })
                            putExtra("android.support.customtabs.extra.SHARE_MENU_ITEM", false)
                            addFlags(Intent.FLAG_ACTIVITY_NO_HISTORY)
                        }
                        startActivity(browser)
                    }
                    else -> showAuthFailure()
                }
            } catch (_: android.content.ActivityNotFoundException) {
                app.preferencesManager.savePendingAuth(null)
                showAuthFailure()
            } finally { startingBrowserAuth = false }
        }
    }

    private fun observePendingAuth() {
        lifecycleScope.launch {
            repeatOnLifecycle(Lifecycle.State.RESUMED) {
                val app = application as ParallelLingvoApp
                app.preferencesManager.pendingAuth.distinctUntilChanged().collect { flow ->
                    if (flow == null) {
                        // Native email/Google sign-in owns its navigation. Reacting to
                        // its saved session here would race the AuthFragment collector.
                        return@collect
                    }
                    if (System.currentTimeMillis() - flow.createdAt > 3600000L) {
                        app.preferencesManager.savePendingAuth(null)
                        showAuthFailure(R.string.auth_expired)
                        return@collect
                    }
                    if (app.preferencesManager.serverUrl.first().trimEnd('/') != flow.serverUrl) {
                        app.preferencesManager.savePendingAuth(null)
                        showAuthFailure(R.string.invalid_auth_link)
                        return@collect
                    }
                    while (app.preferencesManager.pendingAuth.first()?.flowId == flow.flowId) {
                        if (flow.linking && app.preferencesManager.userId.first() != flow.ownerUserId) {
                            app.preferencesManager.savePendingAuth(null)
                            showAuthFailure(R.string.invalid_auth_link)
                            break
                        }
                        val current = app.preferencesManager.pendingAuth.first()
                        val nativeToken = current?.nativeIdToken
                        if (current != null && !nativeToken.isNullOrBlank()) {
                            when (val verified = app.repository.verifyNativeTelegram(
                                TelegramNativeRequest(flow.flowId, flow.verifier, nativeToken))) {
                                is NetworkResult.Success -> {
                                    if (verified.data.ok != true) {
                                        app.preferencesManager.savePendingAuth(null)
                                        showAuthFailure()
                                        break
                                    }
                                    if (app.preferencesManager.pendingAuth.first()?.flowId != flow.flowId) break
                                    app.preferencesManager.savePendingAuth(current.copy(nativeIdToken = null))
                                }
                                is NetworkResult.Error -> {
                                    if (verified.code in listOf(400, 401, 403, 409, 410)) {
                                        app.preferencesManager.savePendingAuth(null)
                                        showAuthFailure()
                                        break
                                    }
                                    delay(1500)
                                    continue
                                }
                                else -> { delay(1500); continue }
                            }
                        }
                        when (val result = app.repository.exchangeAndroidAuth(AndroidAuthExchangeRequest(flow.flowId, flow.verifier))) {
                            is NetworkResult.Success -> {
                                val response = result.data
                                if (response.pending) { delay(1500); continue }
                                val uid = response.userId.orEmpty()
                                val token = response.token.orEmpty()
                                val ownerMatches = !flow.linking || (uid == flow.ownerUserId &&
                                    app.preferencesManager.userId.first() == flow.ownerUserId)
                                if (response.ok && uid.isNotBlank() && token.isNotBlank() && response.provider == flow.provider && ownerMatches) {
                                    val installed = SessionBoundary.withSession {
                                        val pending = app.preferencesManager.pendingAuth.first()
                                        if (pending?.flowId != flow.flowId || pending.verifier != flow.verifier ||
                                            (flow.linking && app.preferencesManager.userId.first() != flow.ownerUserId)) {
                                            return@withSession false
                                        }
                                        app.preferencesManager.saveLoginSession(uid, token,
                                            if (flow.linking) app.preferencesManager.authMethod.first()
                                            else if (flow.provider == "email") "Email" else "Telegram", flow.serverUrl)
                                        true
                                    }
                                    if (!installed) break
                                    if (flow.linking) {
                                        navigateAfterAuth(R.id.languageSettingsFragment)
                                        val host = supportFragmentManager.findFragmentById(R.id.nav_host_fragment) as? NavHostFragment
                                        (host?.childFragmentManager?.primaryNavigationFragment as? LanguageSettingsFragment)?.refreshContactMethods()
                                        Toast.makeText(this@MainActivity, getString(R.string.account_link_success), Toast.LENGTH_LONG).show()
                                    } else completeAndroidLogin()
                                } else {
                                    app.preferencesManager.savePendingAuth(null)
                                    showAuthFailure()
                                }
                                break
                            }
                            is NetworkResult.Error -> {
                                if (result.code in listOf(400,401,403,409,410)) app.preferencesManager.savePendingAuth(null)
                                showAuthFailure(if (flow.linking) R.string.account_link_failed else R.string.auth_failed)
                                break // A network failure keeps the attempt for the next resume.
                            }
                            else -> break
                        }
                    }
                }
            }
        }
    }

    private suspend fun completeAndroidLogin() {
        val app = application as ParallelLingvoApp
        val me = app.repository.getMe()
        val target = if (me is NetworkResult.Success) {
            syncChildLearningReminder(me.data.accountType)
            updateParentNavigation(me.data)
            when {
                me.data.needsAccountType -> R.id.accountTypeFragment
                else -> R.id.lessonsFragment
            }
        } else if (me is NetworkResult.Error && me.code == 401) {
            app.preferencesManager.clearUser()
            app.repository.clearAuthCookies()
            Toast.makeText(this, getString(R.string.auth_expired), Toast.LENGTH_LONG).show()
            navigateAfterAuth(R.id.authFragment)
            return
        } else {
            showAuthFailure()
            return
        }
        navigateAfterAuth(target)
    }

    private fun showAuthFailure(message: Int = R.string.auth_failed) {
        navigateAfterAuth(R.id.authFragment)
        Toast.makeText(this, getString(message), Toast.LENGTH_LONG).show()
    }

    private fun navigateAfterAuth(destination: Int) {
        if (navController.currentDestination?.id == destination) return
        navController.navigate(destination, null, NavOptions.Builder()
            .setPopUpTo(navController.graph.id, false).setLaunchSingleTop(true).build())
    }

    private fun handleFamilyLinkIntent(intent: Intent?): Boolean {
        val data = intent?.data ?: return false
        if (data.scheme != "https" || data.host != "app.parallellingvo.app" ||
            data.path !in listOf("/family/link", "/family/connect") || data.userInfo != null ||
            data.port !in listOf(-1, 443)) {
            return false
        }
        intent.data = null
        openFamilyInvitation(data.toString())
        return true
    }

    private fun resumePendingFamilyInvitation() {
        val value = pendingFamilyInvitation ?: return
        lifecycleScope.launch {
            val app = application as ParallelLingvoApp
            if (app.preferencesManager.userId.first().isBlank()) return@launch
            if (pendingFamilyInvitation != value) return@launch
            pendingFamilyInvitation = null
            openFamilyInvitation(value)
        }
    }

    /**
     * Universal family invitation (QR / link / code): works for both directions —
     * a child accepting a parent's invite and a parent accepting a child's code.
     * The server decides the account type, so no extra steps are needed here.
     */
    fun openFamilyInvitation(value: String) {
        lifecycleScope.launch {
            val app = application as ParallelLingvoApp
            val owner = app.preferencesManager.userId.first()
            val ownerToken = app.preferencesManager.authToken.first()
            if (owner.isBlank() || ownerToken.isBlank()) {
                pendingFamilyInvitation = value
                Toast.makeText(this@MainActivity, getString(R.string.family_login_to_connect), Toast.LENGTH_LONG).show()
                if (navController.currentDestination?.id != R.id.authFragment) {
                    navController.navigate(R.id.authFragment)
                }
                return@launch
            }
            when (val preview = app.repository.previewFamilyInvitation(value)) {
                is NetworkResult.Success -> {
                    if (app.preferencesManager.userId.first() != owner ||
                        app.preferencesManager.authToken.first() != ownerToken) return@launch
                    val invitation = preview.data
                    val name = invitation.displayName.orEmpty()
                    val note = when {
                        invitation.becomesChild -> "\n\n" + getString(R.string.family_becomes_child)
                        invitation.becomesParent -> "\n\n" + getString(R.string.family_becomes_parent)
                        else -> ""
                    }
                    androidx.appcompat.app.AlertDialog.Builder(this@MainActivity)
                        .setTitle(R.string.family_invite_title)
                        .setMessage(getString(R.string.family_invite_confirm, name) + note)
                        .setPositiveButton(R.string.family_invite_accept) { _, _ ->
                            acceptFamilyInvitation(invitation.code.orEmpty(), invitation.kind.orEmpty(), name, owner, ownerToken)
                        }
                        .setNegativeButton(R.string.cancel, null)
                        .show()
                }
                is NetworkResult.Error -> Toast.makeText(
                    this@MainActivity,
                    familyErrorMessage(preview.message),
                    Toast.LENGTH_LONG
                ).show()
                else -> Unit
            }
        }
    }

    private fun acceptFamilyInvitation(code: String, kind: String, name: String, owner: String, ownerToken: String) {
        lifecycleScope.launch {
            val app = application as ParallelLingvoApp
            val result = SessionBoundary.withSession {
                if (app.preferencesManager.userId.first() != owner ||
                    app.preferencesManager.authToken.first() != ownerToken) return@withSession null
                app.repository.acceptFamilyInvitation(code, kind)
            }
            if (result == null) {
                Toast.makeText(this@MainActivity, getString(R.string.family_invalid_link), Toast.LENGTH_LONG).show()
                return@launch
            }
            when (result) {
                is NetworkResult.Success -> {
                    Toast.makeText(this@MainActivity, getString(R.string.family_linked_to, name), Toast.LENGTH_LONG).show()
                    val me = app.repository.getMe()
                    if (me is NetworkResult.Success) {
                        syncChildLearningReminder(me.data.accountType)
                        updateParentNavigation(me.data)
                    }
                    val destination = if (kind == "family" && (me as? NetworkResult.Success)?.data?.canManageFamily == true) R.id.parentDashboardFragment else R.id.lessonsFragment
                    if (navController.currentDestination?.id != destination) {
                        navController.navigateToTab(destination)
                    }
                }
                is NetworkResult.Error -> Toast.makeText(
                    this@MainActivity,
                    familyErrorMessage(result.message),
                    Toast.LENGTH_LONG
                ).show()
                else -> Unit
            }
        }
    }

    fun updateParentNavigation(user: UserInfo) {
        val preview = user.planState?.preview
        binding.adminPreviewIndicator.visibility = if (user.isAdmin == true && !preview.isNullOrBlank())
            android.view.View.VISIBLE else android.view.View.GONE
        binding.adminPreviewIndicator.text = getString(R.string.admin_preview_indicator, preview.orEmpty().uppercase())
        setParentNavigationVisible(user.canManageFamily)
        if (!user.canManageFamily && navController.currentDestination?.id == R.id.parentDashboardFragment) {
            navController.navigateToTab(R.id.lessonsFragment)
        }
    }

    suspend fun refreshParentNavigation(): Boolean {
        val app = application as ParallelLingvoApp
        if (app.preferencesManager.authToken.first().isBlank()) {
            setParentNavigationVisible(false)
            return false
        }
        return when (val me = app.repository.getMe()) {
            is NetworkResult.Success -> {
                updateParentNavigation(me.data)
                me.data.canManageFamily
            }
            is NetworkResult.Error -> {
                if (me.code == 401) setParentNavigationVisible(false)
                false
            }
            else -> false
        }
    }

    override fun onResume() {
        super.onResume()
        // The first launch already loads /api/me in onCreate or during sign-in.
        if (hasResumedOnce) lifecycleScope.launch { refreshParentNavigation() }
        hasResumedOnce = true
    }

    fun setParentNavigationVisible(visible: Boolean) {
        if (!::binding.isInitialized) return
        binding.bottomNavigation.menu.findItem(R.id.parentDashboardFragment)?.isVisible = visible
    }

    fun syncChildLearningReminder(accountType: String?) {
        val isChild = accountType == "child"
        ChildLearningReminder.setEnabled(this, isChild)
        if (isChild && Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
            ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) !=
            PackageManager.PERMISSION_GRANTED &&
            ChildLearningReminder.shouldRequestPermission(this)) {
            ChildLearningReminder.markPermissionRequested(this)
            notificationPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
        }
    }

    override fun onSupportNavigateUp(): Boolean {
        return navController.navigateUp() || super.onSupportNavigateUp()
    }
}
