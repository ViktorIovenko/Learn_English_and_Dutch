package app.parallellingvo.ui.ads

import app.parallellingvo.data.api.*
import com.google.gson.Gson
import org.junit.Assert.*
import org.junit.Test

class AdvertisingContractTest {
    private val gson = Gson()
    private fun user(plan: String = "free", child: Boolean = false, admin: Boolean = false, preview: String? = null): UserInfo =
        gson.fromJson("""{"user_id":"test","is_admin":$admin,"account_type":"${if (child) "child" else "standard"}",
            "subscription":{"access":true,"paid_access":${plan != "free"},"plan":"$plan"},
            "plan_state":{"plan":"$plan","preview":${preview?.let { "\"$it\"" } ?: "null"},
                "features":{"learning":true,"ads":${plan == "free"},"family":${plan == "family"}},
                "paid_ai_available":${plan != "free"}}}""", UserInfo::class.java)

    private fun page(serve: String = "live", render: String = "text", preview: Boolean = false): AdsPageResponse =
        gson.fromJson("""{"ok":true,"mode":"live","decision":{"serve":"$serve","needs_consent":false},
            "slots":[{"placement":"lesson_bottom","size":"320x50","width":320,"height":50,
                "label":"Ad","render":"$render","preview":$preview,"creative_id":12,
                "headline":"Example","body":"Copy","cta":"Details",
                "image_url":"https://example.org/banner.png","click_url":"https://example.org/offer"}]}""", AdsPageResponse::class.java)

    @Test fun dtoMatchesServerNamesAndNumericCreativeId() {
        val slot = page(render = "image").slots!!.single()
        assertEquals(12, slot.creativeId!!.asInt)
        assertEquals("https://example.org/banner.png", slot.imageUrl)
        assertEquals("https://example.org/offer", slot.clickUrl)
        assertEquals(320, slot.width ?: 0)
    }

    @Test fun stringDemoCreativeIdAndConsentMap() {
        val response = gson.fromJson("""{"ok":true,"mode":"off","decision":{"serve":"demo"},
            "slots":[{"placement":"lesson_bottom","render":"demo","preview":true,"creative_id":"demo-books"}],
            "consent_prompt":{"title":"Title","text":"Copy","accept":"Yes","decline":"No"}}""", AdsPageResponse::class.java)
        assertEquals("demo-books", response.slots!!.single().creativeId!!.asString)
        assertEquals("Yes", response.consentPrompt!!.accept)
    }

    @Test fun freeAccessIsIndependentOfPayment() {
        val me = user()
        assertTrue(me.canUseApp)
        assertFalse(me.isPaid)
        assertTrue(me.showAds)
        assertFalse(me.paidAiAvailable)
        assertFalse(me.canManageFamily)
    }

    @Test fun paidAndChildAccountsDoNotRenderAds() {
        val page = page()
        for (me in listOf(user("premium"), user("family"), user(child = true))) {
            assertFalse(me.showAds)
            assertFalse(AdRenderPolicy.canRender(page.slots!!.single(), page, me))
        }
        assertTrue(user("family").canManageFamily)
        assertFalse(user("premium").canManageFamily)
    }

    @Test fun textAndImageNeedExplicitLiveAuthorization() {
        for (render in listOf("text", "image")) {
            val response = page(render = render)
            assertTrue(AdRenderPolicy.canRender(response.slots!!.single(), response, user()))
            assertFalse(AdRenderPolicy.canRender(response.slots.single(), response.copy(mode = "off"), user()))
            assertFalse(AdRenderPolicy.canRender(response.slots.single().copy(preview = null), response, user()))
        }
    }

    @Test fun previewsOnlyRenderLocalVariants() {
        val admin = user(admin = true, preview = "free")
        for (render in listOf("demo", "mock", "placeholder")) {
            val response = page("demo", render, true)
            assertTrue(AdRenderPolicy.canRender(response.slots!!.single(), response, admin))
            assertFalse(AdRenderPolicy.isLive(response, admin))
        }
        for (render in listOf("image", "text", "html")) {
            val response = page("demo", render, true)
            assertFalse(AdRenderPolicy.canRender(response.slots!!.single(), response, admin))
        }
        val live = page()
        assertFalse(AdRenderPolicy.isLive(live, admin))
        assertFalse(AdRenderPolicy.canRender(live.slots!!.single(), live, admin))
    }

    @Test fun previewPlanControlsFeaturesWithoutRemovingRealAdmin() {
        for (plan in listOf("free", "premium", "family")) {
            val me = user(plan, admin = true, preview = plan)
            assertTrue(me.isAdmin == true)
            assertFalse(me.isAdminUi)
            assertEquals(plan, me.effectivePlan)
            assertEquals(plan == "family", me.canManageFamily)
        }
    }

    @Test fun missingSlotsAndNoneDecisionCannotProduceAdvertising() {
        val response = gson.fromJson("""{"ok":true,"mode":"live","decision":{"serve":"none"},"slots":[]}""", AdsPageResponse::class.java)
        assertTrue(response.slots.orEmpty().isEmpty())
        assertFalse(AdRenderPolicy.canRender(page().slots!!.single(), response, user()))
    }

    @Test fun onlyHttpsUrlsWithoutCredentialsCanOpen() {
        assertEquals("https://example.org/path", AdRenderPolicy.httpsUrl("https://example.org/path"))
        for (url in listOf(null, "", "http://example.org", "javascript:alert(1)", "file:///x", "intent://x",
            "https://", "https:///x", "https://u:p@example.org", "https://example.org/has space")) {
            assertNull(AdRenderPolicy.httpsUrl(url))
        }
    }
}
