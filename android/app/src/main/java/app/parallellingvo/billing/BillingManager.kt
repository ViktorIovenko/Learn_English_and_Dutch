package app.parallellingvo.billing

import android.app.Activity
import android.content.Context
import com.android.billingclient.api.*
import app.parallellingvo.R
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlin.coroutines.resume

sealed class BillingState {
    object Loading : BillingState()
    object NotSubscribed : BillingState()
    object Initiated : BillingState()
    object Pending : BillingState()
    object Received : BillingState()
    object Verifying : BillingState()
    object Confirmed : BillingState()
    data class Active(val productId: String, val expiryMs: Long?) : BillingState()
    data class Error(val message: String) : BillingState()
}

sealed class PurchaseResult {
    data class Error(val message: String, val code: Int? = null) : PurchaseResult()
    object Cancelled : PurchaseResult()
    object Pending : PurchaseResult()
}

class BillingManager(private val context: Context) {
    private val _billingState = MutableStateFlow<BillingState>(BillingState.Loading)
    val billingState: StateFlow<BillingState> = _billingState
    private val _availablePlans = MutableStateFlow<List<ProductDetails>>(emptyList())
    val availablePlans: StateFlow<List<ProductDetails>> = _availablePlans
    private var client: BillingClient? = null
    private val listeners = mutableListOf<(Purchase) -> Unit>()

    suspend fun connect(): Boolean {
        if (client?.isReady == true) return true
        client?.endConnection()
        val billing = BillingClient.newBuilder(context)
            .setListener { result, purchases ->
                when (result.responseCode) {
                    BillingClient.BillingResponseCode.OK -> purchases.orEmpty().forEach { received(it) }
                    BillingClient.BillingResponseCode.USER_CANCELED -> { _billingState.value = BillingState.NotSubscribed }
                    else -> fail(context.getString(R.string.google_play_unavailable, result.responseCode.toString()))
                }
            }
            .enablePendingPurchases(PendingPurchasesParams.newBuilder().enableOneTimeProducts().enablePrepaidPlans().build())
            .enableAutoServiceReconnection()
            .build()
        client = billing
        return suspendCancellableCoroutine { cont ->
            cont.invokeOnCancellation { billing.endConnection() }
            billing.startConnection(object : BillingClientStateListener {
                override fun onBillingSetupFinished(result: BillingResult) {
                    val ok = result.responseCode == BillingClient.BillingResponseCode.OK
                    if (!ok) fail(context.getString(R.string.google_play_unavailable, result.responseCode.toString()))
                    if (cont.isActive) cont.resume(ok)
                }
                override fun onBillingServiceDisconnected() {
                    fail(context.getString(R.string.google_play_disconnected))
                    if (cont.isActive) cont.resume(false)
                }
            })
        }
    }

    suspend fun loadProductDetails(productIds: List<String>) {
        _availablePlans.value = emptyList()
        if (productIds.isEmpty()) return
        val billing = client ?: return
        val params = QueryProductDetailsParams.newBuilder().setProductList(productIds.map {
            QueryProductDetailsParams.Product.newBuilder().setProductId(it)
                .setProductType(BillingClient.ProductType.SUBS).build()
        }).build()
        val result = suspendCancellableCoroutine { cont ->
            billing.queryProductDetailsAsync(params) { status, details ->
                if (cont.isActive) cont.resume(status to details.productDetailsList)
            }
        }
        if (result.first.responseCode == BillingClient.BillingResponseCode.OK) {
            _availablePlans.value = result.second.filter { details ->
                details.subscriptionOfferDetails?.firstOrNull()?.pricingPhases?.pricingPhaseList
                    ?.let { phases -> phases.isNotEmpty() && phases.all { period(it.billingPeriod).isNotBlank() } } == true
            }
        } else fail(context.getString(R.string.google_play_unavailable, result.first.responseCode.toString()))
    }

