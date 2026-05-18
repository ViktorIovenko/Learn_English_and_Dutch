package com.learnwords.app.ui.subscription

import android.app.Activity
import android.app.Application
import android.util.Log
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.android.billingclient.api.ProductDetails
import com.android.billingclient.api.Purchase
import com.learnwords.app.LearnWordsApp
import com.learnwords.app.billing.BillingConfig
import com.learnwords.app.billing.BillingManager
import com.learnwords.app.billing.BillingState
import com.learnwords.app.billing.PurchaseResult
import com.learnwords.app.data.api.SubscriptionDto
import com.learnwords.app.utils.NetworkResult
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

    private val repo = LearnWordsApp.instance.repository
    private val billingManager = BillingManager(app.applicationContext)

    private val _uiState = MutableStateFlow(SubscriptionUiState())
    val uiState: StateFlow<SubscriptionUiState> = _uiState

    private val purchaseListener: (Purchase) -> Unit = { purchase ->
        viewModelScope.launch {
            verifyAndActivate(purchase)
        }
    }

    init {
        billingManager.addPurchaseListener(purchaseListener)
        loadAll()
    }

    fun loadAll() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)

            // 1. Загружаем статус с сервера
            loadServerSubscription()

            // 2. Подключаемся к Google Play и проверяем покупки
            billingManager.connect {
                viewModelScope.launch {
                    billingManager.checkExistingSubscriptions()
                    billingManager.loadProductDetails()
                    updateBillingUiState()
                }
            }

            // Подписываемся на изменения состояния Billing
            launch {
                billingManager.billingState.collectLatest { state ->
                    val isActive = state is BillingState.Active
                    val productId = (state as? BillingState.Active)?.productId
                    _uiState.value = _uiState.value.copy(
                        billingState = state,
                        isGooglePlayActive = isActive,
                        googlePlayProductId = productId,
                        isLoading = false
                    )
                }
            }
        }
    }

    private suspend fun loadServerSubscription() {
        val sdf = SimpleDateFormat("dd.MM.yyyy", Locale.getDefault())
        when (val result = repo.getSubscription()) {
            is NetworkResult.Success -> {
                val sub = result.data
                val statusText = when (sub.status) {
                    "trial"  -> "Пробный период"
                    "active" -> "Активная подписка"
                    else     -> "Нет подписки"
                }
                val expiryText = when {
                    sub.status == "trial" && sub.trialEndsAt != null -> {
                        val d = sub.daysRemaining ?: 0
                        "Истекает через $d дн. (${sdf.format(Date(sub.trialEndsAt))})"
                    }
                    sub.currentPeriodEndsAt != null ->
                        "Следующее списание: ${sdf.format(Date(sub.currentPeriodEndsAt))}"
                    else -> ""
                }
                _uiState.value = _uiState.value.copy(
                    serverSub = sub,
                    serverStatusText = statusText,
                    serverExpiryText = expiryText,
                    isServerActive = sub.isActive == true || sub.status == "trial",
                    daysRemaining = sub.daysRemaining
                )
            }
            is NetworkResult.Error -> {
                // Не критично — продолжаем показывать UI без статуса сервера
                Log.w("SubVM", "Failed to load server sub: ${result.message}")
            }
            else -> {}
        }
    }

    private fun updateBillingUiState() {
        val plans = billingManager.availablePlans.value.map { details ->
            PlanUiModel(
                productId = details.productId,
                title = when (details.productId) {
                    BillingConfig.SUBSCRIPTION_MONTHLY_ID -> "Ежемесячная"
                    BillingConfig.SUBSCRIPTION_YEARLY_ID  -> "Годовая"
                    else -> details.title
                },
                priceString = billingManager.getPriceString(details),
                trialString = billingManager.getTrialString(details),
                isPopular = details.productId == BillingConfig.SUBSCRIPTION_YEARLY_ID,
                productDetails = details
            )
        }
        _uiState.value = _uiState.value.copy(availablePlans = plans)
    }

    // ─── Покупка подписки ─────────────────────────────────────────────────

    fun subscribe(activity: Activity, plan: PlanUiModel) {
        val result = billingManager.launchBillingFlow(activity, plan.productDetails)
        when (result) {
            is PurchaseResult.Error -> _uiState.value = _uiState.value.copy(
                error = "Ошибка покупки: ${result.message}"
            )
            PurchaseResult.Cancelled -> { /* пользователь закрыл диалог — ничего не делаем */ }
            else -> { /* Pending — ждём callback в purchaseListener */ }
        }
    }

    // ─── Верификация покупки на сервере ───────────────────────────────────

    private suspend fun verifyAndActivate(purchase: Purchase) {
        _uiState.value = _uiState.value.copy(isVerifying = true, error = null)

        val packageName = getApplication<LearnWordsApp>().packageName
        val productId = purchase.products.firstOrNull() ?: ""

        when (val result = repo.verifyPurchase(
            purchaseToken = purchase.purchaseToken,
            productId = productId,
            packageName = packageName
        )) {
            is NetworkResult.Success -> {
                if (result.data.ok == true) {
                    _uiState.value = _uiState.value.copy(
                        isVerifying = false,
                        purchaseSuccess = true,
                        isServerActive = true,
                        serverStatusText = "Подписка активна"
                    )
                } else {
                    _uiState.value = _uiState.value.copy(
                        isVerifying = false,
                        error = "Ошибка верификации: ${result.data.error}"
                    )
                }
            }
            is NetworkResult.Error -> {
                // Покупка прошла в Google Play — сообщаем пользователю
                // даже если сервер не ответил (можно повторить позже)
                _uiState.value = _uiState.value.copy(
                    isVerifying = false,
                    purchaseSuccess = true,
                    error = "Покупка прошла, но синхронизация с сервером не удалась. Повторите через 'Обновить'."
                )
            }
            else -> { _uiState.value = _uiState.value.copy(isVerifying = false) }
        }
    }

    fun clearMessages() {
        _uiState.value = _uiState.value.copy(error = null, purchaseSuccess = false)
    }

    override fun onCleared() {
        super.onCleared()
        billingManager.removePurchaseListener(purchaseListener)
        billingManager.disconnect()
    }
}
