package app.parallellingvo.ui.ads

import android.content.ActivityNotFoundException
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.net.Uri
import android.util.TypedValue
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.FrameLayout
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import androidx.core.content.ContextCompat
import app.parallellingvo.R
import app.parallellingvo.utils.copyBoundedTo
import java.io.ByteArrayOutputStream
import androidx.lifecycle.LifecycleCoroutineScope
import com.google.android.material.button.MaterialButton
import app.parallellingvo.data.api.AdSlotDto
import app.parallellingvo.data.api.AdsConsentPromptDto
import app.parallellingvo.data.api.AdsConsentRequest
import app.parallellingvo.data.api.AdsEventRequest
import app.parallellingvo.data.api.ApiService
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import java.util.concurrent.TimeUnit

/**
 * Free-plan banner for one placement (Awin material, no ad SDK).
 *
 * The server decides everything (/api/ads/page): plan, child profile, consent
 * and material. The banner image is fetched with a separate HTTP client that
 * sends no app token, user id or cookies; a click opens the Awin tracking link
 * in the browser. Nothing about words or learning progress leaves the app.
 */
class AdBannerController(
    private val container: FrameLayout,
    private val api: () -> ApiService,
    private val scope: LifecycleCoroutineScope,
    private val page: String,
    private val placements: List<String>,
) {
    private val context get() = container.context

    fun load() {
        scope.launch {
            val response = runCatching {
                api().getAdsPage(page, device(), placements.joinToString(","))
            }.getOrNull()
            val body = response?.body()
            if (response == null || !response.isSuccessful || body?.ok != true) {
                hide(); return@launch
            }
            val slot = body.slots.orEmpty().firstOrNull { it.placement in placements }
            when {
                slot != null -> render(slot)
                body.consentPrompt != null -> renderConsent(body.consentPrompt)
                else -> hide()
            }
        }
    }

    private fun device(): String =
        if (context.resources.configuration.smallestScreenWidthDp >= 600) "tablet" else "phone"

    private fun dp(value: Int): Int = TypedValue.applyDimension(
        TypedValue.COMPLEX_UNIT_DIP, value.toFloat(), context.resources.displayMetrics
    ).toInt()

    private fun hide() {
        container.removeAllViews()
        container.visibility = View.GONE
    }

    private fun label(text: String?): TextView = TextView(context).apply {
        this.text = (text ?: "Ad").uppercase()
        setTextSize(TypedValue.COMPLEX_UNIT_SP, 10f)
        setTextColor(ContextCompat.getColor(context, R.color.colorTextSecondary))
        gravity = Gravity.CENTER
    }

    private fun render(slot: AdSlotDto) {
        val width = dp(slot.width ?: 320)
        val height = dp(slot.height ?: 50)
        val column = LinearLayout(context).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER_HORIZONTAL
            setPadding(0, dp(4), 0, dp(4))
        }
        column.addView(label(slot.label))
        val clickUrl = slot.clickUrl?.takeIf { it.startsWith("https://") }
        val imageUrl = slot.imageUrl?.takeIf { it.startsWith("https://") }
        val body: View = if (slot.render == "image" && imageUrl != null) {
            ImageView(context).apply {
                scaleType = ImageView.ScaleType.FIT_CENTER
                contentDescription = slot.alt ?: slot.advertiser
                scope.launch {
                    val bitmap = withContext(Dispatchers.IO) { fetchImage(imageUrl) }
                    if (bitmap == null) hide() else setImageBitmap(bitmap)
                }
            }
        } else {
            textCard(slot)
        }
        val params = LinearLayout.LayoutParams(
            width.coerceAtMost(container.resources.displayMetrics.widthPixels - dp(16)), height
        )
        column.addView(body, params)
        if (clickUrl != null && slot.preview != true) {
            body.setOnClickListener {
                event("click", slot)
                try {
                    context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(clickUrl)))
                } catch (_: ActivityNotFoundException) {
                }
            }
        }
        container.removeAllViews()
        container.addView(column, FrameLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT
        ))
        container.visibility = View.VISIBLE
        if (slot.preview != true) {
            scope.launch {
                delay(1000)
                if (container.isShown) event("impression", slot)
            }
        }
    }

    private fun textCard(slot: AdSlotDto): View = LinearLayout(context).apply {
        orientation = LinearLayout.HORIZONTAL
        gravity = Gravity.CENTER_VERTICAL
        setPadding(dp(12), dp(4), dp(12), dp(4))
        background = GradientDrawable().apply {
            cornerRadius = dp(10).toFloat()
            setColor(ContextCompat.getColor(context, R.color.colorInfoBackground))
            setStroke(dp(1), ContextCompat.getColor(context, if (slot.preview == true) R.color.colorAccent else R.color.colorDivider))
        }
        val copy = LinearLayout(context).apply { orientation = LinearLayout.VERTICAL }
        copy.addView(TextView(context).apply {
            text = slot.headline.orEmpty()
            setTypeface(typeface, Typeface.BOLD)
            setTextColor(ContextCompat.getColor(context, R.color.colorOnBackground))
            maxLines = 1
        })
        if (!slot.body.isNullOrBlank() && (slot.height ?: 50) > 50) {
            copy.addView(TextView(context).apply {
                text = slot.body
                setTextSize(TypedValue.COMPLEX_UNIT_SP, 12f)
                maxLines = 2
            })
        }
        addView(copy, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
        if (!slot.cta.isNullOrBlank()) {
            addView(TextView(context).apply {
                text = slot.cta
                setTextColor(Color.WHITE)
                setPadding(dp(10), dp(4), dp(10), dp(4))
                background = GradientDrawable().apply {
                    cornerRadius = dp(999).toFloat()
                    setColor(Color.parseColor("#4A0EA3"))
                }
            })
        }
    }

    /** Non-blocking in-app consent; the choice is stored on the server. */
    private fun renderConsent(prompt: AdsConsentPromptDto) {
        val card = LinearLayout(context).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(12), dp(8), dp(12), dp(8))
            background = GradientDrawable().apply {
                cornerRadius = dp(12).toFloat()
                setColor(ContextCompat.getColor(context, R.color.colorSurface))
                setStroke(dp(1), ContextCompat.getColor(context, R.color.colorDivider))
            }
        }
        card.addView(TextView(context).apply {
            text = prompt.title
            setTypeface(typeface, Typeface.BOLD)
        })
        card.addView(TextView(context).apply {
            text = prompt.text
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 12f)
        })
        val actions = LinearLayout(context).apply { orientation = LinearLayout.HORIZONTAL }
        listOf("granted" to prompt.accept, "denied" to prompt.decline).forEach { (choice, title) ->
            actions.addView(MaterialButton(context).apply {
                text = title
                setOnClickListener {
                    hide()
                    scope.launch {
                        val saved = runCatching { api().setAdsConsent(AdsConsentRequest(choice)) }
                            .getOrNull()?.isSuccessful == true
                        if (saved && choice == "granted") load()
                    }
                }
            })
        }
        card.addView(actions)
        container.removeAllViews()
        container.addView(card, FrameLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT
        ).apply { setMargins(dp(8), dp(4), dp(8), dp(4)) })
        container.visibility = View.VISIBLE
    }

    private fun event(name: String, slot: AdSlotDto) {
        val id = slot.creativeId?.takeIf { it.isJsonPrimitive && it.asJsonPrimitive.isNumber }?.asInt ?: return
        scope.launch {
            runCatching { api().sendAdsEvent(AdsEventRequest(name, slot.placement, id, device())) }
        }
    }

    private fun fetchImage(url: String): Bitmap? = runCatching {
        imageClient.newCall(Request.Builder().url(url).build()).execute().use { response ->
            if (!response.isSuccessful) return@use null
            val body = response.body ?: return@use null
            if (body.contentLength() > MAX_IMAGE_BYTES) return@use null
            val bytes = ByteArrayOutputStream().use { output ->
                body.byteStream().use { it.copyBoundedTo(output, MAX_IMAGE_BYTES.toLong()) }
                output.toByteArray()
            }
            val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
            BitmapFactory.decodeByteArray(bytes, 0, bytes.size, bounds)
            if (bounds.outWidth <= 0 || bounds.outHeight <= 0 ||
                bounds.outWidth.toLong() * bounds.outHeight > 4_000_000L) return@use null
            BitmapFactory.decodeByteArray(bytes, 0, bytes.size)
        }
    }.getOrNull()

    companion object {
        private const val MAX_IMAGE_BYTES = 1_000_000

        // Deliberately separate from ApiClient: no Authorization, X-User-Id or cookies.
        private val imageClient: OkHttpClient by lazy {
            OkHttpClient.Builder()
                .connectTimeout(10, TimeUnit.SECONDS)
                .readTimeout(10, TimeUnit.SECONDS)
                .callTimeout(20, TimeUnit.SECONDS)
                .followRedirects(true)
                .build()
        }
    }
}
