package com.learnwords.app.ui.admin

import android.os.Bundle
import android.view.*
import androidx.appcompat.app.AlertDialog
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.lifecycleScope
import com.learnwords.app.R
import com.learnwords.app.databinding.FragmentAdminBinding
import com.learnwords.app.data.api.AdminUserDto
import com.learnwords.app.data.api.AdminFamilyRelationDto
import com.learnwords.app.utils.toast
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch

class AdminFragment : Fragment() {

    private var _binding: FragmentAdminBinding? = null
    private val binding get() = _binding!!
    private val viewModel: AdminViewModel by viewModels()
    private lateinit var adapter: AdminUserAdapter

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentAdminBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        adapter = AdminUserAdapter(
            onGrant = { user -> confirmGrant(user) },
            onRevoke = { user -> confirmRevoke(user) },
            onUnlinkFamily = { relation -> confirmUnlinkFamily(relation) },
            onResetTts = { user -> confirmResetTts(user) },
            onResetTranslation = { user -> confirmResetTranslation(user) }
        )
        binding.rvUsers.adapter = adapter

        binding.btnGrantById.setOnClickListener {
            val uid = binding.etUserId.text.toString().trim()
            viewModel.grantAccess(uid)
            binding.etUserId.setText("")
        }

        binding.btnRefresh.setOnClickListener {
            viewModel.loadUsers()
        }
        binding.btnResetTtsAll.setOnClickListener {
            confirmResetTts(null)
        }
        binding.btnResetTranslationAll.setOnClickListener {
            confirmResetTranslation(null)
        }

        lifecycleScope.launch {
            viewModel.uiState.collectLatest { state ->
                binding.progressBar.visibility = if (state.isLoading) View.VISIBLE else View.GONE
                adapter.submitList(state.users)
                binding.tvUserCount.text = getString(R.string.users_count, state.users.size)
                val usage = state.ttsUsage
                binding.tvTtsSummary.text = if (usage == null) {
                    getString(R.string.tts_usage_summary, 0, 0, 0)
                } else {
                    getString(
                        R.string.tts_usage_summary,
                        usage.totalRequests,
                        usage.successfulRequests,
                        usage.failedRequests
                    )
                }
                val translationUsage = state.translationUsage
                binding.tvTranslationSummary.text = if (translationUsage == null) {
                    getString(R.string.translation_usage_summary, 0, 0, 0, 0, 0)
                } else {
                    getString(
                        R.string.translation_usage_summary,
                        translationUsage.totalTokens,
                        translationUsage.promptTokens,
                        translationUsage.completionTokens,
                        translationUsage.successfulRequests,
                        translationUsage.failedRequests
                    )
                }

                state.error?.let {
                    context?.toast(it)
                    viewModel.clearMessages()
                }
                state.success?.let {
                    context?.toast(it)
                    viewModel.clearMessages()
                }
            }
        }
    }

    private fun confirmGrant(user: AdminUserDto) {
        val name = user.firstName.ifBlank { user.username.ifBlank { user.userId } }
        AlertDialog.Builder(requireContext())
            .setTitle(R.string.grant_unlimited_title)
            .setMessage(getString(R.string.grant_unlimited_message, name, user.userId))
            .setPositiveButton(R.string.grant) { _, _ -> viewModel.grantAccess(user.userId) }
            .setNegativeButton(R.string.cancel, null)
            .show()
    }

    private fun confirmRevoke(user: AdminUserDto) {
        val name = user.firstName.ifBlank { user.username.ifBlank { user.userId } }
        AlertDialog.Builder(requireContext())
            .setTitle(R.string.revoke_access_title)
            .setMessage(getString(R.string.revoke_access_message, name, user.userId))
            .setPositiveButton(R.string.revoke_access) { _, _ -> viewModel.revokeAccess(user.userId) }
            .setNegativeButton(R.string.cancel, null)
            .show()
    }

    private fun confirmUnlinkFamily(relation: AdminFamilyRelationDto) {
        AlertDialog.Builder(requireContext())
            .setTitle(R.string.admin_unlink_family)
            .setMessage(getString(R.string.admin_unlink_family_confirm, relation.displayName))
            .setPositiveButton(R.string.parent_disconnect) { _, _ ->
                viewModel.unlinkFamily(relation.parentUserId, relation.childUserId)
            }
            .setNegativeButton(R.string.cancel, null)
            .show()
    }

    private fun confirmResetTts(user: AdminUserDto?) {
        val message = if (user == null) {
            getString(R.string.tts_usage_reset_all_confirm)
        } else {
            val name = user.firstName.ifBlank { user.username.ifBlank { user.userId } }
            getString(R.string.tts_usage_reset_user_confirm, name, user.userId)
        }
        AlertDialog.Builder(requireContext())
            .setTitle(R.string.tts_usage_reset_title)
            .setMessage(message)
            .setPositiveButton(R.string.tts_usage_reset) { _, _ ->
                viewModel.resetTtsUsage(user?.userId)
            }
            .setNegativeButton(R.string.cancel, null)
            .show()
    }

    private fun confirmResetTranslation(user: AdminUserDto?) {
        val message = if (user == null) {
            getString(R.string.translation_usage_reset_all_confirm)
        } else {
            val name = user.firstName.ifBlank { user.username.ifBlank { user.userId } }
            getString(R.string.translation_usage_reset_user_confirm, name, user.userId)
        }
        AlertDialog.Builder(requireContext())
            .setTitle(R.string.translation_usage_reset_title)
            .setMessage(message)
            .setPositiveButton(R.string.translation_usage_reset) { _, _ ->
                viewModel.resetTranslationUsage(user?.userId)
            }
            .setNegativeButton(R.string.cancel, null)
            .show()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
