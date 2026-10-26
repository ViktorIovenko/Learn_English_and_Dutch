package app.parallellingvo.ui.upload

import android.os.Bundle
import android.view.*
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import app.parallellingvo.ParallelLingvoApp
import app.parallellingvo.utils.NetworkResult
import app.parallellingvo.utils.navigateToTab
import com.google.android.material.tabs.TabLayoutMediator
import app.parallellingvo.R
import app.parallellingvo.databinding.FragmentUploadBinding
import app.parallellingvo.utils.copyToClipboard
import app.parallellingvo.utils.toast
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch

class UploadFragment : Fragment() {

    private var _binding: FragmentUploadBinding? = null
    private val binding get() = _binding!!
    private val viewModel: UploadViewModel by viewModels()

    private val tabTitleRes = listOf(
        R.string.word_database_tab,
        R.string.add_tab,
        R.string.topic_tab,
        R.string.share_tab
    )

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentUploadBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        app.parallellingvo.ui.ads.AdBannerController(
            container = binding.adContainer,
            owner = viewLifecycleOwner,
            session = androidx.lifecycle.ViewModelProvider(this)[app.parallellingvo.ui.ads.AdsSessionViewModel::class.java],
            page = "secondary", placements = listOf("secondary_bottom"),
        )
        binding.tvPlanNotice.setOnClickListener {
            findNavController().navigateToTab(R.id.subscriptionFragment)
        }

        val pagerAdapter = UploadPagerAdapter(this)
        binding.viewPager.adapter = pagerAdapter

        TabLayoutMediator(binding.tabLayout, binding.viewPager) { tab, position ->
            tab.text = getString(tabTitleRes[position])
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
                    requireContext().toast(getString(R.string.link_copied, url), long = true)
                }
            }
        }
    }

    override fun onResume() {
        super.onResume()
        viewLifecycleOwner.lifecycleScope.launch {
            val me = ParallelLingvoApp.instance.repository.getMe()
            val plan = (me as? NetworkResult.Success)?.data?.planState ?: return@launch
            val notice = when {
                !plan.paidAiGloballyEnabled -> R.string.plan_ai_paused
                !plan.features.aiPaid -> R.string.plan_ai_upgrade
                else -> null
            }
            binding.tvPlanNotice.visibility = if (notice == null) View.GONE else View.VISIBLE
            if (notice != null) binding.tvPlanNotice.setText(notice)
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
