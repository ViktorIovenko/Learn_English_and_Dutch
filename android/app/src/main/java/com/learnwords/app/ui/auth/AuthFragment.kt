package com.learnwords.app.ui.auth

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import com.learnwords.app.R
import com.learnwords.app.MainActivity
import com.learnwords.app.databinding.FragmentAuthBinding
import com.learnwords.app.utils.gone
import com.learnwords.app.utils.toast
import com.learnwords.app.utils.visible
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch

class AuthFragment : Fragment() {

    private var _binding: FragmentAuthBinding? = null
    private val binding get() = _binding!!
    private val viewModel: AuthViewModel by viewModels()

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentAuthBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        // Restore saved values
        lifecycleScope.launch {
            binding.etServerUrl.setText(viewModel.serverUrl.first())
            binding.etUserId.setText(viewModel.userId.first())
        }

        binding.btnLogin.setOnClickListener {
            val userId = binding.etUserId.text.toString().trim()
            val password = binding.etPassword.text.toString().trim()
            val serverUrl = binding.etServerUrl.text.toString().trim()
            viewModel.login(userId, password, serverUrl)
        }

        binding.btnOffline.setOnClickListener {
            val userId = binding.etUserId.text.toString().trim()
            val serverUrl = binding.etServerUrl.text.toString().trim()
            viewModel.loginOffline(userId, serverUrl)
        }

        lifecycleScope.launch {
            viewModel.uiState.collectLatest { state ->
                binding.progressBar.visibility = if (state.isLoading) View.VISIBLE else View.GONE
                binding.btnLogin.isEnabled = !state.isLoading
                binding.btnOffline.isEnabled = !state.isLoading

                state.error?.let {
                    requireContext().toast(it)
                    viewModel.clearError()
                }

                if (state.isLoggedIn) {
                    (activity as? MainActivity)?.syncChildLearningReminder(state.accountType)
                    val action = if (state.needsAccountType) {
                        R.id.action_authFragment_to_accountTypeFragment
                    } else {
                        R.id.action_authFragment_to_lessonsFragment
                    }
                    findNavController().navigate(action)
                }
            }
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
