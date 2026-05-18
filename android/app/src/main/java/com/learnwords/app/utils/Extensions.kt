package com.learnwords.app.utils

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.view.View
import android.widget.Toast
import com.learnwords.app.data.api.WordDto
import com.learnwords.app.data.db.WordEntity

fun Context.toast(message: String, long: Boolean = false) {
    Toast.makeText(this, message, if (long) Toast.LENGTH_LONG else Toast.LENGTH_SHORT).show()
}

fun Context.copyToClipboard(label: String, text: String) {
    val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
    clipboard.setPrimaryClip(ClipData.newPlainText(label, text))
    toast("Скопировано в буфер обмена")
}

fun View.visible() { visibility = View.VISIBLE }
fun View.gone() { visibility = View.GONE }
fun View.invisible() { visibility = View.INVISIBLE }

fun WordDto.toEntity(): WordEntity = WordEntity(
    id = id,
    lesson = lesson,
    number = number,
    nl = nl,
    en = en,
    ru = ru,
    exNl = exNl,
    exEn = exEn,
    exRu = exRu,
    audioNl = audioNl,
    audioEn = audioEn,
    audioRu = audioRu,
    difficult = difficult,
    status = status
)

fun WordEntity.toDto(): WordDto = WordDto(
    id = id,
    lesson = lesson,
    number = number,
    nl = nl,
    en = en,
    ru = ru,
    exNl = exNl,
    exEn = exEn,
    exRu = exRu,
    audioNl = audioNl,
    audioEn = audioEn,
    audioRu = audioRu,
    difficult = difficult,
    status = status
)

fun WordDto.getWordByLang(lang: String): String? = when (lang) {
    "nl" -> nl
    "en" -> en
    "ru" -> ru
    else -> nl ?: en ?: ru
}

fun WordDto.getExampleByLang(lang: String): String? = when (lang) {
    "nl" -> exNl
    "en" -> exEn
    "ru" -> exRu
    else -> null
}

fun WordDto.getAudioByLang(lang: String): String? = when (lang) {
    "nl" -> audioNl
    "en" -> audioEn
    "ru" -> audioRu
    else -> null
}

fun Long.msToSeconds() = this / 1000
fun Long.msToMinutes() = this / 60000
fun Long.secToMinSec(): String {
    val m = this / 60
    val s = this % 60
    return "%d:%02d".format(m, s)
}

fun String.scrambleLetters(): List<Char> = this.filter { it.isLetter() || it == ' ' }
    .toMutableList().apply { shuffle() }
