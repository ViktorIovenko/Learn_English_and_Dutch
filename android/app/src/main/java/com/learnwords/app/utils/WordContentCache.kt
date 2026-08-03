package com.learnwords.app.utils

import android.content.Context
import com.google.gson.Gson
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext
import kotlinx.coroutines.flow.first
import okhttp3.OkHttpClient
import okhttp3.Request
import java.io.File
import java.security.MessageDigest

/** Общий дисковый LRU-кэш переводов и MP3. */
class WordContentCache(
    context: Context,
    private val preferencesManager: PreferencesManager
) {
    private val root = File(context.cacheDir, "word_content").apply { mkdirs() }
    private val gson = Gson()
    private val mutex = Mutex()

    suspend fun <T> getJson(key: String, type: Class<T>): T? = withContext(Dispatchers.IO) {
        mutex.withLock {
            val file = entryFile("translation:$key", ".json")
            if (!file.isFile) return@withLock null
            runCatching {
                file.setLastModified(System.currentTimeMillis())
                gson.fromJson(file.readText(Charsets.UTF_8), type)
            }.getOrNull()
        }
    }

    suspend fun putJson(key: String, value: Any) = withContext(Dispatchers.IO) {
        mutex.withLock {
            val target = entryFile("translation:$key", ".json")
            writeAtomically(target, gson.toJson(value).toByteArray(Charsets.UTF_8))
            trimLocked(configuredMaxBytes())
        }
    }

    suspend fun getOrDownloadAudio(url: String, client: OkHttpClient): File? =
        withContext(Dispatchers.IO) {
            mutex.withLock {
                val target = entryFile("audio:$url", ".mp3")
                if (target.isFile && target.length() > 0L) {
                    target.setLastModified(System.currentTimeMillis())
                    return@withLock target
                }

                val request = Request.Builder().url(url).get().build()
                runCatching {
                    client.newCall(request).execute().use { response ->
                        if (!response.isSuccessful) return@use null
                        val body = response.body ?: return@use null
                        val temp = File(target.parentFile, "${target.name}.tmp")
                        temp.outputStream().use { output ->
                            body.byteStream().use { input -> input.copyTo(output) }
                        }
                        if (temp.length() == 0L) {
                            temp.delete()
                            return@use null
                        }
                        if (target.exists()) target.delete()
                        if (!temp.renameTo(target)) {
                            temp.copyTo(target, overwrite = true)
                            temp.delete()
                        }
                        target.setLastModified(System.currentTimeMillis())
                        trimLocked(configuredMaxBytes())
                        target.takeIf { it.isFile }
                    }
                }.getOrNull()
            }
        }

    private fun entryFile(key: String, extension: String): File =
        File(root, sha256(key) + extension)

    private fun writeAtomically(target: File, bytes: ByteArray) {
        val temp = File(target.parentFile, "${target.name}.tmp")
        temp.writeBytes(bytes)
        if (target.exists()) target.delete()
        if (!temp.renameTo(target)) {
            temp.copyTo(target, overwrite = true)
            temp.delete()
        }
        target.setLastModified(System.currentTimeMillis())
    }

    suspend fun trimToConfiguredLimit() = withContext(Dispatchers.IO) {
        mutex.withLock { trimLocked(configuredMaxBytes()) }
    }

    private suspend fun configuredMaxBytes(): Long =
        preferencesManager.cacheLimitMb.first().toLong() * BYTES_PER_MIB

    private fun trimLocked(maxBytes: Long) {
        val files = root.listFiles()?.filter { it.isFile && !it.name.endsWith(".tmp") }
            ?.sortedBy { it.lastModified() }
            .orEmpty()
        var total = files.sumOf { it.length() }
        for (file in files) {
            if (total <= maxBytes) break
            val size = file.length()
            if (file.delete()) total -= size
        }
    }

    private fun sha256(value: String): String = MessageDigest.getInstance("SHA-256")
        .digest(value.toByteArray(Charsets.UTF_8))
        .joinToString("") { "%02x".format(it) }

    companion object {
        const val DEFAULT_CACHE_MB = 100
        const val MIN_CACHE_MB = 10
        const val MAX_CACHE_MB = 2048
        private const val BYTES_PER_MIB = 1024L * 1024L
    }
}
