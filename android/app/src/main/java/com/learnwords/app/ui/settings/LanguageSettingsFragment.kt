package com.learnwords.app.ui.settings

import android.graphics.Bitmap
import android.graphics.Color
import android.net.Uri
import android.content.Intent
import android.os.Bundle
import android.view.*
import android.widget.AdapterView
import android.widget.ArrayAdapter
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Button
import androidx.appcompat.app.AppCompatDelegate
import androidx.core.os.LocaleListCompat
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.lifecycleScope
import androidx.navigation.NavOptions
import androidx.navigation.fragment.findNavController
import com.learnwords.app.BuildConfig
import com.learnwords.app.LearnWordsApp
import com.learnwords.app.MainActivity
import com.learnwords.app.R
import com.learnwords.app.databinding.FragmentLanguageSettingsBinding
import com.learnwords.app.utils.NetworkResult
import com.learnwords.app.utils.toast
import com.learnwords.app.utils.copyToClipboard
import com.learnwords.app.utils.familyErrorMessage
import com.learnwords.app.utils.navigateToTab
import com.learnwords.app.data.api.FamilyMemberDto
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
    private val familyQrScanner = registerForActivityResult(ScanContract()) { result ->
        val value = result.contents.orEmpty()
        if (value.isNotBlank()) linkChildFromQr(value)
    }

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentLanguageSettingsBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

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
        binding.swMcpEnabled.setOnCheckedChangeListener { _, isChecked -> onMcpToggle(isChecked) }
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
        loadMcpStatus()
        binding.btnFamily.setOnClickListener { showFamilyDialog() }
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
                    LearnWordsApp.instance.preferencesManager.saveUiLanguageOverride(code)
                    viewModel.saveUiLanguageOverride(code)
                    applyAppLocale(code)
                }
            }

            override fun onNothingSelected(parent: AdapterView<*>?) = Unit
        }

        binding.btnAdminPanel.setOnClickListener {
            findNavController().navigate(R.id.action_settings_to_admin)
        }

        binding.btnRelogin.setOnClickListener {
            viewModel.logout()
            navigateToAuth()
        }

        binding.btnLogout.setOnClickListener {
            viewModel.logout()
            requireContext().toast(getString(R.string.logged_out))
            navigateToAuth()
        }

        // Показываем кнопку только администраторам
        viewModel.isAdmin.onEach { isAdmin ->
            binding.btnAdminPanel.visibility = if (isAdmin) View.VISIBLE else View.GONE
        }.launchIn(viewLifecycleOwner.lifecycleScope)

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
            when (val result = LearnWordsApp.instance.repository.getDailyGoal()) {
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
            when (LearnWordsApp.instance.repository.saveDailyGoal(value)) {
                is NetworkResult.Success -> requireContext().toast(getString(R.string.settings_saved))
                is NetworkResult.Error -> requireContext().toast(getString(R.string.daily_goal_invalid))
                else -> Unit
            }
        }
    }

    private fun loadCacheLimit() {
        viewLifecycleOwner.lifecycleScope.launch {
            val limit = LearnWordsApp.instance.preferencesManager.cacheLimitMb.first()
            binding.etCacheLimitMb.setText(limit.toString())
        }
    }

    private fun saveCacheLimit() {
        val value = binding.etCacheLimitMb.text?.toString()?.toIntOrNull()
        if (value == null || value !in com.learnwords.app.utils.WordContentCache.MIN_CACHE_MB..com.learnwords.app.utils.WordContentCache.MAX_CACHE_MB) {
            requireContext().toast(getString(R.string.cache_limit_invalid))
            return
        }
        viewLifecycleOwner.lifecycleScope.launch {
            val app = LearnWordsApp.instance
            app.preferencesManager.saveCacheLimitMb(value)
            app.wordContentCache.trimToConfiguredLimit()
            requireContext().toast(getString(R.string.cache_limit_saved, value))
        }
    }

    private var ignoreMcpToggle = false
    private var mcpConnectorName: String = ""
    private var mcpConnectorDescription: String = ""

    private fun loadMcpStatus() {
        viewLifecycleOwner.lifecycleScope.launch {
            when (val result = LearnWordsApp.instance.repository.getMcpUser()) {
                is NetworkResult.Success -> {
                    val data = result.data
                    ignoreMcpToggle = true
                    binding.swMcpEnabled.isChecked = data.enabled
                    ignoreMcpToggle = false
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
                else -> Unit
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
        if (ignoreMcpToggle) return
        binding.swMcpEnabled.isEnabled = false
        viewLifecycleOwner.lifecycleScope.launch {
            when (LearnWordsApp.instance.repository.setMcpEnabled(enabled)) {
                is NetworkResult.Success -> loadMcpStatus()
                else -> {
                    requireContext().toast(getString(R.string.mcp_connector_update_failed))
                    loadMcpStatus()
                }
            }
        }
    }

    private fun openMcpSettingsInBrowser() {
        viewLifecycleOwner.lifecycleScope.launch {
            val base = LearnWordsApp.instance.preferencesManager.serverUrl.first().ifBlank { BuildConfig.BASE_URL }
            val url = base.trimEnd('/') + "/settings"
            try {
                startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
            } catch (e: Exception) {
                requireContext().toast(url)
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
            when (val family = LearnWordsApp.instance.repository.getFamily()) {
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
                        (activity as? MainActivity)?.setParentNavigationVisible(true)
                        findNavController().navigateToTab(R.id.parentDashboardFragment)
                    }
                }
                is NetworkResult.Error -> requireContext().toast(requireContext().familyErrorMessage(family.message))
                else -> Unit
            }
        }
    }

    private suspend fun showChildPairingDialog(parents: List<FamilyMemberDto>) {
        when (val pairing = LearnWordsApp.instance.repository.getPairingCode()) {
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
        val token = runCatching { Uri.parse(value).getQueryParameter("token") }
            .getOrNull()
            .orEmpty()
        if (token.isBlank()) {
            requireContext().toast(getString(R.string.family_invalid_link))
            return
        }
        viewLifecycleOwner.lifecycleScope.launch {
            when (val result = LearnWordsApp.instance.repository.linkChild(token)) {
                is NetworkResult.Success -> {
                    val name = result.data.child?.displayName.orEmpty()
                    requireContext().toast(getString(R.string.family_linked_to, name))
                    (activity as? MainActivity)?.setParentNavigationVisible(true)
                    if (findNavController().currentDestination?.id != R.id.parentDashboardFragment) {
                        findNavController().navigateToTab(R.id.parentDashboardFragment)
                    }
                }
                is NetworkResult.Error -> requireContext().toast(requireContext().familyErrorMessage(result.message))
                else -> Unit
            }
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
