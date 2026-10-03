package com.learnwords.app

import android.Manifest
import android.content.Intent
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
import androidx.navigation.NavController
import androidx.navigation.fragment.NavHostFragment
import androidx.navigation.ui.setupWithNavController
import com.google.android.material.bottomnavigation.BottomNavigationView
import com.learnwords.app.R
import com.learnwords.app.utils.NetworkResult
import com.learnwords.app.databinding.ActivityMainBinding
import com.learnwords.app.utils.familyErrorMessage
import com.learnwords.app.utils.ChildLearningReminder
import com.learnwords.app.utils.navigateToTab
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private lateinit var navController: NavController
    private val notificationPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        if (granted) ChildLearningReminder.scheduleNext(this)
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        applyStoredLocale()
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        val navHostFragment = supportFragmentManager
            .findFragmentById(R.id.nav_host_fragment) as NavHostFragment
        navController = navHostFragment.navController

        val bottomNav: BottomNavigationView = binding.bottomNavigation
        bottomNav.setupWithNavController(navController)
        setParentNavigationVisible(false)

        // Hide bottom nav on study/auth screens
        navController.addOnDestinationChangedListener { _, destination, _ ->
            when (destination.id) {
                R.id.learnFragment, R.id.difficultFragment, R.id.authFragment,
                R.id.accountTypeFragment ->
                    bottomNav.visibility = android.view.View.GONE
                else ->
                    bottomNav.visibility = android.view.View.VISIBLE
            }
        }

        val handledDeepLink = handleIncomingIntent(intent)

        // Check if user is logged in, redirect to auth if not
        lifecycleScope.launch {
            val prefs = (application as LearnWordsApp).preferencesManager
            val userId = prefs.userId.first()
            if (!handledDeepLink) {
                if (userId.isBlank() && navController.currentDestination?.id != R.id.authFragment) {
                    ChildLearningReminder.setEnabled(this@MainActivity, false)
                    navController.navigate(R.id.authFragment)
                } else if (userId.isNotBlank()) {
                    val me = (application as LearnWordsApp).repository.getMe()
                    if (me is NetworkResult.Success) {
                        syncChildLearningReminder(me.data.accountType)
                        setParentNavigationVisible(me.data.isParent)
                        if (me.data.needsAccountType &&
                            navController.currentDestination?.id != R.id.accountTypeFragment) {
                            navController.navigate(R.id.accountTypeFragment)
                        } else if (!hasSubscriptionAccess(me.data) &&
                            navController.currentDestination?.id != R.id.subscriptionFragment) {
                            navController.navigate(R.id.subscriptionFragment)
                        }
                    }
                }
            }
        }
    }

    private fun applyStoredLocale() {
        val prefs = (application as LearnWordsApp).preferencesManager
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
        handleTelegramAuthIntent(intent) || handleFamilyLinkIntent(intent)

    private fun handleTelegramAuthIntent(intent: Intent?): Boolean {
        val data = intent?.data ?: return false
        if (data.scheme != "learnwords" || data.host != "auth") return false

        val token = data.getQueryParameter("auth").orEmpty()
        val serverUrl = data.getQueryParameter("server").orEmpty()
        if (token.isBlank() || serverUrl.isBlank()) {
            Toast.makeText(this, getString(R.string.invalid_auth_link), Toast.LENGTH_SHORT).show()
            return true
        }

        lifecycleScope.launch {
            val app = application as LearnWordsApp
            when (val result = app.repository.loginWithTelegramToken(serverUrl, token)) {
                is NetworkResult.Success -> {
                    val userId = result.data.userId.orEmpty()
                    if (userId.isNotBlank()) {
                        app.preferencesManager.saveUserId(userId)
                        app.preferencesManager.saveAuthToken(result.data.token.orEmpty())
                        app.preferencesManager.saveAuthMethod("Telegram")
                        Toast.makeText(this@MainActivity, getString(R.string.login_success), Toast.LENGTH_SHORT).show()
                        val me = app.repository.getMe()
                        if (me is NetworkResult.Success) {
                            syncChildLearningReminder(me.data.accountType)
                            setParentNavigationVisible(me.data.isParent)
                        }
                        val destination = when {
                            me is NetworkResult.Success && me.data.needsAccountType -> R.id.accountTypeFragment
                            me !is NetworkResult.Success || !hasSubscriptionAccess(me.data) -> R.id.subscriptionFragment
                            else -> R.id.lessonsFragment
                        }
                        if (navController.currentDestination?.id != destination) {
                            navController.navigate(destination)
                        }
                    } else {
                        Toast.makeText(this@MainActivity, getString(R.string.server_user_id_missing), Toast.LENGTH_SHORT).show()
                    }
                }
                is NetworkResult.Error -> {
                    Toast.makeText(this@MainActivity, result.message, Toast.LENGTH_LONG).show()
                    if (navController.currentDestination?.id != R.id.authFragment) {
                        navController.navigate(R.id.authFragment)
                    }
                }
                else -> Unit
            }
        }
        return true
    }

    private fun handleFamilyLinkIntent(intent: Intent?): Boolean {
        val data = intent?.data ?: return false
        if (data.scheme != "https" || data.host != "app.parallellingvo.app" || data.path != "/family/link") {
            return false
        }
        val token = data.getQueryParameter("token").orEmpty()
        if (token.isBlank()) {
            Toast.makeText(this, getString(R.string.family_invalid_link), Toast.LENGTH_LONG).show()
            return true
        }
        lifecycleScope.launch {
            val app = application as LearnWordsApp
            if (app.preferencesManager.userId.first().isBlank()) {
                Toast.makeText(this@MainActivity, getString(R.string.login_title), Toast.LENGTH_LONG).show()
                if (navController.currentDestination?.id != R.id.authFragment) {
                    navController.navigate(R.id.authFragment)
                }
                return@launch
            }
            when (val result = app.repository.linkChild(token)) {
                is NetworkResult.Success -> {
                    setParentNavigationVisible(true)
                    val name = result.data.child?.displayName.orEmpty()
                    Toast.makeText(
                        this@MainActivity,
                        getString(R.string.family_linked_to, name),
                        Toast.LENGTH_LONG
                    ).show()
                    if (navController.currentDestination?.id != R.id.parentDashboardFragment) {
                        navController.navigateToTab(R.id.parentDashboardFragment)
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
        return true
    }

    fun setParentNavigationVisible(visible: Boolean) {
        if (!::binding.isInitialized) return
        binding.bottomNavigation.menu.findItem(R.id.parentDashboardFragment)?.isVisible = visible
    }

    private fun hasSubscriptionAccess(user: com.learnwords.app.data.api.UserInfo): Boolean =
        user.isAdmin == true || user.subscription?.isActive == true

    fun syncChildLearningReminder(accountType: String?) {
        val isChild = accountType == "child"
        if (accountType != null) {
            lifecycleScope.launch {
                (application as LearnWordsApp).preferencesManager.saveAccountTypeCache(accountType)
            }
        }
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
