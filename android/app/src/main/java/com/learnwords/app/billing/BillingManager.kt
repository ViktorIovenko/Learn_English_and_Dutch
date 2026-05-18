package com.learnwords.app.billing

import android.app.Activity
import android.content.Context
import android.util.Log
import com.android.billingclient.api.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlin.coroutines.resume

private const val TAG = "BillingManager"

/** Текущее состояние подписки со стороны Google Play */
sealed class BillingState {
    object Loading : BillingState()
    object NotSubscribed : BillingState()
    data class Active(
        val productId: String,
        val purchaseToken: String,
        val expiryMs: Long?
    ) : BillingState()
    data class Error(val message: String) : BillingState()
}

/** Результат попытки купить подписку */
sealed class PurchaseResult {
    data class Success(val purchase: Purchase) : PurchaseResult()
    data class Error(val message: String, val code: Int? = null) : PurchaseResult()
    object Cancelled : PurchaseResult()
    object Pending : PurchaseResult()
}

class BillingManager(private val context: Context) {

    private val _billingState = MutableStateFlow<BillingState>(BillingState.Loading)
    val billingState: StateFlow<BillingState> = _billingState

    private val _availablePlans = MutableStateFlow<List<ProductDetails>>(emptyList())
    val availablePlans: StateFlow<List<ProductDetails>> = _availablePlans

    private var billingClient: BillingClient? = null

    // ─── Подключение к Google Play ─────────────────────────────────────────

    fun connect(onReady: () -> Unit = {}) {
        billingClient = BillingClient.newBuilder(context)
            .setListener { billingResult, purchases ->
                handlePurchaseUpdate(billingResult, purchases)
            }
            .enablePendingPurchases()
            .build()

        billingClient!!.startConnection(object : BillingClientStateListener {
            override fun onBillingSetupFinished(result: BillingResult) {
                if (result.responseCode == BillingClient.BillingResponseCode.OK) {
                    Log.d(TAG, "Billing client connected")
                    onReady()
                } else {
                    Log.w(TAG, "Billing setup failed: ${result.debugMessage}")
                    _billingState.value = BillingState.Error("Google Play недоступен: ${result.debugMessage}")
                }
            }

            override fun onBillingServiceDisconnected() {
                Log.w(TAG, "Billing service disconnected")
                _billingState.value = BillingState.Error("Соединение с Google Play прервано")
            }
        })
    }

    // ─── Загрузка деталей планов (цены, описания) ──────────────────────────

    suspend fun loadProductDetails() {
        val client = billingClient ?: return
        if (!client.isReady) return

        val params = QueryProductDetailsParams.newBuilder()
            .setProductList(
                BillingConfig.ALL_SUBSCRIPTION_IDS.map { id ->
                    QueryProductDetailsParams.Product.newBuilder()
                        .setProductId(id)
                        .setProductType(BillingClient.ProductType.SUBS)
                        .build()
                }
            )
            .build()

        val result = suspendCancellableCoroutine { cont ->
            client.queryProductDetailsAsync(params) { billingResult, productDetailsList ->
                cont.resume(Pair(billingResult, productDetailsList))
            }
        }

        if (result.first.responseCode == BillingClient.BillingResponseCode.OK) {
            _availablePlans.value = result.second
            Log.d(TAG, "Loaded ${result.second.size} product(s)")
        } else {
            Log.w(TAG, "Failed to load products: ${result.first.debugMessage}")
        }
    }

    // ─── Проверка текущих активных подписок ───────────────────────────────

    suspend fun checkExistingSubscriptions() {
        val client = billingClient ?: run {
            _billingState.value = BillingState.NotSubscribed
            return
        }
        if (!client.isReady) {
            _billingState.value = BillingState.NotSubscribed
            return
        }

        val params = QueryPurchasesParams.newBuilder()
            .setProductType(BillingClient.ProductType.SUBS)
            .build()

        val result = suspendCancellableCoroutine { cont ->
            client.queryPurchasesAsync(params) { billingResult, purchases ->
                cont.resume(Pair(billingResult, purchases))
            }
        }

        if (result.first.responseCode != BillingClient.BillingResponseCode.OK) {
            _billingState.value = BillingState.Error(result.first.debugMessage)
            return
        }

        val activePurchase = result.second.firstOrNull { purchase ->
            purchase.purchaseState == Purchase.PurchaseState.PURCHASED
        }

        if (activePurchase != null) {
            val productId = activePurchase.products.firstOrNull() ?: ""
            _billingState.value = BillingState.Active(
                productId = productId,
                purchaseToken = activePurchase.purchaseToken,
                expiryMs = null  // Google Play не возвращает expiry напрямую — получай с бэкенда
            )
            // Подтвердить покупку если ещё не подтверждена
            if (!activePurchase.isAcknowledged) {
                acknowledgePurchase(activePurchase.purchaseToken)
            }
        } else {
            _billingState.value = BillingState.NotSubscribed
        }
    }

    // ─── Запуск потока покупки ─────────────────────────────────────────────

