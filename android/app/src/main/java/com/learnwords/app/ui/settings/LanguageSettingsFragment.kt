package com.learnwords.app.ui.settings

import android.os.Bundle
import android.view.*
import android.widget.ArrayAdapter
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import com.learnwords.app.BuildConfig
import com.learnwords.app.R
import com.learnwords.app.databinding.FragmentLanguageSettingsBinding
import com.learnwords.app.utils.toast
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.flow.launchIn
import kotlinx.coroutines.flow.onEach
import kotlinx.coroutines.launch

class LanguageSettingsFragment : Fragment() {

    private var _binding: FragmentLanguageSettingsBinding? = null
    private val binding get() = _binding!!
    private val viewModel: LanguageSettingsViewModel by viewModels()
    private lateinit var selectedAdapter: SelectedLanguageAdapter

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

        binding.btnAddLang.setOnClickListener {
            showAddLanguageDialog()
        }

        binding.btnAdminPanel.setOnClickListener {
            findNavController().navigate(R.id.action_settings_to_admin)
        }

        binding.btnRelogin.setOnClickListener {
            viewModel.logout()
            findNavController().navigate(R.id.authFragment)
        }

        binding.btnLogout.setOnClickListener {
            viewModel.logout()
            requireContext().toast("Вы вышли из аккаунта")
            findNavController().navigate(R.id.authFragment)
        }

        // Показываем кнопку только администраторам
        viewModel.isAdmin.onEach { isAdmin ->
            binding.btnAdminPanel.visibility = if (isAdmin) View.VISIBLE else View.GONE
        }.launchIn(viewLifecycleOwner.lifecycleScope)

        combine(viewModel.authMethod, viewModel.userId, viewModel.serverUrl) { method, userId, serverUrl ->
            Triple(method, userId, serverUrl)
        }.onEach { (method, userId, serverUrl) ->
            binding.tvAuthMethod.text = "Способ входа: ${method.ifBlank { "не указан" }}"
            binding.tvAuthUserId.text = "Telegram ID: ${userId.ifBlank { "не выполнен вход" }}"
            binding.tvAuthServerUrl.text = "Сервер: ${serverUrl.ifBlank { BuildConfig.BASE_URL }}"
        }.launchIn(viewLifecycleOwner.lifecycleScope)

        lifecycleScope.launch {
            viewModel.uiState.collectLatest { state ->
                binding.progressBar.visibility = if (state.isLoading) View.VISIBLE else View.GONE
                binding.btnSave.isEnabled = !state.isLoading

                selectedAdapter.setItems(state.selectedLangs, state.allLanguages)
                binding.tvMaxWarning.visibility =
                    if (state.selectedLangs.size >= 4) View.VISIBLE else View.GONE

                state.error?.let {
                    requireContext().toast(it)
                    viewModel.clearError()
                }
                if (state.saved) {
                    requireContext().toast("Настройки сохранены")
                    viewModel.clearSaved()
                }
            }
        }
    }

    private fun showAddLanguageDialog() {
        val state = viewModel.uiState.value
        val available = state.allLanguages.filter { it.code !in state.selectedLangs }
        if (available.isEmpty()) {
            requireContext().toast("Нет доступных языков для добавления")
            return
        }
        val labels = available.map { "${it.flag ?: ""} ${it.name} (${it.code.uppercase()})" }
        val codes = available.map { it.code }

        val adapter = ArrayAdapter(requireContext(), android.R.layout.simple_list_item_1, labels)
        androidx.appcompat.app.AlertDialog.Builder(requireContext())
            .setTitle("Добавить язык")
            .setAdapter(adapter) { _, idx ->
                viewModel.addLanguage(codes[idx])
            }
            .show()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
