package app.parallellingvo.ui.settings

import app.parallellingvo.utils.WordContentCache

import android.graphics.Bitmap
import android.graphics.Color
import android.net.Uri
import android.content.Intent
import android.app.Activity
import android.os.Bundle
import android.view.*
import android.widget.AdapterView
import android.widget.ArrayAdapter
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Button
import androidx.appcompat.app.AppCompatDelegate
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.os.LocaleListCompat
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.lifecycleScope
import androidx.navigation.NavOptions
import androidx.navigation.fragment.findNavController
import app.parallellingvo.BuildConfig
import app.parallellingvo.ParallelLingvoApp
import app.parallellingvo.MainActivity
import app.parallellingvo.R
import app.parallellingvo.databinding.FragmentLanguageSettingsBinding
import app.parallellingvo.utils.NetworkResult
import app.parallellingvo.utils.toast
import app.parallellingvo.utils.copyToClipboard
import app.parallellingvo.utils.familyErrorMessage
import app.parallellingvo.utils.navigateToTab
import app.parallellingvo.data.api.FamilyMemberDto
import app.parallellingvo.data.api.AndroidAuthStartRequest
import app.parallellingvo.data.api.EmailLinkRequest
import app.parallellingvo.utils.PendingAndroidAuth
import app.parallellingvo.utils.newAuthVerifier
import app.parallellingvo.utils.authChallenge
import app.parallellingvo.utils.normalizedAuthServer
import com.google.android.gms.auth.api.signin.GoogleSignIn
import com.google.android.gms.auth.api.signin.GoogleSignInOptions
import com.google.android.gms.common.api.ApiException
import com.google.zxing.BarcodeFormat
import com.google.zxing.MultiFormatWriter
import com.journeyapps.barcodescanner.ScanContract
import com.journeyapps.barcodescanner.ScanOptions
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.flow.launchIn
import kotlinx.coroutines.flow.onEach
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch

class LanguageSettingsFragment : Fragment() {