    fun launchBillingFlow(
        activity: Activity,
        productDetails: ProductDetails,
        offerToken: String? = null
    ): PurchaseResult {
        val client = billingClient
            ?: return PurchaseResult.Error("Billing client не инициализирован")

        // Берём первый доступный offer token если не передан явно
        val token = offerToken
            ?: productDetails.subscriptionOfferDetails?.firstOrNull()?.offerToken
            ?: return PurchaseResult.Error("Нет доступных предложений для этого продукта")

        val productDetailsParams = BillingFlowParams.ProductDetailsParams.newBuilder()
            .setProductDetails(productDetails)
            .setOfferToken(token)
            .build()

        val flowParams = BillingFlowParams.newBuilder()
            .setProductDetailsParamsList(listOf(productDetailsParams))
            .build()

        val result = client.launchBillingFlow(activity, flowParams)
        return when (result.responseCode) {
            BillingClient.BillingResponseCode.OK -> PurchaseResult.Pending  // диалог открылся — результат придёт в PurchasesUpdatedListener
            BillingClient.BillingResponseCode.USER_CANCELED -> PurchaseResult.Cancelled
            else -> PurchaseResult.Error(result.debugMessage, result.responseCode)
        }
    }

    // ─── Обработка обновлений покупки (callback) ─────────────────────────

    private fun handlePurchaseUpdate(billingResult: BillingResult, purchases: List<Purchase>?) {
        when (billingResult.responseCode) {
            BillingClient.BillingResponseCode.OK -> {
                purchases?.forEach { purchase ->
                    processPurchase(purchase)
                }
            }
            BillingClient.BillingResponseCode.USER_CANCELED -> {
                Log.d(TAG, "User cancelled purchase")
            }
            else -> {
                Log.w(TAG, "Purchase error: ${billingResult.debugMessage}")
                _billingState.value = BillingState.Error(billingResult.debugMessage)
            }
        }
    }

    private fun processPurchase(purchase: Purchase) {
        if (purchase.purchaseState == Purchase.PurchaseState.PURCHASED) {
            val productId = purchase.products.firstOrNull() ?: ""
            _billingState.value = BillingState.Active(
                productId = productId,
                purchaseToken = purchase.purchaseToken,
                expiryMs = null
            )
            if (!purchase.isAcknowledged) {
                acknowledgePurchase(purchase.purchaseToken)
            }
            // Оповещаем слушателей о новой покупке
            purchaseListeners.forEach { it(purchase) }
        }
    }

    // ─── Подтверждение покупки (обязательно в течение 3 дней) ────────────

    private fun acknowledgePurchase(purchaseToken: String) {
        val params = AcknowledgePurchaseParams.newBuilder()
            .setPurchaseToken(purchaseToken)
            .build()
        billingClient?.acknowledgePurchase(params) { result ->
            if (result.responseCode == BillingClient.BillingResponseCode.OK) {
                Log.d(TAG, "Purchase acknowledged: $purchaseToken")
            } else {
                Log.w(TAG, "Failed to acknowledge purchase: ${result.debugMessage}")
            }
        }
    }

    // ─── Слушатели покупок ────────────────────────────────────────────────

    private val purchaseListeners = mutableListOf<(Purchase) -> Unit>()

    fun addPurchaseListener(listener: (Purchase) -> Unit) {
        purchaseListeners.add(listener)
    }

    fun removePurchaseListener(listener: (Purchase) -> Unit) {
        purchaseListeners.remove(listener)
    }

    // ─── Вспомогательные методы ───────────────────────────────────────────

    /** Получить цену плана как строку, напр. "€4.99/мес" */
    fun getPriceString(productDetails: ProductDetails): String {
        val offer = productDetails.subscriptionOfferDetails?.firstOrNull()
        val phase = offer?.pricingPhases?.pricingPhaseList?.lastOrNull()
        return phase?.formattedPrice ?: when (productDetails.productId) {
            BillingConfig.SUBSCRIPTION_MONTHLY_ID -> BillingConfig.PRICE_MONTHLY_FALLBACK
            BillingConfig.SUBSCRIPTION_YEARLY_ID  -> BillingConfig.PRICE_YEARLY_FALLBACK
            else -> "—"
        }
    }

    /** Получить пробный период плана если есть (напр. "14 дней бесплатно") */
    fun getTrialString(productDetails: ProductDetails): String? {
        val offer = productDetails.subscriptionOfferDetails?.firstOrNull()
        val phases = offer?.pricingPhases?.pricingPhaseList ?: return null
        val freeTrial = phases.firstOrNull {
            it.priceAmountMicros == 0L && it.billingCycleCount > 0
        }
        return freeTrial?.let {
            val period = it.billingPeriod  // ISO 8601: "P7D", "P1M", etc.
            parsePeriodToRussian(period) + " бесплатно"
        }
    }

    private fun parsePeriodToRussian(iso8601: String): String {
        return when {
            iso8601.contains("7D")  -> "7 дней"
            iso8601.contains("14D") -> "14 дней"
            iso8601.contains("30D") -> "30 дней"
            iso8601.contains("1M")  -> "1 месяц"
            iso8601.contains("3M")  -> "3 месяца"
            else -> iso8601
        }
    }

    fun disconnect() {
        billingClient?.endConnection()
        billingClient = null
    }
}
