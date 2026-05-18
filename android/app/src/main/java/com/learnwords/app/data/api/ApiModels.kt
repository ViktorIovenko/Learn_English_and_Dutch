package com.learnwords.app.data.api

import com.google.gson.annotations.SerializedName

// ─── Auth ────────────────────────────────────────────────────────────────────

data class LoginRequest(
    @SerializedName("user_id") val userId: String,
    @SerializedName("password") val password: String
)

data class LoginTokenRequest(
    @SerializedName("auth") val auth: String
)

data class LoginResponse(
    @SerializedName("ok") val ok: Boolean,
    @SerializedName("user_id") val userId: String?,
    @SerializedName("error") val error: String?
)

data class UserInfo(
    @SerializedName("user_id") val userId: String,
    @SerializedName("username") val username: String?,
    @SerializedName("first_name") val firstName: String?,
    @SerializedName("subscription") val subscription: SubscriptionDto?,
    @SerializedName("is_admin") val isAdmin: Boolean?
)

// ─── Lessons ─────────────────────────────────────────────────────────────────

data class LessonDto(
    @SerializedName("lesson") val lesson: String,
    @SerializedName("number") val number: String?,
    @SerializedName(value = "word_count", alternate = ["words_count"]) val wordCount: Int,
    @SerializedName("hidden") val hidden: Boolean = false
)

// ─── Words ───────────────────────────────────────────────────────────────────

data class WordDto(
    @SerializedName("id") val id: Int,
    @SerializedName("lesson") val lesson: String?,
    @SerializedName("number") val number: String?,
    @SerializedName("nl") val nl: String?,
    @SerializedName("en") val en: String?,
    @SerializedName("ru") val ru: String?,
    @SerializedName("ex_nl") val exNl: String?,
    @SerializedName("ex_en") val exEn: String?,
    @SerializedName("ex_ru") val exRu: String?,
    @SerializedName("audio_nl") val audioNl: String?,
    @SerializedName("audio_en") val audioEn: String?,
    @SerializedName("audio_ru") val audioRu: String?,
    @SerializedName("difficult") val difficult: Boolean = false,
    @SerializedName("status") val status: String?,
    @SerializedName("editable") val editable: Boolean = true
)

data class WordsResponse(
    @SerializedName("words") val words: List<WordDto>,
    @SerializedName("total") val total: Int?,
    @SerializedName("page") val page: Int?,
    @SerializedName("per_page") val perPage: Int?
)

data class UpdateWordRequest(
    @SerializedName("nl") val nl: String? = null,
    @SerializedName("en") val en: String? = null,
    @SerializedName("ru") val ru: String? = null,
    @SerializedName("ex_nl") val exNl: String? = null,
    @SerializedName("ex_en") val exEn: String? = null,
    @SerializedName("ex_ru") val exRu: String? = null,
    @SerializedName("difficult") val difficult: Boolean? = null
)

data class UpdateWordResponse(
    @SerializedName("ok") val ok: Boolean,
    @SerializedName("word") val word: WordDto?,
    @SerializedName("error") val error: String?
)

data class ImportWordsRequest(
    @SerializedName("lesson") val lesson: String,
    @SerializedName("words") val words: List<Map<String, String?>>
)

data class ImportWordsResponse(
    @SerializedName("imported") val imported: Int,
    @SerializedName("skipped") val skipped: Int,
    @SerializedName("lesson") val lesson: String?
)

// ─── Difficult ───────────────────────────────────────────────────────────────

data class SetDifficultRequest(
    @SerializedName("word_id") val wordId: Int,
    @SerializedName("difficult") val difficult: Boolean
)

// ─── Languages ───────────────────────────────────────────────────────────────

data class LanguageOption(
    @SerializedName("code") val code: String,
    @SerializedName("name") val name: String,
    @SerializedName("flag") val flag: String?
)

data class UserLanguageDto(
    @SerializedName("priority") val priority: Int,
    @SerializedName("lang_code") val langCode: String,
    @SerializedName("name") val name: String?
)

data class SaveLanguagesRequest(
    @SerializedName("languages") val languages: List<String>
)

// ─── Subscription ─────────────────────────────────────────────────────────────

data class SubscriptionDto(
    @SerializedName("status") val status: String?,
    @SerializedName("trial_ends_at") val trialEndsAt: Long?,
    @SerializedName("current_period_ends_at") val currentPeriodEndsAt: Long?,
    @SerializedName("days_remaining") val daysRemaining: Int?,
    @SerializedName("is_active") val isActive: Boolean?,
    @SerializedName("provider") val provider: String?,
    @SerializedName("cancel_at_period_end") val cancelAtPeriodEnd: Boolean?
)

