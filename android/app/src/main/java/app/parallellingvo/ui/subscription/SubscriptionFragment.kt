package app.parallellingvo.ui.subscription

import android.os.Bundle
import android.view.*
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import app.parallellingvo.utils.navigateToTab
import app.parallellingvo.R
import app.parallellingvo.MainActivity
import app.parallellingvo.billing.BillingState
import app.parallellingvo.databinding.FragmentSubscriptionBinding
import app.parallellingvo.utils.gone
import app.parallellingvo.utils.toast
import app.parallellingvo.utils.visible
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch

class SubscriptionFragment : Fragment() {

    private var _binding: FragmentSubscriptionBinding? = null
    private val binding get() = _binding!!
    private val viewModel: SubscriptionViewModel by viewModels()
    private var lastNavigationPlan: String? = null

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentSubscriptionBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        binding.btnManageGooglePlay.setOnClickListener {
            val uri = android.net.Uri.parse("https://play.google.com/store/account/subscriptions").buildUpon()
                .appendQueryParameter("package", requireContext().packageName).build()
            runCatching { startActivity(android.content.Intent(android.content.Intent.ACTION_VIEW, uri)) }
                .onFailure { requireContext().toast(getString(R.string.google_play_disconnected)) }
        }
        binding.swipeRefresh.setOnRefreshListener { viewModel.loadAll() }
        binding.btnPlanSettings.setOnClickListener {
            findNavController().navigateToTab(R.id.languageSettingsFragment)
        }

        viewLifecycleOwner.lifecycleScope.launch {
            viewModel.uiState.collectLatest { state ->
                renderState(state)
            }
        }
    }

    private fun renderState(state: SubscriptionUiState) {
        val plan = state.planState?.plan ?: state.serverSub?.plan
        if (plan != null && plan != lastNavigationPlan) {
            lastNavigationPlan = plan
            viewLifecycleOwner.lifecycleScope.launch {
                (activity as? MainActivity)?.refreshParentNavigation()
            }
        }
        binding.swipeRefresh.isRefreshing = state.isLoading || state.isVerifying

        // ── Статус сервера ────────────────────────────────────────────────
        binding.tvStatus.text = state.serverStatusText.ifBlank { getString(R.string.loading) }
        binding.tvExpiry.text = state.serverExpiryText
        binding.tvExpiry.visibility = if (state.serverExpiryText.isNotEmpty()) View.VISIBLE else View.GONE
        renderCatalog(state)
        binding.cardActivePlay.gone()
        binding.tvNoPlans.gone()

        val trialDays = state.daysRemaining
        if (trialDays != null && state.serverSub?.status == "trial" &&
            (state.planState?.plan ?: state.serverSub.plan) != "family") {
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
                if (state.isServerActive)
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
            BillingState.Initiated, BillingState.Pending, BillingState.Received,
            BillingState.Verifying, BillingState.Confirmed -> {
                binding.tvBillingStatus.setTextColor(ContextCompat.getColor(requireContext(), R.color.colorTextSecondary))
                binding.tvBillingStatus.setText(when (state.billingState) {
                    BillingState.Initiated -> R.string.purchase_initiated
                    BillingState.Pending -> R.string.purchase_pending
                    BillingState.Received -> R.string.purchase_received
                    BillingState.Confirmed -> R.string.purchase_confirmed
                    else -> R.string.activating_subscription
                })
                binding.cardPlans.gone()
                binding.cardActivePlay.gone()
            }
            is BillingState.Error -> {
                binding.cardActivePlay.gone()
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

    private fun renderCatalog(state: SubscriptionUiState) {
        val plan = state.planState?.plan ?: state.serverSub?.plan
        val features = state.planState?.features
        binding.tvPlanFeatures.text = if (features == null) "" else buildList {
            if (features.learning) add(getString(R.string.plan_f_learning))
            if (features.manualWords) add(getString(R.string.plan_f_manual))
            add(getString(if (features.ads) R.string.plan_f_ads else R.string.plan_f_no_ads))
            if (features.mcp) add("MCP · ChatGPT")
            if (features.aiPaid) add(getString(R.string.plan_f_ai))
            if (features.family) add(getString(R.string.plan_f_family))
            if (state.planState?.paidAiGloballyEnabled != true) add(getString(R.string.plan_ai_paused))
        }.joinToString("\n")
        binding.catalogContainer.removeAllViews()
        val catalog = listOf(
            Triple("free", R.string.plan_price_free, listOf(R.string.plan_f_learning, R.string.plan_f_manual, R.string.plan_f_ads)),
            Triple("premium", R.string.plan_price_premium, listOf(R.string.plan_f_learning, R.string.plan_f_manual, R.string.plan_f_no_ads, R.string.plan_f_ai, R.string.plan_f_limits)),
            Triple("family", R.string.plan_price_family, listOf(R.string.plan_f_learning, R.string.plan_f_manual, R.string.plan_f_no_ads, R.string.plan_f_ai, R.string.plan_f_limits, R.string.plan_f_family))
        )
        catalog.forEach { (code, price, descriptions) ->
            val card = layoutInflater.inflate(R.layout.item_subscription_plan, binding.catalogContainer, false)
            card.findViewById<android.widget.TextView>(R.id.tv_plan_title).text = when (code) {
                "free" -> "Free"
                "premium" -> "Premium"
                else -> "Family"
            }
            card.findViewById<android.widget.TextView>(R.id.tv_plan_price).setText(price)
            card.findViewById<android.widget.TextView>(R.id.tv_plan_trial).apply {
                text = descriptions.joinToString("\n") { getString(it) } + "\nMCP · ChatGPT"
                visible()
            }
            card.findViewById<android.widget.TextView>(R.id.tv_popular_badge).apply {
                setText(R.string.plan_current)
                visibility = if (code == plan) View.VISIBLE else View.GONE
            }
            card.findViewById<View>(R.id.btn_subscribe).gone()
            binding.catalogContainer.addView(card)
        }
    }

    private fun renderPlans(state: SubscriptionUiState) {
        binding.plansContainer.removeAllViews()

        state.availablePlans.forEach { plan ->
            val card = layoutInflater.inflate(
                R.layout.item_subscription_plan,
                binding.plansContainer,
                false
            )

            card.findViewById<android.widget.TextView>(R.id.tv_plan_title).text = plan.title
            card.findViewById<android.widget.TextView>(R.id.tv_plan_price).text = plan.priceString

            val tvTrial = card.findViewById<android.widget.TextView>(R.id.tv_plan_trial)
            if (plan.trialString != null) {
                tvTrial.text = plan.trialString
                tvTrial.visible()
            } else {
                tvTrial.gone()
            }

            val badge = card.findViewById<android.widget.TextView>(R.id.tv_popular_badge)
            badge.visibility = if (plan.isPopular) View.VISIBLE else View.GONE

            card.findViewById<com.google.android.material.button.MaterialButton>(
                R.id.btn_subscribe
            ).setOnClickListener {
                viewModel.subscribe(requireActivity(), plan)
            }

            binding.plansContainer.addView(card)
        }
    }

    override fun onResume() {
        super.onResume()
        viewModel.loadAll()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