    suspend fun queryPurchases(): List<Purchase>? {
        val billing = client ?: return null
        val params = QueryPurchasesParams.newBuilder().setProductType(BillingClient.ProductType.SUBS).build()
        val result = suspendCancellableCoroutine { cont ->
            billing.queryPurchasesAsync(params) { status, purchases ->
                if (cont.isActive) cont.resume(status to purchases)
            }
        }
        if (result.first.responseCode != BillingClient.BillingResponseCode.OK) {
            fail(context.getString(R.string.google_play_unavailable, result.first.responseCode.toString()))
            return null
        }
        if (result.second.isEmpty()) _billingState.value = BillingState.NotSubscribed
        return result.second
    }

    private fun received(purchase: Purchase) {
        _billingState.value = if (purchase.purchaseState == Purchase.PurchaseState.PENDING)
            BillingState.Pending else BillingState.Received
        if (purchase.purchaseState == Purchase.PurchaseState.PURCHASED) {
            PurchaseSyncWorker.enqueue(context)
            listeners.toList().forEach { it(purchase) }
        }
    }

    fun launchBillingFlow(activity: Activity, details: ProductDetails, accountId: String): PurchaseResult {
        val billing = client ?: return PurchaseResult.Error(context.getString(R.string.billing_client_not_initialized))
        if (accountId.isBlank()) return PurchaseResult.Error(context.getString(R.string.verification_error, "account"))
        val offer = details.subscriptionOfferDetails?.firstOrNull()
            ?: return PurchaseResult.Error(context.getString(R.string.no_product_offers))
        val params = BillingFlowParams.newBuilder().setObfuscatedAccountId(accountId)
            .setProductDetailsParamsList(listOf(BillingFlowParams.ProductDetailsParams.newBuilder()
                .setProductDetails(details).setOfferToken(offer.offerToken).build())).build()
        _billingState.value = BillingState.Initiated
        val result = billing.launchBillingFlow(activity, params)
        return when (result.responseCode) {
            BillingClient.BillingResponseCode.OK -> PurchaseResult.Pending
            BillingClient.BillingResponseCode.USER_CANCELED -> PurchaseResult.Cancelled
            else -> PurchaseResult.Error(context.getString(R.string.purchase_error, result.responseCode.toString()), result.responseCode)
        }
    }

    fun verifying() { _billingState.value = BillingState.Verifying }
    fun pending() { _billingState.value = BillingState.Pending }
    fun confirmed() { _billingState.value = BillingState.Confirmed }
    fun activate(productId: String, expiry: Long?) { _billingState.value = BillingState.Active(productId, expiry) }
    fun inactive() { _billingState.value = BillingState.NotSubscribed }
    fun fail(message: String) { _billingState.value = BillingState.Error(message) }
    fun addPurchaseListener(listener: (Purchase) -> Unit) { listeners.add(listener) }
    fun removePurchaseListener(listener: (Purchase) -> Unit) { listeners.remove(listener) }

    fun getPriceString(details: ProductDetails): String = details.subscriptionOfferDetails?.firstOrNull()
        ?.pricingPhases?.pricingPhaseList?.lastOrNull()?.let { "${it.formattedPrice} / ${period(it.billingPeriod)}" } ?: "—"

    fun getTrialString(details: ProductDetails): String? = details.subscriptionOfferDetails?.firstOrNull()
        ?.pricingPhases?.pricingPhaseList?.firstOrNull { it.priceAmountMicros == 0L && it.billingCycleCount > 0 }
        ?.let { "${period(it.billingPeriod)} ${context.getString(R.string.free)}" }

    private fun period(value: String): String {
        val parts = Regex("(\\d+)([YMWD])").findAll(value).toList()
        if (parts.isEmpty() || "P" + parts.joinToString("") { it.value } != value) return ""
        return runCatching {
            val units = mapOf("Y" to android.icu.util.MeasureUnit.YEAR, "M" to android.icu.util.MeasureUnit.MONTH,
                "W" to android.icu.util.MeasureUnit.WEEK, "D" to android.icu.util.MeasureUnit.DAY)
            val measures = parts.map { android.icu.util.Measure(it.groupValues[1].toInt(), units.getValue(it.groupValues[2])) }
            android.icu.text.MeasureFormat.getInstance(context.resources.configuration.locales[0],
                android.icu.text.MeasureFormat.FormatWidth.WIDE).formatMeasures(*measures.toTypedArray())
        }.getOrDefault("")
    }

    fun disconnect() { client?.endConnection(); client = null }
}
