package app.parallellingvo.ui.ads

import android.graphics.Rect
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.net.Uri
import android.util.TypedValue
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.*
import androidx.browser.customtabs.CustomTabsIntent
import androidx.core.content.ContextCompat
import androidx.core.view.doOnLayout
import androidx.lifecycle.*
import app.parallellingvo.ParallelLingvoApp
import app.parallellingvo.R
import app.parallellingvo.data.api.*
import app.parallellingvo.data.repository.AdvertisingRepository
import app.parallellingvo.utils.NetworkResult
import app.parallellingvo.utils.SessionBoundary
import coil.ImageLoader
import coil.request.CachePolicy
import coil.request.ImageRequest
import coil.request.Disposable
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import okhttp3.OkHttpClient
import java.util.concurrent.TimeUnit

/** Native server-controlled advertising. Preview has no external I/O or events. */
class AdBannerController(
    private val container: FrameLayout,
    private val owner: LifecycleOwner,
    private val session: AdsSessionViewModel,
    private val page: String,
    private val placements: List<String>,
) {
    private val app = ParallelLingvoApp.instance
    private val repo = AdvertisingRepository(app.apiClient)
    private val context get() = container.context
    private val scope get() = owner.lifecycleScope
    private var image: Disposable? = null
    private var generation = 0L
    private var renderJob: Job? = null
    private var refreshJob: Job? = null
    private var consentDialog: androidx.appcompat.app.AlertDialog? = null
    private var consentAttempted = false

    init {
        scope.launch {
            owner.repeatOnLifecycle(Lifecycle.State.RESUMED) {
                try {
                    combine(app.preferencesManager.adminPreviewPlan, app.preferencesManager.adminPreviewAds,
                        app.preferencesManager.userId) { plan, ads, user -> Triple(plan, ads, user) }
                        .distinctUntilChanged().collectLatest { refreshJob?.cancelAndJoin(); loadNow() }
                } finally {
                    refreshJob?.cancel()
                    hide()
                }
            }
        }
    }

    fun load() {
        refreshJob?.cancel()
        refreshJob = scope.launch { if (owner.lifecycle.currentState.isAtLeast(Lifecycle.State.RESUMED)) loadNow() }
    }

    private suspend fun loadNow() {
        hide()
        val me = (app.repository.getMe() as? NetworkResult.Success)?.data ?: return
        if (!me.showAds) return
        val result = repo.getAdsForPage(page, device(), placements)
        val body = (result as? NetworkResult.Success)?.data ?: return
        if (body.ok != true) return
        val preview = !me.planState?.preview.isNullOrBlank()
        val live = AdRenderPolicy.isLive(body, me)
        if (body.decision?.serve == "none") {
            if (body.decision?.needsConsent == true && !preview && !consentAttempted) {
                body.consentPrompt?.let { showConsent(it) }
            }
            return
        }
        val slot = body.slots.orEmpty().firstOrNull { it.placement in placements } ?: return
        if (AdRenderPolicy.canRender(slot, body, me)) render(slot, live)
    }

    private fun device() = if (context.resources.configuration.smallestScreenWidthDp >= 600) "tablet" else "phone"
    private fun dp(value: Int) = TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP,
        value.toFloat(), context.resources.displayMetrics).toInt()

    private fun hide() {
        generation++
        image?.dispose(); image = null
        renderJob?.cancel(); renderJob = null
        consentDialog?.dismiss(); consentDialog = null
        container.removeAllViews()
        container.visibility = View.GONE
    }

    private fun render(slot: AdSlotDto, live: Boolean) {
        val version = generation
        val accountGeneration = SessionBoundary.generation
        val column = LinearLayout(context).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER_HORIZONTAL
        }
        column.addView(TextView(context).apply {
            text = slot.label.orEmpty()
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 10f)
            gravity = Gravity.CENTER
            setTextColor(ContextCompat.getColor(context, R.color.colorTextSecondary))
        })
        val frame = FrameLayout(context)
        column.addView(frame, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(50)))
        var ready = slot.render != "image"
        val body: View = if (slot.render == "image") ImageView(context).apply {
            scaleType = ImageView.ScaleType.FIT_CENTER
            contentDescription = slot.alt ?: slot.advertiser
        } else textCard(slot)
        frame.addView(body, FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT))
        container.addView(column)
        container.visibility = View.VISIBLE
        // The available container width, never physical screen pixels, sets the ratio.
        frame.doOnLayout {
            if (version != generation) return@doOnLayout
            val width = (slot.width ?: 320).coerceAtLeast(1)
            val height = (slot.height ?: 50).coerceAtLeast(1)
            frame.layoutParams = frame.layoutParams.apply { this.height = (frame.width.toLong() * height / width).toInt().coerceAtLeast(1) }
        }
        if (live && slot.render == "image") {
            val url = AdRenderPolicy.httpsUrl(slot.imageUrl) ?: run { hide(); return }
            image = imageLoader(context).enqueue(ImageRequest.Builder(context)
                .data(url).size(1024, 1024).target(body as ImageView)
                .memoryCachePolicy(CachePolicy.DISABLED).diskCachePolicy(CachePolicy.DISABLED)
                .listener(onSuccess = { _, _ -> if (version == generation) ready = true },
                    onError = { _, _ -> if (version == generation) hide() })
                .build())
        }
        val click = if (live) AdRenderPolicy.httpsUrl(slot.clickUrl) else null
        if (click != null) body.setOnClickListener {
            body.isEnabled = false
            scope.launch {
                if (version != generation || accountGeneration != SessionBoundary.generation) return@launch
                withTimeoutOrNull(1500) { repo.recordAdClick(slot, device()) }
                if (version == generation && accountGeneration == SessionBoundary.generation && container.isShown) {
                    try { CustomTabsIntent.Builder().build().launchUrl(context, Uri.parse(click)) }
                    catch (_: android.content.ActivityNotFoundException) { }
                    catch (_: SecurityException) { }
                }
                body.isEnabled = true
            }
        }
        if (live) renderJob = scope.launch {
            var visibleSince = 0L
            val rect = Rect()
            while (version == generation && accountGeneration == SessionBoundary.generation) {
                val visible = ready && frame.isShown && frame.hasWindowFocus() &&
                    frame.getGlobalVisibleRect(rect) && rect.width().toLong() * rect.height() >= frame.width.toLong() * frame.height / 2
                val now = android.os.SystemClock.elapsedRealtime()
                if (!visible) visibleSince = 0L
                else if (visibleSince == 0L) visibleSince = now
                else if (now - visibleSince >= 1000) {
                    val key = "$accountGeneration:${slot.placement}:${slot.creativeId}"
                    if (session.recordOnce(key)) repo.recordAdImpression(slot, device())
                    break
                }
                delay(200)
            }
        }
    }

    private fun textCard(slot: AdSlotDto): View = LinearLayout(context).apply {
        orientation = LinearLayout.HORIZONTAL
        gravity = Gravity.CENTER_VERTICAL
        setPadding(dp(8), dp(2), dp(8), dp(2))
        background = GradientDrawable().apply {
            cornerRadius = dp(8).toFloat()
            setColor(ContextCompat.getColor(context, R.color.colorInfoBackground))
            setStroke(dp(1), ContextCompat.getColor(context, R.color.colorDivider))
        }
        val copy = LinearLayout(context).apply { orientation = LinearLayout.VERTICAL }
        copy.addView(TextView(context).apply {
            text = if (slot.render == "placeholder") "${slot.placement}  ${slot.size.orEmpty()}" else slot.headline.orEmpty()
            setTypeface(typeface, Typeface.BOLD)
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 12f)
            maxLines = 2
        })
        if (!slot.body.isNullOrBlank()) copy.addView(TextView(context).apply {
            text = slot.body
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 11f)
            maxLines = if ((slot.height ?: 50) > 50) 3 else 1
        })
        addView(copy, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
        if (!slot.cta.isNullOrBlank()) addView(TextView(context).apply {
            text = slot.cta
            setPadding(dp(6), 0, 0, 0)
            maxWidth = dp(100)
            setTextColor(ContextCompat.getColor(context, R.color.colorPrimary))
        })
    }

    private fun showConsent(prompt: AdsConsentPromptDto) {
        if (listOf(prompt.title, prompt.text, prompt.accept, prompt.decline).any { it.isNullOrBlank() }) return
        consentAttempted = true
        fun save(choice: String) {
            scope.launch {
                val response = repo.setAdsConsent(choice)
                if (response is NetworkResult.Success && response.data.ok && choice == "granted") load()
            }
        }
        consentDialog = androidx.appcompat.app.AlertDialog.Builder(context)
            .setTitle(prompt.title).setMessage(prompt.text)
            .setPositiveButton(prompt.accept) { _, _ -> save("granted") }
            .setNegativeButton(prompt.decline) { _, _ -> save("denied") }
            .show()
    }

    companion object {
        private var loader: ImageLoader? = null
        private fun imageLoader(context: android.content.Context): ImageLoader = loader ?: ImageLoader.Builder(context.applicationContext)
            .okHttpClient(OkHttpClient.Builder().followSslRedirects(false)
                .addInterceptor { chain ->
                    val response = chain.proceed(chain.request())
                    try {
                        val bounded = response.peekBody(1_000_001)
                        if (bounded.contentLength() > 1_000_000) throw java.io.IOException("Image too large")
                        response.newBuilder().body(bounded).build()
                    } finally { response.close() }
                }
                .addNetworkInterceptor { chain ->
                    check(chain.request().url.scheme == "https")
                    chain.proceed(chain.request())
                }
                .connectTimeout(10, TimeUnit.SECONDS).readTimeout(10, TimeUnit.SECONDS)
                .callTimeout(20, TimeUnit.SECONDS).build())
            .build().also { loader = it }
    }
}
