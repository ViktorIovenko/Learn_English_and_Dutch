package app.parallellingvo.data.api

import android.content.res.Resources
import app.parallellingvo.BuildConfig
import app.parallellingvo.utils.PreferencesManager
import app.parallellingvo.utils.SessionBoundary
import com.google.gson.GsonBuilder
import com.google.gson.JsonDeserializer
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import okhttp3.HttpUrl
import okhttp3.HttpUrl.Companion.toHttpUrl
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.io.IOException
import java.util.concurrent.TimeUnit

class ApiClient(private val preferencesManager: PreferencesManager) {

    // API authentication uses bearer tokens only; no browser session cookies persist.
    fun clearCookies() { httpClient.dispatcher.cancelAll() }

    private data class ApiSession(val generation: Long, val userId: String, val token: String, val origin: HttpUrl, val preview: String, val previewAds: Boolean)

    internal val httpClient: OkHttpClient = OkHttpClient.Builder()
        .addNetworkInterceptor { chain ->
            val session = chain.request().tag(ApiSession::class.java)
            if (session != null && (session.generation % 2L != 0L || session.generation != SessionBoundary.generation)) {
                throw IOException("Session changed")
            }
            val url = chain.request().url
            if (url.scheme != "https") throw IOException("HTTPS required")
            if (session != null && (url.host != session.origin.host || url.port != session.origin.port)) {
                throw IOException("Cross-origin API redirect blocked")
            }
            val builder = chain.request().newBuilder()
                .removeHeader("Authorization").removeHeader("Cookie").removeHeader("X-User-Id")
                .removeHeader("X-Client").removeHeader("X-Device-Language")
                .removeHeader("X-Admin-Plan-Preview").removeHeader("X-Admin-Preview-Ads")
            if (session != null && url.scheme == "https" && url.host == session.origin.host &&
                url.port == session.origin.port) {
                builder.header("X-User-Id", session.userId)
                    .header("X-Client", "android")
                    .header("X-Device-Language", systemLanguageCode())
                if (session.token.isNotBlank()) {
                    builder.header("Authorization", "Bearer ${session.token}")
                    if (session.preview.isNotBlank()) builder.header("X-Admin-Plan-Preview", session.preview)
                        .header("X-Admin-Preview-Ads", session.previewAds.toString())
                }
            }
            chain.proceed(builder.build())
        }
        .addInterceptor(HttpLoggingInterceptor().apply {
            // Auth requests contain passwords, verifiers and bearer tokens.
            level = HttpLoggingInterceptor.Level.NONE
        })
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .writeTimeout(60, TimeUnit.SECONDS)
        .callTimeout(90, TimeUnit.SECONDS)
        .build()

    private val booleanDeserializer = JsonDeserializer<Boolean> { json, _, _ ->
            when {
                json == null || json.isJsonNull -> false
                json.isJsonPrimitive && json.asJsonPrimitive.isBoolean -> json.asBoolean
                json.isJsonPrimitive && json.asJsonPrimitive.isNumber -> json.asInt != 0
                json.isJsonPrimitive && json.asJsonPrimitive.isString -> {
                    val value = json.asString.trim().lowercase()
                    value == "true" || value == "1" || value == "yes"
                }
                else -> false
            }
        }

    private val gson = GsonBuilder()
        .registerTypeAdapter(Boolean::class.javaObjectType, booleanDeserializer)
        .registerTypeAdapter(Boolean::class.javaPrimitiveType, booleanDeserializer)
        .create()

    val service: ApiService
        get() {
        val generation = SessionBoundary.generation
        val userId = runBlocking { preferencesManager.userId.first() }
        val token = runBlocking { preferencesManager.authToken.first() }
        val baseUrl = runBlocking { preferencesManager.serverUrl.first() }
            .ifBlank { BuildConfig.BASE_URL }
            .let { if (it.endsWith("/")) it else "$it/" }

        if (generation % 2L != 0L || generation != SessionBoundary.generation) throw IOException("Session changed")
        val origin = baseUrl.toHttpUrl()
        require(origin.scheme == "https" && origin.username.isEmpty() && origin.password.isEmpty()) {
            "HTTPS server required"
        }
        val preview = runBlocking { preferencesManager.adminPreviewPlan.first() }
        val previewAds = runBlocking { preferencesManager.adminPreviewAds.first() }
        if (generation != SessionBoundary.generation) throw IOException("Session changed")
        val session = ApiSession(generation, userId, token, origin, preview, previewAds)
        return Retrofit.Builder()
            .baseUrl(baseUrl)
            .callFactory { request ->
                httpClient.newCall(request.newBuilder().tag(ApiSession::class.java, session).build())
            }
            .addConverterFactory(GsonConverterFactory.create(gson))
            .build()
            .create(ApiService::class.java)
    }

    private fun systemLanguageCode(): String =
        Resources.getSystem().configuration.locales[0].language
}
