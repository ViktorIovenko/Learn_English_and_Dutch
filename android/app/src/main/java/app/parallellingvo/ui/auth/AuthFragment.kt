package app.parallellingvo.ui.auth

import android.app.Activity
import android.content.Context
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.view.inputmethod.InputMethodManager
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.findNavController
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatDelegate
import androidx.core.os.LocaleListCompat
import app.parallellingvo.ParallelLingvoApp
import com.google.android.gms.auth.api.signin.GoogleSignIn
import com.google.android.gms.auth.api.signin.GoogleSignInStatusCodes
import com.google.android.gms.common.api.ApiException
import com.google.android.gms.common.api.CommonStatusCodes
import app.parallellingvo.BuildConfig
import app.parallellingvo.R
import app.parallellingvo.MainActivity
import app.parallellingvo.databinding.FragmentAuthBinding
import app.parallellingvo.utils.toast
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import java.util.Locale

class AuthFragment : Fragment() {

    private var _binding: FragmentAuthBinding? = null
    private val binding get() = _binding!!
    private val viewModel: AuthViewModel by viewModels()
    private var googleServerUrl = BuildConfig.BASE_URL

    private val googleLoginLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.data == null && result.resultCode == Activity.RESULT_CANCELED) {
            viewModel.googleLoginCancelled()
            return@registerForActivityResult
        }
        try {
            val account = GoogleSignIn.getSignedInAccountFromIntent(result.data)
                .getResult(ApiException::class.java)
            val idToken = account?.idToken
            if (idToken.isNullOrBlank()) {
                viewModel.googleLoginFailed()
            } else {
                viewModel.loginWithGoogleToken(idToken, googleServerUrl)
            }
        } catch (error: ApiException) {
            if (error.statusCode == GoogleSignInStatusCodes.SIGN_IN_CANCELLED ||
                error.statusCode == CommonStatusCodes.CANCELED) {
                viewModel.googleLoginCancelled()
            } else {
                viewModel.googleLoginFailed(error.statusCode)
            }
        }
    }

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentAuthBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        googleServerUrl = savedInstanceState?.getString("google_server_url") ?: googleServerUrl
        (activity as? MainActivity)?.setupBrandImages(binding.imgLoginMark, binding.imgLoginName, 36f)
        setupAppearanceControls()


        binding.btnGoogleLogin.setOnClickListener {
            googleServerUrl = effectiveServerUrl()
            viewModel.startGoogleLogin(googleServerUrl)
        }

        binding.btnTelegramLogin.setOnClickListener {
            if (viewModel.uiState.value.isLoading) return@setOnClickListener
            (activity as? MainActivity)?.startBrowserAuth("telegram", "login", effectiveServerUrl())
        }

        binding.btnEmailLogin.setOnClickListener {
            val showForm = binding.emailLoginSection.visibility != View.VISIBLE
            binding.emailLoginSection.visibility = if (showForm) View.VISIBLE else View.GONE
            if (showForm) {
                binding.etEmail.requestFocus()
            } else {
                binding.emailLoginSection.clearFocus()
                val keyboard = requireContext().getSystemService(Context.INPUT_METHOD_SERVICE) as? InputMethodManager
                keyboard?.hideSoftInputFromWindow(binding.root.windowToken, 0)
            }
        }

        binding.btnEmailSubmit.setOnClickListener {
            viewModel.loginWithEmail(binding.etEmail.text.toString().trim(), binding.etEmailPassword.text.toString(),
                effectiveServerUrl(), resources.configuration.locales[0].language)
        }
        binding.etEmailPassword.setOnEditorActionListener { _, action, _ ->
            if (action == android.view.inputmethod.EditorInfo.IME_ACTION_GO) {
                binding.btnEmailSubmit.performClick(); true
            } else false
        }
        binding.btnEmailRegister.setOnClickListener {
            (activity as? MainActivity)?.startBrowserAuth("email", "setup", effectiveServerUrl())
        }
        binding.btnEmailReset.setOnClickListener {
            (activity as? MainActivity)?.startBrowserAuth("email", "reset", effectiveServerUrl())
        }

        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
            viewModel.uiState.collectLatest { state ->
                binding.progressBar.visibility = if (state.isLoading) View.VISIBLE else View.GONE
                binding.btnGoogleLogin.isEnabled = !state.isLoading
                binding.btnTelegramLogin.isClickable = !state.isLoading
                binding.btnEmailSubmit.isEnabled = !state.isLoading
                binding.btnEmailRegister.isEnabled = !state.isLoading
                binding.btnEmailReset.isEnabled = !state.isLoading

                state.error?.let {
                    requireContext().toast(it)
                    viewModel.clearError()
                }

                if (state.isLoggedIn && findNavController().currentDestination?.id == R.id.authFragment) {
                    (activity as? MainActivity)?.syncChildLearningReminder(state.accountType)
                    (activity as? MainActivity)?.refreshParentNavigation()
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

        viewLifecycleOwner.lifecycleScope.launch {
            viewModel.googleSignInIntent.collectLatest { intent ->
                googleLoginLauncher.launch(intent)
            }
        }
    }

    private fun setupAppearanceControls() {
        val prefs = ParallelLingvoApp.instance.preferencesManager
        val codes = listOf("", "en", "nl", "ru", "de", "fr", "es", "it", "pt", "pl", "uk")
        val systemLanguage = android.content.res.Resources.getSystem().configuration.locales[0].language
        val languageLabels = codes.map { code ->
            if (code.isBlank()) getString(R.string.ui_language_auto, systemLanguage.uppercase(Locale.ROOT))
            else Locale.forLanguageTag(code).let { it.getDisplayName(it) }
        }
        val modes = listOf(AppCompatDelegate.MODE_NIGHT_FOLLOW_SYSTEM,
            AppCompatDelegate.MODE_NIGHT_NO, AppCompatDelegate.MODE_NIGHT_YES)
        val themeLabels = listOf(getString(R.string.theme_system),
            getString(R.string.theme_light), getString(R.string.theme_dark))

        viewLifecycleOwner.lifecycleScope.launch {
            prefs.uiLanguageOverride.collectLatest { code ->
                binding.btnLoginLanguage.text = languageLabels[codes.indexOf(code).coerceAtLeast(0)]
            }
        }
        viewLifecycleOwner.lifecycleScope.launch {
            prefs.themeMode.collectLatest { mode ->
                binding.btnLoginTheme.text = getString(R.string.theme_current,
                    themeLabels[modes.indexOf(mode).coerceAtLeast(0)])
            }
        }
        binding.btnLoginLanguage.setOnClickListener {
            viewLifecycleOwner.lifecycleScope.launch {
                val selected = codes.indexOf(prefs.uiLanguageOverride.first()).coerceAtLeast(0)
                AlertDialog.Builder(requireContext())
                    .setTitle(R.string.interface_language)
                    .setSingleChoiceItems(languageLabels.toTypedArray(), selected) { dialog, index ->
                        dialog.dismiss()
                        viewLifecycleOwner.lifecycleScope.launch {
                            prefs.saveUiLanguageOverride(codes[index].ifBlank { null })
                            AppCompatDelegate.setApplicationLocales(if (codes[index].isBlank()) {
                                LocaleListCompat.getEmptyLocaleList()
                            } else LocaleListCompat.forLanguageTags(codes[index]))
                        }
                    }.show()
            }
        }
        binding.btnLoginTheme.setOnClickListener {
            viewLifecycleOwner.lifecycleScope.launch {
                val selected = modes.indexOf(prefs.themeMode.first()).coerceAtLeast(0)
                AlertDialog.Builder(requireContext())
                    .setTitle(R.string.theme_title)
                    .setSingleChoiceItems(themeLabels.toTypedArray(), selected) { dialog, index ->
                        dialog.dismiss()
                        viewLifecycleOwner.lifecycleScope.launch {
                            prefs.saveThemeMode(modes[index])
                            AppCompatDelegate.setDefaultNightMode(modes[index])
                        }
                    }.show()
            }
        }
    }

    override fun onSaveInstanceState(outState: Bundle) {
        super.onSaveInstanceState(outState)
        outState.putString("google_server_url", googleServerUrl)
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }

    private fun effectiveServerUrl(): String =
        BuildConfig.BASE_URL

}
