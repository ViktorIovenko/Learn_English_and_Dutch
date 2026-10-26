package app.parallellingvo.billing

import app.parallellingvo.utils.safeApiCall

import android.content.Context
import androidx.work.*
import com.android.billingclient.api.Purchase
import app.parallellingvo.ParallelLingvoApp
import app.parallellingvo.utils.NetworkResult
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withTimeout
import java.util.concurrent.TimeUnit

/** Play persists purchases; tokens are never copied to WorkManager's database. */
class PurchaseSyncWorker(context: Context, params: WorkerParameters) : CoroutineWorker(context, params) {
    override suspend fun doWork(): Result {
        val app = applicationContext as ParallelLingvoApp
        if (app.preferencesManager.authToken.first().isBlank()) return Result.success()
        val manager = BillingManager(applicationContext)
        return try {
            withTimeout(90_000) {
                if (!manager.connect()) return@withTimeout Result.retry()
                val purchases = manager.queryPurchases() ?: return@withTimeout Result.retry()
                val sync = safeApiCall { app.apiClient.service.syncPlaySubscriptions() }
                var retry = sync is NetworkResult.Error && (sync.code == null || sync.code == 429 || sync.code!! >= 500)
                for (purchase in purchases) {
                    if (purchase.purchaseState != Purchase.PurchaseState.PURCHASED) continue
                    val result = app.repository.verifyPurchase(purchase.purchaseToken,
                        purchase.products.firstOrNull().orEmpty(), applicationContext.packageName)
                    if (result is NetworkResult.Error && (result.code == null || result.code == 429 || result.code!! >= 500)) retry = true
                    if (result is NetworkResult.Success && !result.data.verified) retry = true
                }
                if (retry) Result.retry() else Result.success()
            }
        } catch (_: kotlinx.coroutines.TimeoutCancellationException) {
            Result.retry()
        } catch (cancelled: kotlinx.coroutines.CancellationException) {
            throw cancelled
        } catch (_: Exception) {
            Result.retry()
        } finally { manager.disconnect() }
    }

    companion object {
        private val constraints = Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build()
        fun enqueue(context: Context) {
            WorkManager.getInstance(context).enqueueUniqueWork("play-purchase-sync", ExistingWorkPolicy.KEEP,
                OneTimeWorkRequestBuilder<PurchaseSyncWorker>().setConstraints(constraints)
                    .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 30, TimeUnit.SECONDS).build())
        }
        fun schedule(context: Context) {
            WorkManager.getInstance(context).enqueueUniquePeriodicWork("play-purchase-periodic", ExistingPeriodicWorkPolicy.UPDATE,
                PeriodicWorkRequestBuilder<PurchaseSyncWorker>(15, TimeUnit.MINUTES).setConstraints(constraints).build())
            enqueue(context)
        }
    }
}