data class VerifyPurchaseRequest(
    @SerializedName("purchase_token") val purchaseToken: String,
    @SerializedName("product_id") val productId: String,
    @SerializedName("package_name") val packageName: String
)

data class VerifyPurchaseResponse(
    @SerializedName("ok") val ok: Boolean,
    @SerializedName("status") val status: String?,
    @SerializedName("expires_at") val expiresAt: Long?,
    @SerializedName("error") val error: String?
)

// ─── Lessons management ───────────────────────────────────────────────────────

data class SetHiddenRequest(
    @SerializedName("lesson") val lesson: String,
    @SerializedName("hidden") val hidden: Boolean
)

data class DeleteLessonsRequest(
    @SerializedName("lessons") val lessons: List<String>
)

// ─── Audio ───────────────────────────────────────────────────────────────────

data class EnsureAudioRequest(
    @SerializedName("ids") val ids: List<Int>,
    @SerializedName("langs") val langs: List<String> = listOf("nl", "en", "ru")
)

data class EnsureAudioResponse(
    @SerializedName("ok") val ok: Boolean? = null,
    @SerializedName("items") val items: List<EnsureAudioItem> = emptyList(),
    @SerializedName("generated") val generated: Int = 0,
    @SerializedName("skipped") val skipped: Int = 0,
    @SerializedName("error") val error: String? = null
)

data class EnsureAudioItem(
    @SerializedName("id") val id: Int,
    @SerializedName("nl") val nl: String?,
    @SerializedName("en") val en: String?,
    @SerializedName("ru") val ru: String?,
    @SerializedName("ok") val ok: Boolean? = null
)

// ─── Sharing ─────────────────────────────────────────────────────────────────

data class ShareSetDto(
    @SerializedName("token") val token: String,
    @SerializedName("title") val title: String?,
    @SerializedName("lesson") val lesson: String?,
    @SerializedName("word_count") val wordCount: Int?,
    @SerializedName("owner") val owner: String?,
    @SerializedName("expires_at") val expiresAt: Long?,
    @SerializedName("import_count") val importCount: Int?,
    @SerializedName("max_imports") val maxImports: Int?,
    @SerializedName("words_preview") val wordsPreview: List<WordDto>?
)

data class CreateShareRequest(
    @SerializedName("lessons") val lessons: List<String>,
    @SerializedName("title") val title: String?,
    @SerializedName("expires_hours") val expiresHours: Int?
)

data class CreateShareResponse(
    @SerializedName("token") val token: String,
    @SerializedName("url") val url: String
)

data class ImportShareResponse(
    @SerializedName("imported") val imported: Int,
    @SerializedName("lesson") val lesson: String?
)

// ─── Progress ─────────────────────────────────────────────────────────────────

data class ProgressEvent(
    @SerializedName("scope") val scope: String,
    @SerializedName("event_type") val eventType: String,
    @SerializedName("event_ts") val eventTs: Long,
    @SerializedName("payload") val payload: Map<String, Any?>?
)

data class SyncProgressRequest(
    @SerializedName("events") val events: List<ProgressEvent>
)

// ─── Ollama / AI generation ──────────────────────────────────────────────────

data class GenerateByTopicRequest(
    @SerializedName("topic") val topic: String,
    @SerializedName("level") val level: String,
    @SerializedName("count") val count: Int,
    @SerializedName("languages") val languages: List<String>
)

data class TranslateWordRequest(
    @SerializedName("word") val word: String,
    @SerializedName("from_lang") val fromLang: String,
    @SerializedName("to_langs") val toLangs: List<String>
)

data class GenericResponse(
    @SerializedName("ok") val ok: Boolean?,
    @SerializedName("error") val error: String?,
    @SerializedName("message") val message: String?
)

// ─── Admin ────────────────────────────────────────────────────────────────────

data class AdminUserDto(
    @SerializedName("user_id") val userId: String,
    @SerializedName("username") val username: String,
    @SerializedName("first_name") val firstName: String,
    @SerializedName("status") val status: String,
    @SerializedName("provider") val provider: String,
    @SerializedName("is_unlimited") val isUnlimited: Boolean,
    @SerializedName("current_period_ends_at") val currentPeriodEndsAt: Long?,
    @SerializedName("trial_ends_at") val trialEndsAt: Long?
)

data class AdminUsersResponse(
    @SerializedName("ok") val ok: Boolean,
    @SerializedName("users") val users: List<AdminUserDto>
)

data class GrantAccessRequest(
    @SerializedName("user_id") val userId: String
)
