package app.parallellingvo.utils

import android.net.Uri
import android.util.Base64
import java.security.MessageDigest
import java.security.SecureRandom

data class PendingAndroidAuth(
    val flowId: String,
    val verifier: String,
    val serverUrl: String,
    val provider: String,
    val createdAt: Long = System.currentTimeMillis(),
    val linking: Boolean = false,
    val ownerUserId: String = "",
    val nativeClientId: String? = null,
    val nativeIdToken: String? = null
)

fun newAuthVerifier(): String = ByteArray(32).also { SecureRandom().nextBytes(it) }.let {
    Base64.encodeToString(it, Base64.URL_SAFE or Base64.NO_WRAP or Base64.NO_PADDING)
}

fun authChallenge(verifier: String): String = MessageDigest.getInstance("SHA-256")
    .digest(verifier.toByteArray(Charsets.UTF_8)).joinToString("") { "%02x".format(it.toInt() and 0xff) }

fun normalizedAuthServer(value: String): String? = runCatching {
    val uri = Uri.parse(value.trim())
    if (uri.scheme != "https" || uri.host.isNullOrBlank() || uri.userInfo != null ||
        uri.query != null || uri.fragment != null || uri.path !in listOf(null, "", "/")) null
    else uri.buildUpon().path("").build().toString().trimEnd('/')
}.getOrNull()
