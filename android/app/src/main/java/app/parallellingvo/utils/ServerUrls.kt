package app.parallellingvo.utils

import app.parallellingvo.BuildConfig
import okhttp3.HttpUrl.Companion.toHttpUrl
import okhttp3.HttpUrl.Companion.toHttpUrlOrNull

/** Rewrite only our retired host; preserve paths, query parameters and other hosts. */
fun migrateAppUrl(value: String): String {
    val url = value.trim()
    val parsed = url.toHttpUrlOrNull() ?: return url
    if (parsed.host != "learn.iovenko.eu" || parsed.username.isNotEmpty() || parsed.password.isNotEmpty()) {
        return url
    }
    val current = BuildConfig.BASE_URL.toHttpUrl()
    return parsed.newBuilder()
        .scheme(current.scheme)
        .host(current.host)
        .port(current.port)
        .build().toString()
}

fun currentServerUrl(value: String): String =
    migrateAppUrl(value).trimEnd('/').ifBlank { BuildConfig.BASE_URL.trimEnd('/') }
