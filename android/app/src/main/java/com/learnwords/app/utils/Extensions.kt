package com.learnwords.app.utils

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.view.View
import android.widget.Toast
import com.learnwords.app.R
import com.learnwords.app.data.api.WordDto
import com.learnwords.app.data.db.WordEntity

fun Context.toast(message: String, long: Boolean = false) {
    Toast.makeText(this, message, if (long) Toast.LENGTH_LONG else Toast.LENGTH_SHORT).show()
}

fun Context.copyToClipboard(label: String, text: String) {
    val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
    clipboard.setPrimaryClip(ClipData.newPlainText(label, text))
    toast(getString(R.string.copy_done))
}

fun Context.familyErrorMessage(error: String): String = when (error.substringAfterLast(':').trim()) {
    "parent_limit_reached" -> getString(R.string.family_error_parent_limit)
    "child_cannot_be_parent" -> getString(R.string.family_error_child_parent)
    "cannot_link_self" -> getString(R.string.family_error_self)
    "invalid_or_expired_pairing_code" -> getString(R.string.family_error_expired)
    "child_account_not_found" -> getString(R.string.family_error_child_missing)
    else -> error
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
    de = de,
    fr = fr,
    es = es,
    ita = ita,
    pt = pt,
    pl = pl,
    uk = uk,
    exNl = exNl,
    exEn = exEn,
    exRu = exRu,
    exDe = exDe,
    exFr = exFr,
    exEs = exEs,
    exIt = exIt,
    exPt = exPt,
    exPl = exPl,
    exUk = exUk,
    audioNl = audioNl,
    audioEn = audioEn,
    audioRu = audioRu,
    audioDe = audioDe,
    audioFr = audioFr,
    audioEs = audioEs,
    audioIt = audioIt,
    audioPt = audioPt,
    audioPl = audioPl,
    audioUk = audioUk,
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
    de = de,
    fr = fr,
    es = es,
    ita = ita,
    pt = pt,
    pl = pl,
    uk = uk,
    exNl = exNl,
    exEn = exEn,
    exRu = exRu,
    exDe = exDe,
    exFr = exFr,
    exEs = exEs,
    exIt = exIt,
    exPt = exPt,
    exPl = exPl,
    exUk = exUk,
    audioNl = audioNl,
    audioEn = audioEn,
    audioRu = audioRu,
    audioDe = audioDe,
    audioFr = audioFr,
    audioEs = audioEs,
    audioIt = audioIt,
    audioPt = audioPt,
    audioPl = audioPl,
    audioUk = audioUk,
    difficult = difficult,
    status = status
)

fun WordDto.getWordByLang(lang: String): String? = when (lang) {
    "nl" -> nl
    "en" -> en
    "ru" -> ru
    "de" -> de
    "fr" -> fr
    "es" -> es
    "it" -> ita
    "pt" -> pt
    "pl" -> pl
    "uk" -> uk
    else -> nl ?: en ?: ru
}

fun WordDto.getExampleByLang(lang: String): String? = when (lang) {
    "nl" -> exNl
    "en" -> exEn
    "ru" -> exRu
    "de" -> exDe
    "fr" -> exFr
    "es" -> exEs
    "it" -> exIt
    "pt" -> exPt
    "pl" -> exPl
    "uk" -> exUk
    else -> null
}

fun WordDto.getAudioByLang(lang: String): String? = when (lang) {
    "nl" -> audioNl
    "en" -> audioEn
    "ru" -> audioRu
    "de" -> audioDe
    "fr" -> audioFr
    "es" -> audioEs
    "it" -> audioIt
    "pt" -> audioPt
    "pl" -> audioPl
    "uk" -> audioUk
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
