package com.learnwords.app.data.api

import android.content.res.Resources
import com.learnwords.app.BuildConfig
import com.learnwords.app.utils.PreferencesManager
import com.google.gson.GsonBuilder
import com.google.gson.JsonDeserializer
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import okhttp3.JavaNetCookieJar
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.net.CookieManager
import java.net.CookiePolicy
import java.util.concurrent.TimeUnit

class ApiClient(private val preferencesManager: PreferencesManager) {

    private val cookieManager = CookieManager().apply {
        setCookiePolicy(CookiePolicy.ACCEPT_ALL)
    }

    internal val httpClient: OkHttpClient = OkHttpClient.Builder()
        .cookieJar(JavaNetCookieJar(cookieManager))
        .addInterceptor { chain ->
            val userId = runBlocking { preferencesManager.userId.first() }
            val authToken = runBlocking { preferencesManager.authToken.first() }
            val builder = chain.request().newBuilder()
                .addHeader("X-User-Id", userId)
                .addHeader("X-Client", "android")
                .addHeader("X-Device-Language", systemLanguageCode())
            if (authToken.isNotBlank()) {
                builder.addHeader("Authorization", "Bearer $authToken")
            }
            chain.proceed(builder.build())
        }
        .addInterceptor(HttpLoggingInterceptor().apply {
            level = if (BuildConfig.DEBUG)
                HttpLoggingInterceptor.Level.BODY
            else
                HttpLoggingInterceptor.Level.NONE
        })
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .writeTimeout(60, TimeUnit.SECONDS)
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
        val baseUrl = runBlocking { preferencesManager.serverUrl.first() }
            .ifBlank { BuildConfig.BASE_URL }
            .let { if (it.endsWith("/")) it else "$it/" }

        return Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(httpClient)
            .addConverterFactory(GsonConverterFactory.create(gson))
            .build()
            .create(ApiService::class.java)
    }

    private fun systemLanguageCode(): String =
        Resources.getSystem().configuration.locales[0].language
}
