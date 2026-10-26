package app.parallellingvo.ui.subscription

import app.parallellingvo.billing.PurchaseSyncWorker
import app.parallellingvo.utils.safeApiCall

import android.app.Activity
import android.app.Application
import android.util.Log
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.android.billingclient.api.ProductDetails
import com.android.billingclient.api.Purchase
import app.parallellingvo.ParallelLingvoApp
import app.parallellingvo.R
import app.parallellingvo.billing.BillingConfig
import app.parallellingvo.billing.BillingManager
import app.parallellingvo.billing.BillingState
import app.parallellingvo.billing.PurchaseResult
import app.parallellingvo.data.api.SubscriptionDto
import app.parallellingvo.data.api.PlanStateDto
import app.parallellingvo.utils.NetworkResult
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.*

data class PlanUiModel(
    val productId: String,
    val title: String,
    val priceString: String,
    val trialString: String?,
    val isPopular: Boolean,
    val productDetails: ProductDetails
)

data class SubscriptionUiState(
    val isLoading: Boolean = false,
    // Данные с сервера
    val serverSub: SubscriptionDto? = null,
    val planState: PlanStateDto? = null,
    val serverStatusText: String = "",
    val serverExpiryText: String = "",
    val isServerActive: Boolean = false,
    val daysRemaining: Int? = null,
    // Данные Google Play
    val billingState: BillingState = BillingState.Loading,
    val availablePlans: List<PlanUiModel> = emptyList(),
    val isGooglePlayActive: Boolean = false,
    val googlePlayProductId: String? = null,
    // Общее
    val error: String? = null,
    val purchaseSuccess: Boolean = false,
    val isVerifying: Boolean = false
)

class SubscriptionViewModel(app: Application) : AndroidViewModel(app) {
    private val appContext = getApplication<ParallelLingvoApp>()
    private val repo = appContext.repository
    private val billingManager = BillingManager(app.applicationContext)
    private val _uiState = MutableStateFlow(SubscriptionUiState())
    val uiState: StateFlow<SubscriptionUiState> = _uiState
    private var accountId = ""
    private var loadJob: kotlinx.coroutines.Job? = null
    private val verificationMutex = kotlinx.coroutines.sync.Mutex()
    private val purchaseListener: (Purchase) -> Unit = { purchase ->
        viewModelScope.launch { verifyAndActivate(purchase, true) }
    }

    init {
        billingManager.addPurchaseListener(purchaseListener)
        viewModelScope.launch {
            billingManager.billingState.collectLatest { state ->
                _uiState.value = _uiState.value.copy(billingState = state,
                    isGooglePlayActive = state is BillingState.Active,
                    googlePlayProductId = (state as? BillingState.Active)?.productId)
            }
        }
        loadAll()
    }

