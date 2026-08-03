package com.learnwords.app.ui.auth

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import com.learnwords.app.LearnWordsApp
import com.learnwords.app.MainActivity
import com.learnwords.app.R
import com.learnwords.app.databinding.FragmentAccountTypeBinding
import com.learnwords.app.utils.NetworkResult
import com.learnwords.app.utils.toast
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
            when (val result = LearnWordsApp.instance.repository.setAccountType(accountType)) {
                is NetworkResult.Success -> {
                    (activity as? MainActivity)?.syncChildLearningReminder(accountType)
                    val me = LearnWordsApp.instance.repository.getMe()
                    if (me is NetworkResult.Success) {
                        (activity as? MainActivity)?.setParentNavigationVisible(me.data.isParent)
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
