package com.learnwords.app.ui.admin

import android.os.Bundle
import android.view.*
import androidx.appcompat.app.AlertDialog
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.lifecycleScope
import com.learnwords.app.databinding.FragmentAdminBinding
import com.learnwords.app.data.api.AdminUserDto
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
            onRevoke = { user -> confirmRevoke(user) }
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

        lifecycleScope.launch {
            viewModel.uiState.collectLatest { state ->
                binding.progressBar.visibility = if (state.isLoading) View.VISIBLE else View.GONE
                adapter.submitList(state.users)
                binding.tvUserCount.text = "Пользователей: ${state.users.size}"

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
            .setTitle("Выдать безлимитный доступ")
            .setMessage("Дать безлимитный доступ пользователю $name (${user.userId})?")
            .setPositiveButton("Выдать") { _, _ -> viewModel.grantAccess(user.userId) }
            .setNegativeButton("Отмена", null)
            .show()
    }

    private fun confirmRevoke(user: AdminUserDto) {
        val name = user.firstName.ifBlank { user.username.ifBlank { user.userId } }
        AlertDialog.Builder(requireContext())
            .setTitle("Отозвать доступ")
            .setMessage("Отозвать доступ у пользователя $name (${user.userId})?")
            .setPositiveButton("Отозвать") { _, _ -> viewModel.revokeAccess(user.userId) }
            .setNegativeButton("Отмена", null)
            .show()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
