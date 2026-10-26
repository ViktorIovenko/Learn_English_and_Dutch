package app.parallellingvo.data.repository

import app.parallellingvo.data.api.*
import app.parallellingvo.utils.*
import kotlinx.coroutines.CancellationException

/** No creative persistence: offline learning never depends on advertising. */
class AdvertisingRepository(private val client: ApiClient) {
    suspend fun getAdsForPage(page: String, device: String, placements: List<String>) =
        SessionBoundary.withSession { safeApiCall { client.service.getAdsPage(page, device, placements.joinToString(",")) } }

    suspend fun getAdsConsent() = SessionBoundary.withSession { safeApiCall { client.service.getAdsConsent() } }

    suspend fun setAdsConsent(choice: String) = SessionBoundary.withSession {
        safeApiCall { client.service.setAdsConsent(AdsConsentRequest(choice)) }
    }

    suspend fun recordAdImpression(slot: AdSlotDto, device: String) = event("impression", slot, device)
    suspend fun recordAdClick(slot: AdSlotDto, device: String) = event("click", slot, device)

    private suspend fun event(name: String, slot: AdSlotDto, device: String) = SessionBoundary.withSession {
        val id = slot.creativeId?.takeIf { it.isJsonPrimitive && it.asJsonPrimitive.isNumber }?.asInt
        if (slot.preview != false || slot.render !in setOf("text", "image") || id == null) return@withSession
        try { client.service.sendAdsEvent(AdsEventRequest(name, slot.placement, id, device)) }
        catch (e: CancellationException) { throw e }
        catch (_: Exception) { /* Advertising failures are silent. */ }
        Unit
    }
}