    private var _binding: FragmentLanguageSettingsBinding? = null
    private val binding get() = _binding!!
    private val viewModel: LanguageSettingsViewModel by viewModels()
    private lateinit var selectedAdapter: SelectedLanguageAdapter
    private var uiLanguageCodes: List<String?> = emptyList()
    private var ignoreUiLanguageSelection = false
    private var currentUiLanguageOverride: String? = null
    private var renderedUiLanguageSelectorKey: String = ""
    private var familyInvitationUrl: String = ""
    private var linkedGoogleEmail: String? = null
    private var googleLinkOwner: String = ""
    private var linkingGoogle = false
    private val googleLinkLauncher = registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
        if (result.resultCode == Activity.RESULT_CANCELED) {
            linkingGoogle = false
            loadMcpStatus()
            return@registerForActivityResult
        }
        val token = try {
            GoogleSignIn.getSignedInAccountFromIntent(result.data).getResult(ApiException::class.java)?.idToken
        } catch (_: ApiException) { null }
        viewLifecycleOwner.lifecycleScope.launch {
            try {
                val app = ParallelLingvoApp.instance
                if (token.isNullOrBlank() || googleLinkOwner != app.preferencesManager.userId.first()) {
                    context?.toast(getString(R.string.account_link_failed))
                    return@launch
                }
                when (val linked = app.repository.linkGoogleIdentity(token)) {
                    is NetworkResult.Success -> if (linked.data.ok == true) {
                        context?.toast(getString(R.string.account_link_success))
                    } else context?.toast(getString(R.string.account_link_failed))
                    is NetworkResult.Error -> context?.toast(contactLinkError(linked))
                    else -> Unit
                }
            } finally {
                linkingGoogle = false
                refreshContactMethods()
            }
        }
    }
    private val familyQrScanner = registerForActivityResult(ScanContract()) { result ->
        val value = result.contents.orEmpty()
        if (value.isNotBlank()) linkChildFromQr(value)
    }

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentLanguageSettingsBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onResume() {
        super.onResume()
        loadAccountIdentities()
        loadMcpStatus()
        loadSubscriptionSummary()
    }

    fun refreshContactMethods() {
        if (_binding == null) return
        loadAccountIdentities()
        loadMcpStatus()
        loadSubscriptionSummary()
    }

    override fun onSaveInstanceState(outState: Bundle) {
        outState.putString("google_link_owner", googleLinkOwner)
        super.onSaveInstanceState(outState)
    }

    private fun contactLinkError(error: NetworkResult.Error): String = when {
        error.message.contains("identity_conflict") -> getString(R.string.account_link_conflict)
        error.message.contains("weak_password") -> getString(R.string.account_email_password_hint)
        error.message.contains("password_mismatch") -> getString(R.string.account_email_password_mismatch)
        else -> getString(R.string.account_link_failed)
    }

    private fun startGoogleLink() {
        if (linkingGoogle) return
        linkingGoogle = true
        binding.btnLinkGoogle.isEnabled = false
        viewLifecycleOwner.lifecycleScope.launch {
            val app = ParallelLingvoApp.instance
            googleLinkOwner = app.preferencesManager.userId.first()
            val config = app.repository.getGoogleAuthConfig(app.preferencesManager.serverUrl.first())
            val client = (config as? NetworkResult.Success)?.data?.clientId
            if (client.isNullOrBlank() || googleLinkOwner != app.preferencesManager.userId.first()) {
                linkingGoogle = false
                context?.toast(getString(R.string.account_link_failed))
                loadMcpStatus()
                return@launch
            }
            val options = GoogleSignInOptions.Builder(GoogleSignInOptions.DEFAULT_SIGN_IN)
                .requestIdToken(client).requestEmail().build()
            runCatching { googleLinkLauncher.launch(GoogleSignIn.getClient(requireContext(), options).signInIntent) }
                .onFailure {
                    linkingGoogle = false
                    context?.toast(getString(R.string.account_link_failed))
                    loadMcpStatus()
                }
        }
    }

    private fun sendEmailLink() {
        val b = _binding ?: return
        val email = b.etLinkEmail.text.toString().trim()
        val password = b.etLinkPassword.text.toString()
        val confirmation = b.etLinkPasswordConfirmation.text.toString()
        b.tilLinkEmail.error = null
        b.tilLinkPassword.error = null
        b.tilLinkPasswordConfirmation.error = null
        if (!android.util.Patterns.EMAIL_ADDRESS.matcher(email).matches()) {
            b.tilLinkEmail.error = getString(R.string.auth_email_invalid)
            return
        }
        if (password.length !in 12..128) {
            b.tilLinkPassword.error = getString(R.string.account_email_password_hint)
            return
        }
        if (password != confirmation) {
            b.tilLinkPasswordConfirmation.error = getString(R.string.account_email_password_mismatch)
            return
        }
        b.btnEmailLinkSend.isEnabled = false
        viewLifecycleOwner.lifecycleScope.launch {
            val app = ParallelLingvoApp.instance
            val prefs = app.preferencesManager
            var flowId: String? = null
            try {
                val owner = prefs.userId.first()
                val server = normalizedAuthServer(prefs.serverUrl.first())
                if (server == null || owner.isBlank()) return@launch
                val verifier = newAuthVerifier()
                val language = resources.configuration.locales[0].language
                val started = app.repository.startAndroidAuth(server,
                    AndroidAuthStartRequest("email", authChallenge(verifier), language, "link"))
                val response = (started as? NetworkResult.Success)?.data
                val flow = response?.flowId.orEmpty()
                if (response?.ok != true || !Regex("[A-Za-z0-9_-]{43}").matches(flow) || owner != prefs.userId.first()) {
                    context?.toast(getString(R.string.account_link_failed))
                    return@launch
                }
                flowId = flow
                prefs.savePendingAuth(PendingAndroidAuth(flow, verifier, server, "email", linking = true, ownerUserId = owner))
                when (val sent = app.repository.requestEmailLink(EmailLinkRequest(flow, verifier, email, password, confirmation, language))) {
                    is NetworkResult.Success -> if (sent.data.ok == true) {
                        flowId = null // Keep the verifier until email confirmation is exchanged.
                        val current = _binding ?: return@launch
                        current.etLinkPassword.text?.clear()
                        current.etLinkPasswordConfirmation.text?.clear()
                        current.emailLinkForm.visibility = View.GONE
                        current.tvEmailLinkStatus.setText(R.string.account_email_sent)
                        current.tvEmailLinkStatus.visibility = View.VISIBLE
                    } else context?.toast(getString(R.string.account_link_failed))
                    is NetworkResult.Error -> {
                        if (sent.code == null) flowId = null // Delivery may have succeeded before a network timeout.
                        context?.toast(contactLinkError(sent))
                    }
                    else -> Unit
                }
            } finally {
                if (kotlin.coroutines.coroutineContext[kotlinx.coroutines.Job]?.isActive != false &&
                    flowId != null && prefs.pendingAuth.first()?.flowId == flowId) prefs.savePendingAuth(null)
                _binding?.btnEmailLinkSend?.isEnabled = true
            }
        }
    }

    private fun loadSubscriptionSummary() {
        familyInvitationUrl = ""
        _binding?.familyQrContent?.visibility = View.GONE
        viewLifecycleOwner.lifecycleScope.launch {
            val result = ParallelLingvoApp.instance.repository.getMe()
            val b = _binding ?: return@launch
            if (result !is NetworkResult.Success) {
                b.tvSettingsPlan.setText(R.string.subscription_title)
                b.tvSettingsSubscriptionSummary.setText(R.string.page_unavailable)
                b.btnSettingsSubscription.setText(R.string.plan_title)
                return@launch
            }
            val user = result.data
            val state = user.planState
            val plan = state?.plan ?: user.subscription?.plan
                ?: if (user.subscription?.isActive == true) "premium" else "free"
            val unlimited = user.subscription?.isUnlimited == true || plan == "admin"
            b.tvSettingsPlan.text = when {
                unlimited -> getString(R.string.plan_unlimited)
                plan == "family" -> "Family"
                plan == "premium" -> "Premium"
                else -> "Free"
            }
            b.tvSettingsSubscriptionSummary.text = buildList {
                if (plan == "free") add(getString(R.string.plan_f_learning))
                add(getString(if (state?.features?.ads ?: (plan == "free"))
                    R.string.plan_f_ads else R.string.plan_f_no_ads))
                if (state?.features?.aiPaid ?: (plan != "free")) add(getString(R.string.plan_f_ai))
                if (state?.features?.family ?: (plan == "family" || unlimited)) add(getString(R.string.plan_f_family))
            }.joinToString(" · ")
            b.btnSettingsSubscription.setText(if (plan == "free") R.string.settings_subscribe else R.string.plan_title)
            (activity as? MainActivity)?.updateParentNavigation(user)
            if (user.canManageFamily) {
                b.btnFamily.setText(R.string.family_refresh_link)
                loadFamilyInvitation()
            } else {
                b.btnFamily.setText(R.string.family_settings)
                b.tvFamilyInviteStatus.visibility = View.GONE
            }
        }
    }

    private suspend fun loadFamilyInvitation() {
        val current = _binding ?: return
        familyInvitationUrl = ""
        current.familyQrContent.visibility = View.GONE
        current.tvFamilyInviteStatus.visibility = View.VISIBLE
        current.tvFamilyInviteStatus.setText(R.string.loading)
        current.btnFamily.isEnabled = false
        val result = ParallelLingvoApp.instance.repository.getFamilyInviteCode()
        val b = _binding ?: return
        b.btnFamily.isEnabled = true
        when (result) {
            is NetworkResult.Success -> {
                val invitation = result.data
                val url = invitation.inviteUrl.orEmpty()
                if (!invitation.ok || url.isBlank()) {
                    b.tvFamilyInviteStatus.setText(R.string.family_invalid_link)
                    return
                }
                familyInvitationUrl = url
                b.ivFamilyQr.setImageBitmap(createQrBitmap(url, 720))
                b.tvFamilyInviteCode.text = invitation.shortCode.orEmpty()
                b.familyQrContent.visibility = View.VISIBLE
                b.tvFamilyInviteStatus.visibility = View.GONE
            }
            is NetworkResult.Error -> b.tvFamilyInviteStatus.text = requireContext().familyErrorMessage(result.message)
            else -> b.tvFamilyInviteStatus.setText(R.string.page_unavailable)
        }
    }

    private fun loadAccountIdentities() {
        val current = _binding ?: return
        current.btnLinkTelegram.isEnabled = false
        current.btnLinkEmail.isEnabled = false
        viewLifecycleOwner.lifecycleScope.launch {
            when (val result = ParallelLingvoApp.instance.repository.getAccountIdentities()) {
                is NetworkResult.Success -> {
                    val b = _binding ?: return@launch
                    if (!result.data.ok) {
                        b.tvTelegramIdentity.setText(R.string.page_unavailable)
                        b.tvEmailIdentity.setText(R.string.page_unavailable)
                        return@launch
                    }
                    b.tvTelegramIdentity.setText(if (result.data.telegramLinked) R.string.account_linked else R.string.account_not_linked)
                    b.tvEmailIdentity.text = result.data.email ?: getString(R.string.account_not_linked)
                    b.btnLinkTelegram.visibility = if (result.data.telegramLinked) View.GONE else View.VISIBLE
                    b.btnLinkEmail.visibility = if (result.data.email != null) View.GONE else View.VISIBLE
                    if (result.data.email != null) {
                        b.emailLinkForm.visibility = View.GONE
                        b.tvEmailLinkStatus.visibility = View.GONE
                    }
                    b.btnLinkTelegram.isEnabled = result.data.ok
                    b.btnLinkEmail.isEnabled = result.data.ok
                }
                else -> {
                    _binding?.tvTelegramIdentity?.setText(R.string.page_unavailable)
                    _binding?.tvEmailIdentity?.setText(R.string.page_unavailable)
                }
            }
        }
    }

    private fun linkLoginProvider(provider: String) {
        viewLifecycleOwner.lifecycleScope.launch {
            val server = ParallelLingvoApp.instance.preferencesManager.serverUrl.first()
            (activity as? MainActivity)?.startBrowserAuth(provider, "link", server)
        }
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        googleLinkOwner = savedInstanceState?.getString("google_link_owner").orEmpty()
        binding.btnSettingsSubscription.setOnClickListener {
            findNavController().navigateToTab(R.id.subscriptionFragment)
        }
        binding.tvEmailMethod.text = getString(R.string.auth_email_address) + " / " + getString(R.string.hint_password)
        binding.btnLinkTelegram.setOnClickListener { linkLoginProvider("telegram") }
        binding.btnLinkGoogle.setOnClickListener { startGoogleLink() }
        binding.btnLinkEmail.setOnClickListener {
            binding.emailLinkForm.visibility = if (binding.emailLinkForm.visibility == View.VISIBLE) View.GONE else View.VISIBLE
            if (binding.etLinkEmail.text.isNullOrBlank()) binding.etLinkEmail.setText(linkedGoogleEmail.orEmpty())
        }
        binding.btnEmailLinkSend.setOnClickListener { sendEmailLink() }

        binding.btnPrivacyPolicy.setOnClickListener {
            runCatching { startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(BuildConfig.BASE_URL + "privacy"))) }
                .onFailure { requireContext().toast(getString(R.string.page_unavailable)) }
        }
        binding.btnDeletionPage.setOnClickListener {
            runCatching { startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(BuildConfig.BASE_URL + "account/delete"))) }
                .onFailure { requireContext().toast(getString(R.string.page_unavailable)) }
        }
        binding.btnDeleteAccount.setOnClickListener {
            com.google.android.material.dialog.MaterialAlertDialogBuilder(requireContext())
                .setTitle(R.string.delete_account)
                .setMessage(R.string.delete_account_confirmation)
                .setNegativeButton(android.R.string.cancel, null)
                .setPositiveButton(R.string.delete_account) { _, _ ->
                    binding.btnDeleteAccount.isEnabled = false
                    viewLifecycleOwner.lifecycleScope.launch {
                        when (val result = ParallelLingvoApp.instance.repository.deleteAccount()) {
                            is NetworkResult.Success -> if (result.data.ok == true) {
                                requireActivity().recreate()
                            } else {
                                _binding?.btnDeleteAccount?.isEnabled = true
                                context?.toast(getString(R.string.delete_account_failed))
                            }
                            else -> {
                                _binding?.btnDeleteAccount?.isEnabled = true
                                context?.toast(getString(R.string.delete_account_failed))
                            }
                        }
                    }
                }.show()
        }

        selectedAdapter = SelectedLanguageAdapter(
            onMoveUp = { code -> viewModel.moveUp(code) },
            onMoveDown = { code -> viewModel.moveDown(code) },
            onRemove = { code -> viewModel.removeLanguage(code) }
        )
        binding.rvSelectedLangs.adapter = selectedAdapter

        binding.btnSave.setOnClickListener { viewModel.save() }
        binding.btnSaveDailyGoal.setOnClickListener { saveDailyGoal() }
        loadDailyGoal()
        binding.btnSaveCacheLimit.setOnClickListener { saveCacheLimit() }
        loadCacheLimit()
        // View-state restoration also changes isChecked; only user clicks may update the server.
        binding.swMcpEnabled.setOnClickListener { onMcpToggle(binding.swMcpEnabled.isChecked) }
        binding.btnMcpManage.setOnClickListener { openMcpSettingsInBrowser() }
        binding.btnMcpCopyName.setOnClickListener {
            requireContext().copyToClipboard(getString(R.string.mcp_connector_name_label), mcpConnectorName)
        }
        binding.btnMcpCopyDescription.setOnClickListener {
            requireContext().copyToClipboard(getString(R.string.mcp_connector_description_label), mcpConnectorDescription)
        }
        binding.btnMcpCopyHowto.setOnClickListener {
            requireContext().copyToClipboard(getString(R.string.mcp_how_to_connect_label), getString(R.string.mcp_how_to_connect))
        }
        binding.btnFamily.setOnClickListener { showFamilyDialog() }
        binding.btnFamilyCopy.setOnClickListener {
            if (familyInvitationUrl.isNotBlank()) {
                requireContext().copyToClipboard(getString(R.string.family_link_label), familyInvitationUrl)
            }
        }
        binding.btnFamilyShare.setOnClickListener {
            if (familyInvitationUrl.isNotBlank()) {
                startActivity(Intent.createChooser(Intent(Intent.ACTION_SEND).apply {
                    type = "text/plain"
                    putExtra(Intent.EXTRA_TEXT, familyInvitationUrl)
                }, getString(R.string.family_share_link)))
            }
        }
        if (arguments?.getBoolean("show_family_pairing") == true) {
            arguments?.putBoolean("show_family_pairing", false)
            binding.root.post { showFamilyDialog() }
        }

        binding.btnAddLang.setOnClickListener {
            showAddLanguageDialog()
        }

        binding.spUiLanguage.onItemSelectedListener = object : AdapterView.OnItemSelectedListener {
            override fun onItemSelected(parent: AdapterView<*>?, view: View?, position: Int, id: Long) {
                if (ignoreUiLanguageSelection) return
                val code = uiLanguageCodes.getOrNull(position)
                if (code.orEmpty() == currentUiLanguageOverride.orEmpty()) return
                viewLifecycleOwner.lifecycleScope.launch {
                    ParallelLingvoApp.instance.preferencesManager.saveUiLanguageOverride(code)
                    viewModel.saveUiLanguageOverride(code)
                    applyAppLocale(code)
                }
            }

            override fun onNothingSelected(parent: AdapterView<*>?) = Unit
        }

        binding.btnRelogin.setOnClickListener {
            viewLifecycleOwner.lifecycleScope.launch {
                viewModel.logout()
                navigateToAuth()
            }
        }

        binding.btnLogout.setOnClickListener {
            viewLifecycleOwner.lifecycleScope.launch {
                viewModel.logout()
                requireContext().toast(getString(R.string.logged_out))
                navigateToAuth()
            }
        }

        combine(viewModel.authMethod, viewModel.userId, viewModel.serverUrl) { method, userId, serverUrl ->
            Triple(method, userId, serverUrl)
        }.onEach { (method, userId, serverUrl) ->
            binding.tvAuthMethod.text = getString(R.string.auth_method, method.ifBlank { getString(R.string.auth_method_empty) })
            binding.tvAuthUserId.text = getString(R.string.auth_user_id, userId.ifBlank { getString(R.string.auth_user_empty) })
            binding.tvAuthServerUrl.text = getString(R.string.auth_server_url, serverUrl.ifBlank { BuildConfig.BASE_URL })
        }.launchIn(viewLifecycleOwner.lifecycleScope)

        viewLifecycleOwner.lifecycleScope.launch {
            viewModel.uiState.collectLatest { state ->
                val binding = _binding ?: return@collectLatest
                binding.progressBar.visibility = if (state.isLoading) View.VISIBLE else View.GONE
                binding.btnSave.isEnabled = !state.isLoading

                selectedAdapter.setItems(state.selectedLangs, state.allLanguages)
                binding.tvMaxWarning.visibility =
                    if (state.selectedLangs.size >= 5) View.VISIBLE else View.GONE
                renderUiLanguageSelector(state)

                state.error?.let {
                    requireContext().toast(it)
                    viewModel.clearError()
                }
                if (state.saved) {
                    requireContext().toast(getString(R.string.settings_saved))
                    viewModel.clearSaved()
                }
            }
        }
    }

    private fun loadDailyGoal() {
        viewLifecycleOwner.lifecycleScope.launch {
            when (val result = ParallelLingvoApp.instance.repository.getDailyGoal()) {
                is NetworkResult.Success -> {
                    binding.etDailyGoal.setText(result.data.goalValue.toString())
                    binding.tvDailyGoalLabel.text = getString(
                        if (result.data.goalType == "words") R.string.daily_goal_words
                        else R.string.daily_goal_minutes
                    )
                }
                else -> Unit
            }
        }
    }

    private fun saveDailyGoal() {
        val value = binding.etDailyGoal.text?.toString()?.toIntOrNull()
        if (value == null) {
            requireContext().toast(getString(R.string.daily_goal_invalid))
            return
        }
        viewLifecycleOwner.lifecycleScope.launch {
            when (ParallelLingvoApp.instance.repository.saveDailyGoal(value)) {
                is NetworkResult.Success -> requireContext().toast(getString(R.string.settings_saved))
                is NetworkResult.Error -> requireContext().toast(getString(R.string.daily_goal_invalid))
                else -> Unit
            }
        }
    }

    private fun loadCacheLimit() {
        viewLifecycleOwner.lifecycleScope.launch {
            val limit = ParallelLingvoApp.instance.preferencesManager.cacheLimitMb.first()
            binding.etCacheLimitMb.setText(limit.toString())
        }
    }

    private fun saveCacheLimit() {
        val value = binding.etCacheLimitMb.text?.toString()?.toIntOrNull()
        if (value == null || value !in WordContentCache.MIN_CACHE_MB..WordContentCache.MAX_CACHE_MB) {
            requireContext().toast(getString(R.string.cache_limit_invalid))
            return
        }
        viewLifecycleOwner.lifecycleScope.launch {
            val app = ParallelLingvoApp.instance
            app.preferencesManager.saveCacheLimitMb(value)
            app.wordContentCache.trimToConfiguredLimit()
            requireContext().toast(getString(R.string.cache_limit_saved, value))
        }
    }

    private var mcpConnectorName: String = ""
    private var mcpConnectorDescription: String = ""

    private fun loadMcpStatus() {
        _binding?.tvGoogleIdentity?.setText(R.string.loading)
        _binding?.btnLinkGoogle?.isEnabled = false
        viewLifecycleOwner.lifecycleScope.launch {
            when (val result = ParallelLingvoApp.instance.repository.getMcpUser()) {
                is NetworkResult.Success -> {
                    val data = result.data
                    val b = _binding ?: return@launch
                    val google = data.googleAccount
                    linkedGoogleEmail = google?.takeIf { it.linked }?.email?.takeIf { it.isNotBlank() }
                    b.btnLinkGoogle.visibility = if (data.ok && google != null && !google.linked) View.VISIBLE else View.GONE
                    b.btnLinkGoogle.isEnabled = data.ok && !linkingGoogle
                    b.tvGoogleIdentity.text = when {
                        !data.ok || google == null -> getString(R.string.page_unavailable)
                        !google.linked -> getString(R.string.account_not_linked)
                        else -> google.email?.takeIf { it.isNotBlank() }
                            ?: getString(R.string.account_linked)
                    }
                    binding.swMcpEnabled.isChecked = data.enabled
                    binding.swMcpEnabled.isEnabled = true
                    binding.tvMcpStatus.text = getString(
                        R.string.mcp_connections_count,
                        mcpStateLabel(data.state),
                        data.connections.size
                    )
                    val connector = data.connector
                    val isRussian = resources.configuration.locales[0].language == "ru"
                    mcpConnectorName = connector?.name?.takeIf { it.isNotBlank() } ?: "ParallelLingvo"
                    mcpConnectorDescription = connector
                        ?.let { if (isRussian) it.description else (it.descriptionEn ?: it.description) }
                        ?.takeIf { it.isNotBlank() }
                        ?: getString(R.string.mcp_connector_description)
                    binding.tvMcpName.text = mcpConnectorName
                    binding.tvMcpDescription.text = mcpConnectorDescription
                }
                else -> _binding?.tvGoogleIdentity?.setText(R.string.page_unavailable)
            }
        }
    }

    private fun mcpStateLabel(state: String): String = getString(
        when (state) {
            "connected" -> R.string.mcp_state_connected
            "paused" -> R.string.mcp_state_paused
            "ready" -> R.string.mcp_state_ready
            else -> R.string.mcp_state_disabled
        }
    )

    private fun onMcpToggle(enabled: Boolean) {
        binding.swMcpEnabled.isEnabled = false
        viewLifecycleOwner.lifecycleScope.launch {
            when (ParallelLingvoApp.instance.repository.setMcpEnabled(enabled)) {
                is NetworkResult.Success -> loadMcpStatus()
                else -> {
                    requireContext().toast(getString(R.string.mcp_connector_update_failed))
                    loadMcpStatus()
                }
            }
        }
    }

    private fun openMcpSettingsInBrowser() {
        binding.btnMcpManage.isEnabled = false
        viewLifecycleOwner.lifecycleScope.launch {
            try {
                val result = ParallelLingvoApp.instance.repository.createBrowserLink()
                val url = when (result) {
                    is NetworkResult.Success -> result.data.takeIf { it.ok }?.browserUrl
                    else -> null
                }
                if (url.isNullOrBlank()) {
                    context?.toast(getString(R.string.page_unavailable))
                    return@launch
                }
                startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
            } catch (e: kotlinx.coroutines.CancellationException) {
                throw e
            } catch (e: Exception) {
                context?.toast(getString(R.string.page_unavailable))
            } finally {
                _binding?.btnMcpManage?.isEnabled = true
            }
        }
    }

    private fun navigateToAuth() {
        val navController = findNavController()
        if (navController.currentDestination?.id == R.id.authFragment) return
        val navOptions = NavOptions.Builder()
            .setPopUpTo(R.id.lessonsFragment, true)
            .build()
        navController.navigate(R.id.authFragment, null, navOptions)
    }

    private fun renderUiLanguageSelector(state: LangSettingsUiState) {
        val languages = state.allLanguages.ifEmpty { return }
        currentUiLanguageOverride = state.uiLanguageOverride
        val selectorKey = buildString {
            append(state.detectedUiLanguage)
            append('|')
            append(state.uiLanguageOverride.orEmpty())
            append('|')
            append(languages.joinToString(",") { "${it.code}:${it.name}:${it.flag.orEmpty()}" })
        }
        if (selectorKey == renderedUiLanguageSelectorKey) return
        renderedUiLanguageSelectorKey = selectorKey

        val labels = mutableListOf(getString(R.string.ui_language_auto, state.detectedUiLanguage.ifBlank { "system" }.uppercase()))
        labels.addAll(languages.map { "${it.flag ?: ""} ${it.name} (${it.code.uppercase()})" })
        uiLanguageCodes = listOf<String?>(null) + languages.map { it.code }

        val adapter = ArrayAdapter(requireContext(), android.R.layout.simple_spinner_item, labels).apply {
            setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
        }
        ignoreUiLanguageSelection = true
        binding.spUiLanguage.adapter = adapter
        val selectedCode = state.uiLanguageOverride
        val selectedIndex = if (selectedCode.isNullOrBlank()) 0 else uiLanguageCodes.indexOf(selectedCode).coerceAtLeast(0)
        binding.spUiLanguage.setSelection(selectedIndex, false)
        ignoreUiLanguageSelection = false
    }

    private fun applyAppLocale(languageCode: String?) {
        val locales = if (languageCode.isNullOrBlank()) {
            LocaleListCompat.getEmptyLocaleList()
        } else {
            LocaleListCompat.forLanguageTags(languageCode)
        }
        AppCompatDelegate.setApplicationLocales(locales)
    }

    private fun showAddLanguageDialog() {
        val state = viewModel.uiState.value
        val available = state.allLanguages.filter { it.code !in state.selectedLangs }
        if (available.isEmpty()) {
            requireContext().toast(getString(R.string.no_languages_available))
            return
        }
        val labels = available.map { "${it.flag ?: ""} ${it.name} (${it.code.uppercase()})" }
        val codes = available.map { it.code }

        val adapter = ArrayAdapter(requireContext(), android.R.layout.simple_list_item_1, labels)
        androidx.appcompat.app.AlertDialog.Builder(requireContext())
            .setTitle(R.string.add_language)
            .setAdapter(adapter) { _, idx ->
                viewModel.addLanguage(codes[idx])
            }
            .show()
    }

    private fun showFamilyDialog() {
        viewLifecycleOwner.lifecycleScope.launch {
            val me = ParallelLingvoApp.instance.repository.getMe()
            if (me !is NetworkResult.Success) {
                if (me is NetworkResult.Error) requireContext().toast(me.message)
                return@launch
            }
            (activity as? MainActivity)?.updateParentNavigation(me.data)
            if (!me.data.needsAccountType && me.data.accountType != "child" && !me.data.canManageFamily) {
                findNavController().navigateToTab(R.id.subscriptionFragment)
                return@launch
            }
            if (me.data.canManageFamily) {
                loadFamilyInvitation()
                return@launch
            }
            when (val family = ParallelLingvoApp.instance.repository.getFamily()) {
                is NetworkResult.Success -> {
                    val data = family.data
                    if (data.needsAccountType) {
                        findNavController().navigate(R.id.accountTypeFragment)
                    } else if (data.accountType == "child") {
                        showChildPairingDialog(data.parents)
                    } else if (data.children.isEmpty()) {
                        androidx.appcompat.app.AlertDialog.Builder(requireContext())
                            .setTitle(R.string.family_settings)
                            .setMessage(getString(R.string.family_parent_telegram_note))
                            .setPositiveButton(android.R.string.ok, null)
                            .show()
                    } else {
                        findNavController().navigateToTab(R.id.parentDashboardFragment)
                    }
                }
                is NetworkResult.Error -> requireContext().toast(requireContext().familyErrorMessage(family.message))
                else -> Unit
            }
        }
    }

    private suspend fun showChildPairingDialog(parents: List<FamilyMemberDto>) {
        when (val pairing = ParallelLingvoApp.instance.repository.getPairingCode()) {
            is NetworkResult.Success -> {
                val url = pairing.data.pairingUrl.orEmpty()
                if (url.isBlank()) {
                    requireContext().toast(getString(R.string.family_invalid_link))
                    return
                }
                val density = resources.displayMetrics.density
                val padding = (18 * density).toInt()
                var pairingDialog: androidx.appcompat.app.AlertDialog? = null
                val content = LinearLayout(requireContext()).apply {
                    orientation = LinearLayout.VERTICAL
                    setPadding(padding, padding / 2, padding, 0)
                }
                content.addView(TextView(requireContext()).apply {
                    text = getString(R.string.family_child_qr_note)
                    textSize = 15f
                })
                content.addView(ImageView(requireContext()).apply {
                    setImageBitmap(createQrBitmap(url, 720))
                    adjustViewBounds = true
                    contentDescription = getString(R.string.family_child_qr_title)
                })
                content.addView(TextView(requireContext()).apply {
                    text = getString(R.string.family_parents_count, parents.size, 5)
                    textSize = 14f
                    setPadding(0, padding / 2, 0, 0)
                })
                content.addView(TextView(requireContext()).apply {
                    val parentNames = parents.map { parent ->
                        val name = parent.displayName.orEmpty().ifBlank { parent.firstName.orEmpty() }
                        val username = parent.username?.takeIf { it.isNotBlank() }?.let { "@$it" }.orEmpty()
                        listOf(name, username).filter { it.isNotBlank() }.joinToString(" ")
                    }.filter { it.isNotBlank() }
                    text = if (parentNames.isEmpty()) {
                        getString(R.string.family_no_connections)
                    } else {
                        getString(R.string.family_connected_parents, parentNames.joinToString("\n"))
                    }
                    textSize = 14f
                })
                content.addView(TextView(requireContext()).apply {
                    text = url
                    setTextIsSelectable(true)
                    textSize = 13f
                    setPadding(0, padding / 2, 0, padding / 2)
                })
                content.addView(Button(requireContext()).apply {
                    setText(R.string.family_copy_link)
                    setOnClickListener { requireContext().copyToClipboard(getString(R.string.family_link_label), url) }
                })
                content.addView(Button(requireContext()).apply {
                    setText(R.string.family_share_link)
                    setOnClickListener {
                        startActivity(Intent.createChooser(Intent(Intent.ACTION_SEND).apply {
                            type = "text/plain"
                            putExtra(Intent.EXTRA_TEXT, url)
                        }, getString(R.string.family_share_link)))
                    }
                })
                content.addView(Button(requireContext()).apply {
                    setText(R.string.family_refresh_link)
                    setOnClickListener {
                        pairingDialog?.dismiss()
                        showFamilyDialog()
                    }
                })
                pairingDialog = androidx.appcompat.app.AlertDialog.Builder(requireContext())
                    .setTitle(R.string.family_child_qr_title)
                    .setView(content)
                    .setPositiveButton(android.R.string.ok, null)
                    .create()
                pairingDialog.show()
            }
            is NetworkResult.Error -> requireContext().toast(requireContext().familyErrorMessage(pairing.message))
            else -> Unit
        }
    }

    private fun createQrBitmap(value: String, size: Int): Bitmap {
        val matrix = MultiFormatWriter().encode(value, BarcodeFormat.QR_CODE, size, size)
        val pixels = IntArray(size * size)
        for (y in 0 until size) {
            for (x in 0 until size) {
                pixels[y * size + x] = if (matrix[x, y]) Color.BLACK else Color.WHITE
            }
        }
        return Bitmap.createBitmap(size, size, Bitmap.Config.ARGB_8888).apply {
            setPixels(pixels, 0, size, 0, 0, size, size)
        }
    }

    private fun startFamilyQrScan() {
        familyQrScanner.launch(
            ScanOptions().apply {
                setDesiredBarcodeFormats(ScanOptions.QR_CODE)
                setPrompt(getString(R.string.family_scan_prompt))
                setBeepEnabled(false)
                setOrientationLocked(false)
            }
        )
    }

    private fun linkChildFromQr(value: String) {
        (activity as? MainActivity)?.openFamilyInvitation(value)
            ?: requireContext().toast(getString(R.string.family_invalid_link))
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
