package com.learnwords.app.utils

import android.content.Context
import android.media.MediaPlayer
import android.net.Uri
import com.learnwords.app.LearnWordsApp
import kotlinx.coroutines.*

class AudioPlayer(private val context: Context) {

    private var mediaPlayer: MediaPlayer? = null
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
    private var playbackJob: Job? = null

    fun play(url: String, onComplete: (() -> Unit)? = null) {
        stop()
        playbackJob = scope.launch {
            val app = context.applicationContext as LearnWordsApp
            val cached = app.wordContentCache.getOrDownloadAudio(url, app.apiClient.httpClient)
                ?: return@launch
            playLocal(cached.absolutePath, onComplete)
        }
    }

    private fun playLocal(path: String, onComplete: (() -> Unit)?) {
        try {
            mediaPlayer = MediaPlayer().apply {
                setDataSource(context, Uri.fromFile(java.io.File(path)))
                setOnPreparedListener { start() }
                setOnCompletionListener {
                    onComplete?.invoke()
                    release()
                    mediaPlayer = null
                }
                setOnErrorListener { _, _, _ ->
                    release()
                    mediaPlayer = null
                    false
                }
                prepareAsync()
            }
        } catch (e: Exception) {
            mediaPlayer = null
        }
    }

    fun stop() {
        playbackJob?.cancel()
        playbackJob = null
        mediaPlayer?.let {
            try {
                if (it.isPlaying) it.stop()
                it.release()
            } catch (_: Exception) {}
        }
        mediaPlayer = null
    }

    fun release() {
        stop()
        scope.cancel()
    }
}
