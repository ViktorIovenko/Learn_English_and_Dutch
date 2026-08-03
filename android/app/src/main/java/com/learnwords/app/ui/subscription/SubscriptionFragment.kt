package com.learnwords.app.ui.subscription

import android.os.Bundle
import android.view.*
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.lifecycleScope
import com.learnwords.app.R
import com.learnwords.app.billing.BillingState
import com.learnwords.app.databinding.FragmentSubscriptionBinding
import com.learnwords.app.utils.gone
import com.learnwords.app.utils.toast
import com.learnwords.app.utils.visible
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch

class SubscriptionFragment : Fragment() {

    private var _binding: FragmentSubscriptionBinding? = null
    private val binding get() = _binding!!
    private val viewModel: SubscriptionViewModel by viewModels()

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentSubscriptionBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        binding.swipeRefresh.setOnRefreshListener { viewModel.loadAll() }

        lifecycleScope.launch {
            viewModel.uiState.collectLatest { state ->
                renderState(state)
            }
        }
    }

    private fun renderState(state: SubscriptionUiState) {
        binding.swipeRefresh.isRefreshing = state.isLoading || state.isVerifying

        // ── Статус сервера ────────────────────────────────────────────────
        binding.tvStatus.text = state.serverStatusText.ifBlank { getString(R.string.loading) }
        binding.tvExpiry.text = state.serverExpiryText
        binding.tvExpiry.visibility = if (state.serverExpiryText.isNotEmpty()) View.VISIBLE else View.GONE

        val trialDays = state.daysRemaining
        if (trialDays != null && state.serverSub?.status == "trial") {
            binding.progressTrial.max = 14
            binding.progressTrial.progress = (14 - trialDays).coerceIn(0, 14)
            binding.progressTrial.visible()
            binding.tvTrialDays.text = getString(R.string.trial_days_left, trialDays)
            binding.tvTrialDays.visible()
        } else {
            binding.progressTrial.gone()
            binding.tvTrialDays.gone()
        }

        binding.cardStatus.setCardBackgroundColor(
            ContextCompat.getColor(
                requireContext(),
                if (state.isServerActive || state.isGooglePlayActive)
                    R.color.colorBannerActive
                else
                    R.color.colorBannerInactive
            )
        )

        // ── Верификация ────────────────────────────────────────────────────
        if (state.isVerifying) {
            binding.tvVerifying.visible()
            binding.tvVerifying.text = getString(R.string.activating_subscription)
        } else {
            binding.tvVerifying.gone()
        }

        // ── Google Play статус ─────────────────────────────────────────────
        when (val billing = state.billingState) {
            is BillingState.Loading -> {
                binding.tvBillingStatus.text = getString(R.string.google_play_connecting)
                binding.cardPlans.gone()
            }
            is BillingState.Active -> {
                binding.tvBillingStatus.text = getString(R.string.google_play_subscription_active)
                binding.tvBillingStatus.setTextColor(ContextCompat.getColor(requireContext(), R.color.colorCorrect))
                binding.cardPlans.gone()
                binding.cardActivePlay.visible()
                binding.tvActiveProductId.text = getString(R.string.product_id, billing.productId)
            }
            is BillingState.NotSubscribed -> {
                binding.tvBillingStatus.text = getString(R.string.no_google_play_subscription)
                binding.tvBillingStatus.setTextColor(ContextCompat.getColor(requireContext(), R.color.colorTextSecondary))
                binding.cardActivePlay.gone()

                if (state.availablePlans.isNotEmpty()) {
                    binding.cardPlans.visible()
                    renderPlans(state)
                } else {
                    binding.cardPlans.gone()
                    binding.tvNoPlans.visible()
                }
            }
            is BillingState.Error -> {
                binding.tvBillingStatus.text = "Google Play: ${billing.message}"
                binding.tvBillingStatus.setTextColor(ContextCompat.getColor(requireContext(), R.color.colorError))
                binding.cardPlans.gone()
            }
        }

        // ── Сообщения ────────────────────────────────────────────────────
        state.error?.let {
            requireContext().toast(it, long = true)
            viewModel.clearMessages()
        }
        if (state.purchaseSuccess) {
            requireContext().toast(getString(R.string.subscription_success), long = true)
            viewModel.clearMessages()
        }
    }

    private fun renderPlans(state: SubscriptionUiState) {
        binding.plansContainer.removeAllViews()

        state.availablePlans.forEach { plan ->
            val card = layoutInflater.inflate(
                com.learnwords.app.R.layout.item_subscription_plan,
                binding.plansContainer,
                false
            )

            card.findViewById<android.widget.TextView>(com.learnwords.app.R.id.tv_plan_title).text = plan.title
            card.findViewById<android.widget.TextView>(com.learnwords.app.R.id.tv_plan_price).text = plan.priceString

            val tvTrial = card.findViewById<android.widget.TextView>(com.learnwords.app.R.id.tv_plan_trial)
            if (plan.trialString != null) {
                tvTrial.text = plan.trialString
                tvTrial.visible()
            } else {
                tvTrial.gone()
            }

            val badge = card.findViewById<android.widget.TextView>(com.learnwords.app.R.id.tv_popular_badge)
            badge.visibility = if (plan.isPopular) View.VISIBLE else View.GONE

            card.findViewById<com.google.android.material.button.MaterialButton>(
                com.learnwords.app.R.id.btn_subscribe
            ).setOnClickListener {
                viewModel.subscribe(requireActivity(), plan)
            }

            binding.plansContainer.addView(card)
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