    fun loadAll() {
        if (loadJob?.isActive == true) return
        loadJob = viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, availablePlans = emptyList(), error = null)
            try {
                safeApiCall { appContext.apiClient.service.syncPlaySubscriptions() }
                loadServerSubscription()
                if (!billingManager.connect()) return@launch
                val response = safeApiCall { appContext.apiClient.service.getPlayConfig() }
                if (response !is NetworkResult.Success || !response.data.ok) {
                    billingManager.fail(appContext.getString(R.string.play_not_configured))
                    return@launch
                }
                accountId = response.data.accountId
                billingManager.loadProductDetails(response.data.productIds)
                _uiState.value = _uiState.value.copy(availablePlans = billingManager.availablePlans.value.map {
                    PlanUiModel(it.productId, it.title, billingManager.getPriceString(it),
                        billingManager.getTrialString(it), false, it)
                })
                val purchases = billingManager.queryPurchases() ?: return@launch
                if (purchases.isEmpty()) billingManager.inactive()
                for (purchase in purchases) {
                    if (purchase.purchaseState == Purchase.PurchaseState.PENDING) billingManager.pending()
                    else if (purchase.purchaseState == Purchase.PurchaseState.PURCHASED) verifyAndActivate(purchase, false)
                }
            } finally { _uiState.value = _uiState.value.copy(isLoading = false) }
        }
    }

    private suspend fun loadServerSubscription() {
        val sdf = SimpleDateFormat("dd.MM.yyyy", Locale.getDefault())
        when (val result = safeApiCall { appContext.apiClient.service.getSubscription() }) {
            is NetworkResult.Success -> {
                val sub = result.data.subscription ?: return
                val planState = result.data.planState
                val plan = planState?.plan ?: sub.plan ?: if (sub.isActive == true) "premium" else "free"
                val unlimited = sub.isUnlimited || sub.isAdmin || plan == "admin"
                val statusText = when {
                    unlimited -> appContext.getString(R.string.plan_unlimited)
                    plan == "family" -> "Family"
                    sub.status == "trial" -> appContext.getString(R.string.trial_period) + " · Premium"
                    plan == "premium" -> "Premium"
                    else -> "Free"
                }
                val expiryText = when {
                    unlimited -> appContext.getString(R.string.plan_no_expiry)
                    plan != "family" && sub.status == "trial" && sub.trialEndsAt != null -> {
                        val d = sub.daysRemaining ?: 0
                        appContext.getString(R.string.expires_in_days, d, sdf.format(Date(sub.trialEndsAt)))
                    }
                    sub.isActive == true && sub.currentPeriodEndsAt != null ->
                        appContext.getString(R.string.plan_valid_until, sdf.format(Date(sub.currentPeriodEndsAt)))
                    else -> ""
                }
                _uiState.value = _uiState.value.copy(
                    serverSub = sub,
                    planState = planState,
                    serverStatusText = statusText,
                    serverExpiryText = expiryText,
                    isServerActive = plan in setOf("premium", "family", "admin"),
                    daysRemaining = sub.daysRemaining
                )
            }
            is NetworkResult.Error -> {
                _uiState.value = _uiState.value.copy(error = result.message,
                    serverStatusText = _uiState.value.serverStatusText.ifBlank {
                        appContext.getString(R.string.offline_subscription_note)
                    })
            }
            else -> {}
        }
    }


    fun subscribe(activity: Activity, plan: PlanUiModel) {
        when (val result = billingManager.launchBillingFlow(activity, plan.productDetails, accountId)) {
            is PurchaseResult.Error -> billingManager.fail(result.message)
            PurchaseResult.Cancelled -> billingManager.inactive()
            else -> {}
        }
    }

    private suspend fun verifyAndActivate(purchase: Purchase, notify: Boolean) {
        verificationMutex.lock()
        try {
            billingManager.verifying()
            _uiState.value = _uiState.value.copy(isVerifying = true, purchaseSuccess = false)
            when (val result = repo.verifyPurchase(purchase.purchaseToken, purchase.products.firstOrNull().orEmpty(), appContext.packageName)) {
                is NetworkResult.Success -> {
                    val verified = result.data
                    if (verified.ok && verified.verified) {
                        billingManager.confirmed()
                        if (verified.active && verified.acknowledged) {
                            billingManager.activate(purchase.products.firstOrNull().orEmpty(), verified.expiresAt)
                            _uiState.value = _uiState.value.copy(purchaseSuccess = notify)
                        } else billingManager.inactive()
                        loadServerSubscription()
                    } else billingManager.fail(appContext.getString(R.string.purchase_sync_failed))
                }
                is NetworkResult.Error -> {
                    billingManager.fail(appContext.getString(R.string.purchase_sync_failed))
                    PurchaseSyncWorker.enqueue(appContext)
                }
                else -> {}
            }
        } finally {
            _uiState.value = _uiState.value.copy(isVerifying = false)
            verificationMutex.unlock()
        }
    }

    fun clearMessages() { _uiState.value = _uiState.value.copy(error = null, purchaseSuccess = false) }
    override fun onCleared() {
        billingManager.removePurchaseListener(purchaseListener)
        billingManager.disconnect()
        super.onCleared()
    }
}
