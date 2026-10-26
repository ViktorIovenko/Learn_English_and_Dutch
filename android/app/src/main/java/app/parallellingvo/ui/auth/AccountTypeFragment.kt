package app.parallellingvo.ui.auth

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import app.parallellingvo.ParallelLingvoApp
import app.parallellingvo.MainActivity
import app.parallellingvo.R
import app.parallellingvo.databinding.FragmentAccountTypeBinding
import app.parallellingvo.utils.NetworkResult
import app.parallellingvo.utils.toast
import kotlinx.coroutines.launch

class AccountTypeFragment : Fragment() {

    private var _binding: FragmentAccountTypeBinding? = null
    private val binding get() = _binding!!

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentAccountTypeBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        binding.btnChildAccount.setOnClickListener { saveAccountType("child") }
        binding.btnStandardAccount.setOnClickListener { saveAccountType("standard") }
    }

    private fun saveAccountType(accountType: String) {
        setLoading(true)
        viewLifecycleOwner.lifecycleScope.launch {
            when (val result = ParallelLingvoApp.instance.repository.setAccountType(accountType)) {
                is NetworkResult.Success -> {
                    (activity as? MainActivity)?.syncChildLearningReminder(accountType)
                    val me = ParallelLingvoApp.instance.repository.getMe()
                    if (me is NetworkResult.Success) {
                        (activity as? MainActivity)?.updateParentNavigation(me.data)
                    }
                    findNavController().navigate(
                        R.id.action_accountTypeFragment_to_languageSettingsFragment,
                        Bundle().apply { putBoolean("show_family_pairing", accountType == "child") }
                    )
                }
                is NetworkResult.Error -> {
                    setLoading(false)
                    requireContext().toast(result.message)
                }
                else -> setLoading(false)
            }
        }
    }

    private fun setLoading(loading: Boolean) {
        binding.progressBar.visibility = if (loading) View.VISIBLE else View.GONE
        binding.btnChildAccount.isEnabled = !loading
        binding.btnStandardAccount.isEnabled = !loading
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
