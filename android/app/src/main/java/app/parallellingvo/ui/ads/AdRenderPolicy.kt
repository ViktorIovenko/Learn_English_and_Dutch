package app.parallellingvo.ui.ads

import app.parallellingvo.data.api.*

/** Fail closed before image loading, navigation or event recording. */
object AdRenderPolicy {
    fun isLive(page: AdsPageResponse, user: UserInfo): Boolean =
        page.ok == true && page.mode == "live" && page.decision?.serve == "live" &&
            user.showAds && user.isAdmin != true && user.planState?.preview.isNullOrBlank()

    fun canRender(slot: AdSlotDto, page: AdsPageResponse, user: UserInfo): Boolean =
        if (!user.showAds || page.ok != true) false
        else if (isLive(page, user)) slot.preview == false && slot.render in setOf("text", "image")
        else page.decision?.serve == "demo" && slot.preview == true && slot.render in setOf("demo", "mock", "placeholder")

    fun httpsUrl(value: String?): String? = value?.takeIf {
        val uri = runCatching { java.net.URI(it) }.getOrNull()
        uri?.scheme == "https" && !uri.host.isNullOrBlank() && uri.rawUserInfo == null
    }
}
