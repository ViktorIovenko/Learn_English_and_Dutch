package com.learnwords.app.ui.upload

import android.os.Bundle
import android.view.*
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.lifecycleScope
import com.google.android.material.tabs.TabLayoutMediator
import com.learnwords.app.databinding.FragmentUploadBinding
import com.learnwords.app.utils.copyToClipboard
import com.learnwords.app.utils.toast
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch

class UploadFragment : Fragment() {

    private var _binding: FragmentUploadBinding? = null
    private val binding get() = _binding!!
    private val viewModel: UploadViewModel by viewModels()

    private val tabTitles = listOf("Добавить", "По теме", "База слов", "Поделиться")

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentUploadBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        val pagerAdapter = UploadPagerAdapter(this)
        binding.viewPager.adapter = pagerAdapter

        TabLayoutMediator(binding.tabLayout, binding.viewPager) { tab, position ->
            tab.text = tabTitles[position]
        }.attach()

        lifecycleScope.launch {
            viewModel.uiState.collectLatest { state ->
                state.error?.let {
                    requireContext().toast(it)
                    viewModel.clearMessages()
                }
                state.success?.let {
                    requireContext().toast(it, long = true)
                    viewModel.clearMessages()
                }
                state.shareUrl?.let { url ->
                    requireContext().copyToClipboard("Share URL", url)
                    requireContext().toast("Ссылка скопирована: $url", long = true)
                }
            }
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
