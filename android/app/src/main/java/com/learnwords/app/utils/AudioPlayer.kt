package com.learnwords.app.utils

import android.content.Context
import android.media.MediaPlayer
import android.net.Uri

class AudioPlayer(private val context: Context) {

    private var mediaPlayer: MediaPlayer? = null

    fun play(url: String, onComplete: (() -> Unit)? = null) {
        stop()
        try {
            mediaPlayer = MediaPlayer().apply {
                setDataSource(context, Uri.parse(url))
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
        mediaPlayer?.let {
            try {
                if (it.isPlaying) it.stop()
                it.release()
            } catch (_: Exception) {}
        }
        mediaPlayer = null
    }

    fun release() = stop()
}
