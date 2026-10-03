package com.learnwords.app.ui.auth

import android.app.Activity
import android.content.ActivityNotFoundException
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import androidx.activity.result.contract.ActivityResultContracts
import com.google.android.gms.auth.api.signin.GoogleSignIn
import com.learnwords.app.BuildConfig
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

        val googleLoginLauncher = registerForActivityResult(
            ActivityResultContracts.StartActivityForResult()
        ) { result ->
            if (result.resultCode != Activity.RESULT_OK) {
                viewModel.googleLoginCancelled()
                return@registerForActivityResult
            }
            val account = runCatching {
                GoogleSignIn.getSignedInAccountFromIntent(result.data).result
            }.getOrNull()
            val idToken = account?.idToken
            if (idToken.isNullOrBlank()) {
                viewModel.googleLoginCancelled()
            } else {
                viewModel.loginWithGoogleToken(
                    idToken,
                    effectiveServerUrl()
                )
            }
        }

        // Restore saved values
        lifecycleScope.launch {
            binding.etServerUrl.setText(viewModel.serverUrl.first())
            binding.etUserId.setText(viewModel.userId.first())
        }

        binding.btnLogin.setOnClickListener {
            val userId = binding.etUserId.text.toString().trim()
            val password = binding.etPassword.text.toString().trim()
            viewModel.login(userId, password, effectiveServerUrl())
        }

        binding.btnGoogleLogin.setOnClickListener {
            viewModel.startGoogleLogin(effectiveServerUrl())
        }

        binding.btnTelegramLogin.setOnClickListener {
            openTelegramLogin(effectiveServerUrl())
        }

        binding.btnEmailLogin.setOnClickListener {
            requireContext().toast(getString(R.string.email_login_coming_soon))
        }

        binding.btnToggleManualLogin.setOnClickListener {
            binding.manualLoginSection.visibility =
                if (binding.manualLoginSection.visibility == View.VISIBLE) View.GONE else View.VISIBLE
        }

        binding.btnOffline.setOnClickListener {
            val userId = binding.etUserId.text.toString().trim()
            viewModel.loginOffline(userId, effectiveServerUrl())
        }

        lifecycleScope.launch {
            viewModel.uiState.collectLatest { state ->
                binding.progressBar.visibility = if (state.isLoading) View.VISIBLE else View.GONE
                binding.btnLogin.isEnabled = !state.isLoading
                binding.btnGoogleLogin.isEnabled = !state.isLoading
                binding.btnOffline.isEnabled = !state.isLoading

                state.error?.let {
                    requireContext().toast(it)
                    viewModel.clearError()
                }

                if (state.isLoggedIn) {
                    (activity as? MainActivity)?.syncChildLearningReminder(state.accountType)
                    val action = if (state.needsAccountType) {
                        R.id.action_authFragment_to_accountTypeFragment
                    } else if (!state.hasSubscriptionAccess) {
                        R.id.action_authFragment_to_subscriptionFragment
                    } else {
                        R.id.action_authFragment_to_lessonsFragment
                    }
                    findNavController().navigate(action)
                }
            }
        }

        lifecycleScope.launch {
            viewModel.googleSignInIntent.collectLatest { intent ->
                googleLoginLauncher.launch(intent)
            }
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }

    private fun effectiveServerUrl(): String =
        binding.etServerUrl.text.toString().trim().ifBlank { BuildConfig.BASE_URL }

    private fun openTelegramLogin(serverUrl: String) {
        val base = serverUrl.trimEnd('/')
        val url = "$base/auth/telegram?android=1"
        try {
            startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
        } catch (e: ActivityNotFoundException) {
            requireContext().toast(getString(R.string.telegram_login_failed))
        }
    }
}
