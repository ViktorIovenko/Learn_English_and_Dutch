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
    @SerializedName("is_admin") val isAdmin: Boolean?,
    @SerializedName("account_type") val accountType: String? = null,
    @SerializedName("needs_account_type") val needsAccountType: Boolean = false,
    @SerializedName("is_parent") val isParent: Boolean = false,
    @SerializedName("children_count") val childrenCount: Int = 0,
    @SerializedName("ui_language") val uiLanguage: String? = null,
    @SerializedName("detected_ui_language") val detectedUiLanguage: String? = null,
    @SerializedName("ui_language_override") val uiLanguageOverride: String? = null
)

data class AccountTypeRequest(
    @SerializedName("account_type") val accountType: String
)

data class FamilyMemberDto(
    @SerializedName("user_id") val userId: String,
    @SerializedName("display_name") val displayName: String? = null,
    @SerializedName("username") val username: String? = null,
    @SerializedName("first_name") val firstName: String? = null,
    @SerializedName("last_name") val lastName: String? = null,
    @SerializedName("created_at") val createdAt: String? = null
)

data class FamilyStatusResponse(
    @SerializedName("ok") val ok: Boolean,
    @SerializedName("account_type") val accountType: String? = null,
    @SerializedName("needs_account_type") val needsAccountType: Boolean = false,
    @SerializedName("is_parent") val isParent: Boolean = false,
    @SerializedName("children") val children: List<FamilyMemberDto> = emptyList(),
    @SerializedName("parents") val parents: List<FamilyMemberDto> = emptyList(),
    @SerializedName("error") val error: String? = null
)

data class ChildLearningStatusResponse(
    @SerializedName("ok") val ok: Boolean = false,
    @SerializedName("is_child") val isChild: Boolean = false,
    @SerializedName("today_count") val todayCount: Int = 0,
    @SerializedName("daily_goal") val dailyGoal: Int = 25,
    @SerializedName("goal_complete") val goalComplete: Boolean = false,
    @SerializedName("mastery_count") val masteryCount: Int = 10,
    @SerializedName("status_milestone") val statusMilestone: Int = 0
)

data class DailyGoalResponse(
    @SerializedName("ok") val ok: Boolean = false,
    @SerializedName("goal_type") val goalType: String = "minutes",
    @SerializedName("goal_value") val goalValue: Int = 10,
    @SerializedName("minimum") val minimum: Int = 1,
    @SerializedName("maximum") val maximum: Int = 180,
    @SerializedName("error") val error: String? = null
)

data class SaveDailyGoalRequest(@SerializedName("goal_value") val goalValue: Int)

data class PairingCodeResponse(
    @SerializedName("ok") val ok: Boolean,
    @SerializedName("code") val code: String? = null,
    @SerializedName("token") val token: String? = null,
    @SerializedName("pairing_url") val pairingUrl: String? = null,
    @SerializedName("expires_in") val expiresIn: Int? = null,
    @SerializedName("error") val error: String? = null
)

data class LinkChildRequest(
    @SerializedName("token") val token: String
)

data class LinkChildResponse(
    @SerializedName("ok") val ok: Boolean,
    @SerializedName("child") val child: FamilyMemberDto? = null,
    @SerializedName("error") val error: String? = null
)

data class FamilyDashboardResponse(
    @SerializedName("ok") val ok: Boolean,
    @SerializedName("days") val days: Int = 30,
    @SerializedName("children") val children: List<ChildDashboardDto> = emptyList(),
    @SerializedName("error") val error: String? = null
)

data class ChildDashboardDto(
    @SerializedName("user_id") val userId: String,
    @SerializedName("display_name") val displayName: String,
    @SerializedName("parents") val parents: List<FamilyMemberDto> = emptyList(),
    @SerializedName("priority_lesson") val priorityLesson: String = "",
    @SerializedName("available_lessons") val availableLessons: List<ChildLessonDto> = emptyList(),
    @SerializedName("priority_history") val priorityHistory: List<ChildPriorityHistoryDto> = emptyList(),
    @SerializedName("summary") val summary: ChildLearningSummary = ChildLearningSummary(),
    @SerializedName("latest_progress") val latestProgress: ChildLatestProgress? = null,
    @SerializedName("daily") val daily: List<ChildDailyProgress> = emptyList()
)

data class ChildLessonDto(
    @SerializedName("lesson") val lesson: String,
    @SerializedName("lesson_title") val lessonTitle: String = "",
    @SerializedName("lesson_index") val lessonIndex: Int = 0,
    @SerializedName("words_count") val wordsCount: Int = 0
)

data class ChildPriorityHistoryDto(
    @SerializedName("lesson") val lesson: String,
    @SerializedName("parent_user_id") val parentUserId: String = "",
    @SerializedName("started_at") val startedAt: Long = 0,
    @SerializedName("ended_at") val endedAt: Long? = null,
    @SerializedName("duration_seconds") val durationSeconds: Int = 0,
    @SerializedName("is_active") val isActive: Boolean = false
)

data class SetPriorityLessonRequest(
    @SerializedName("lesson") val lesson: String
)

data class PriorityLessonResponse(
    @SerializedName("ok") val ok: Boolean = false,
    @SerializedName("child_user_id") val childUserId: String = "",
    @SerializedName("priority_lesson") val priorityLesson: String = "",
    @SerializedName("error") val error: String? = null
)

data class ChildLearningSummary(
    @SerializedName("words_count") val wordsCount: Int = 0,
    @SerializedName("lessons_count") val lessonsCount: Int = 0,
    @SerializedName("learning_days") val learningDays: Int = 0,
    @SerializedName("learning_streak_days") val learningStreakDays: Int = 0,
    @SerializedName("active_lessons") val activeLessons: Int = 0,
    @SerializedName("correct_answers") val correctAnswers: Int = 0,
    @SerializedName("incorrect_answers") val incorrectAnswers: Int = 0,
    @SerializedName("success_rate") val successRate: Int = 0,
    @SerializedName("last_activity_ts") val lastActivityTs: Long = 0,
    @SerializedName("studied_today") val studiedToday: Boolean = false,
    @SerializedName("today_words") val todayWords: Int = 0,
    @SerializedName("daily_goal") val dailyGoal: Int = 25,
    @SerializedName("today_goal_complete") val todayGoalComplete: Boolean = false,
    @SerializedName("today_status_milestone") val todayStatusMilestone: Int = 0,
    @SerializedName("today_learning_seconds") val todayLearningSeconds: Int = 0,
    @SerializedName("today_first_activity_ts") val todayFirstActivityTs: Long = 0,
    @SerializedName("today_last_activity_ts") val todayLastActivityTs: Long = 0
)

data class LearningStreakResponse(
    @SerializedName("ok") val ok: Boolean = false,
    @SerializedName("learning_streak_days") val learningStreakDays: Int = 0,
    @SerializedName("timezone_offset_minutes") val timezoneOffsetMinutes: Int = 0,
    @SerializedName("error") val error: String? = null
)

data class ChildLatestProgress(
    @SerializedName("lesson") val lesson: String = "",
    @SerializedName("passed") val passed: Int = 0,
    @SerializedName("total") val total: Int = 0,
    @SerializedName("event_ts") val eventTs: Long = 0
)

data class ChildDailyProgress(
    @SerializedName("date") val date: String,
    @SerializedName("correct") val correct: Int = 0,
    @SerializedName("incorrect") val incorrect: Int = 0,
    @SerializedName("events") val events: Int = 0
)

// ─── Lessons ─────────────────────────────────────────────────────────────────

data class LessonDto(
    @SerializedName("lesson") val lesson: String,
    @SerializedName("number") val number: String?,
    @SerializedName(value = "word_count", alternate = ["words_count"]) val wordCount: Int,
    @SerializedName("hidden") val hidden: Boolean = false,
    @SerializedName("is_priority") val isPriority: Boolean = false,
    @SerializedName("language_progress") val languageProgress: List<LessonLanguageProgressDto> = emptyList()
)

data class LessonLanguageProgressDto(
    @SerializedName("code") val code: String,
    @SerializedName("name") val name: String = "",
    @SerializedName("native") val nativeName: String = "",
    @SerializedName("learned_words") val learnedWords: Int = 0,
    @SerializedName("total_words") val totalWords: Int = 0,
    @SerializedName("percent") val percent: Int = 0
)

// Ответ /api/next_lesson и /api/prev_lesson: { ok, next } / { ok, prev }
data class LessonNavResponse(
    @SerializedName("ok") val ok: Boolean = false,
    @SerializedName("next") val next: String? = null,
    @SerializedName("prev") val prev: String? = null
)

// ─── Words ───────────────────────────────────────────────────────────────────

data class WordDto(
    @SerializedName("id") val id: Int,
    @SerializedName("lesson") val lesson: String?,
    @SerializedName("number") val number: String?,
    @SerializedName("nl") val nl: String?,
    @SerializedName("en") val en: String?,
    @SerializedName("ru") val ru: String?,
    @SerializedName("de") val de: String? = null,
    @SerializedName("fr") val fr: String? = null,
    @SerializedName("es") val es: String? = null,
    @SerializedName("it") val ita: String? = null,
    @SerializedName("pt") val pt: String? = null,
    @SerializedName("pl") val pl: String? = null,
    @SerializedName("uk") val uk: String? = null,
    @SerializedName("ex_nl") val exNl: String?,
    @SerializedName("ex_en") val exEn: String?,
    @SerializedName("ex_ru") val exRu: String?,
    @SerializedName("ex_de") val exDe: String? = null,
    @SerializedName("ex_fr") val exFr: String? = null,
    @SerializedName("ex_es") val exEs: String? = null,
    @SerializedName("ex_it") val exIt: String? = null,
    @SerializedName("ex_pt") val exPt: String? = null,
    @SerializedName("ex_pl") val exPl: String? = null,
    @SerializedName("ex_uk") val exUk: String? = null,
    @SerializedName("audio_nl") val audioNl: String?,
    @SerializedName("audio_en") val audioEn: String?,
    @SerializedName("audio_ru") val audioRu: String?,
    @SerializedName("audio_de") val audioDe: String? = null,
    @SerializedName("audio_fr") val audioFr: String? = null,
    @SerializedName("audio_es") val audioEs: String? = null,
    @SerializedName("audio_it") val audioIt: String? = null,
    @SerializedName("audio_pt") val audioPt: String? = null,
    @SerializedName("audio_pl") val audioPl: String? = null,
    @SerializedName("audio_uk") val audioUk: String? = null,
    @SerializedName("difficult") val difficult: Boolean = false,
    @SerializedName("status") val status: String?,
    @SerializedName("editable") val editable: Boolean = true,
    @SerializedName("practice_count") val practiceCount: Int = 0,
    @SerializedName("learned") val learned: Boolean = false
)

data class WordsResponse(
    @SerializedName("words") val words: List<WordDto>,
    @SerializedName("total") val total: Int?,
    @SerializedName("page") val page: Int?,
    @SerializedName("per_page") val perPage: Int?
)

data class DuplicatesResponse(
    @SerializedName("ok") val ok: Boolean? = null,
    @SerializedName("duplicates_count") val duplicatesCount: Int = 0,
    @SerializedName("groups_count") val groupsCount: Int = 0,
    @SerializedName("groups") val groups: List<DuplicateGroup> = emptyList()
)

data class DuplicateGroup(
    @SerializedName("key") val key: String,
    @SerializedName("count") val count: Int,
    @SerializedName("items") val items: List<WordDto> = emptyList()
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

data class DifficultWordsResponse(
    @SerializedName("ok") val ok: Boolean? = null,
    @SerializedName("items") val items: List<DifficultWordItem> = emptyList()
)

data class DifficultWordItem(
    @SerializedName("id") val id: Int,
    @SerializedName("kind") val kind: String? = null,
    @SerializedName("lesson") val lesson: String? = null,
    @SerializedName("number") val number: String? = null,
    @SerializedName(value = "nl_word", alternate = ["nl", "translation_nl"]) val nl: String? = null,
    @SerializedName(value = "en_word", alternate = ["en", "word_en"]) val en: String? = null,
    @SerializedName(value = "ru_word", alternate = ["ru", "translation_ru"]) val ru: String? = null,
    @SerializedName(value = "nl_sentence", alternate = ["ex_nl", "sentence_nl"]) val exNl: String? = null,
    @SerializedName(value = "en_sentence", alternate = ["ex_en", "sentence_en"]) val exEn: String? = null,
    @SerializedName(value = "ru_sentence", alternate = ["ex_ru", "sentence_ru"]) val exRu: String? = null,
    @SerializedName(value = "nl_audio", alternate = ["audio_nl"]) val audioNl: String? = null,
    @SerializedName(value = "en_audio", alternate = ["audio_en"]) val audioEn: String? = null,
    @SerializedName(value = "ru_audio", alternate = ["audio_ru"]) val audioRu: String? = null,
    @SerializedName("difficult") val difficult: Int? = null,
    @SerializedName("status") val status: String? = null
) {
    fun toWordDto(): WordDto = WordDto(
        id = id,
        lesson = lesson ?: kind,
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
        difficult = difficult != 0,
        status = status,
        editable = false
    )
}

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
    @SerializedName(value = "lang_code", alternate = ["code"]) val langCode: String,
    @SerializedName("name") val name: String?
)

data class SaveLanguagesRequest(
    @SerializedName("languages") val languages: List<String>
)

data class UiLanguageResponse(
    @SerializedName("ok") val ok: Boolean? = null,
    @SerializedName("ui_language") val uiLanguage: String,
    @SerializedName("detected_ui_language") val detectedUiLanguage: String?,
    @SerializedName("ui_language_override") val uiLanguageOverride: String?,
    @SerializedName("options") val options: List<LanguageOption> = emptyList()
)

data class SaveUiLanguageRequest(
    @SerializedName("ui_language") val uiLanguage: String?
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
    @SerializedName("nl") val nl: String? = null,
    @SerializedName("en") val en: String? = null,
    @SerializedName("ru") val ru: String? = null,
    @SerializedName("de") val de: String? = null,
    @SerializedName("fr") val fr: String? = null,
    @SerializedName("es") val es: String? = null,
    @SerializedName("it") val ita: String? = null,
    @SerializedName("pt") val pt: String? = null,
    @SerializedName("pl") val pl: String? = null,
    @SerializedName("uk") val uk: String? = null,
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
    @SerializedName("type") val eventType: String,
    @SerializedName("ts") val eventTs: Long,
    @SerializedName("state") val state: Map<String, Any?>?
)

data class SyncProgressRequest(
    @SerializedName("events") val events: List<ProgressEvent>
)

data class SyncProgressResponse(
    @SerializedName("ok") val ok: Boolean = false,
    @SerializedName("stored") val stored: Int = 0,
    @SerializedName("completed_lessons") val completedLessons: List<String> = emptyList(),
    @SerializedName("error") val error: String? = null
)

// ─── AI Platform (облачная генерация слов) ─────────────────────────────────

data class AiTranslateWordRequest(
    @SerializedName("word") val word: String,
    @SerializedName("from_lang") val fromLang: String,
    @SerializedName("level") val level: String,
    @SerializedName("known_ru") val knownRu: String? = null
)

data class AiTranslateWordResponse(
    @SerializedName("ok") val ok: Boolean,
    @SerializedName("error") val error: String?,
    @SerializedName("nl") val nl: String?,
    @SerializedName("en") val en: String?,
    @SerializedName("ru") val ru: String?,
    @SerializedName("ex_nl") val exNl: String?,
    @SerializedName("ex_en") val exEn: String?,
    @SerializedName("ex_ru") val exRu: String?
)

data class AiSuggestTopicWordsRequest(
    @SerializedName("topic") val topic: String,
    @SerializedName("lang") val lang: String,
    @SerializedName("level") val level: String,
    @SerializedName("count") val count: Int,
    @SerializedName("existing_words") val existingWords: List<String> = emptyList()
)

data class AiSuggestTopicWordsResponse(
    @SerializedName("ok") val ok: Boolean,
    @SerializedName("error") val error: String?,
    @SerializedName("words") val words: List<String>?
)

data class NlWordListResponse(
    @SerializedName("ok") val ok: Boolean,
    @SerializedName("error") val error: String?,
    @SerializedName("words") val words: List<String>?
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
    @SerializedName("trial_ends_at") val trialEndsAt: Long?,
    @SerializedName("account_type") val accountType: String = "standard",
    @SerializedName("family_relations") val familyRelations: List<AdminFamilyRelationDto> = emptyList(),
    @SerializedName("tts_successful_requests") val ttsSuccessfulRequests: Int = 0,
    @SerializedName("tts_failed_requests") val ttsFailedRequests: Int = 0,
    @SerializedName("tts_total_requests") val ttsTotalRequests: Int = 0,
    @SerializedName("tts_characters") val ttsCharacters: Int = 0,
    @SerializedName("tts_blocked_requests") val ttsBlockedRequests: Int = 0,
    @SerializedName("tts_character_limit") val ttsCharacterLimit: Int? = null,
    @SerializedName("tts_characters_remaining") val ttsCharactersRemaining: Int? = null,
    @SerializedName("translation_successful_requests") val translationSuccessfulRequests: Int = 0,
    @SerializedName("translation_failed_requests") val translationFailedRequests: Int = 0,
    @SerializedName("translation_prompt_tokens") val translationPromptTokens: Int = 0,
    @SerializedName("translation_completion_tokens") val translationCompletionTokens: Int = 0,
    @SerializedName("translation_total_tokens") val translationTotalTokens: Int = 0
)

data class AdminTtsUsageDto(
    @SerializedName("key") val periodKey: String = "",
    @SerializedName("timezone") val timezone: String = "Europe/Amsterdam",
    @SerializedName("next_reset_at") val nextResetAt: Long = 0,
    @SerializedName("successful_requests") val successfulRequests: Int = 0,
    @SerializedName("failed_requests") val failedRequests: Int = 0,
    @SerializedName("total_requests") val totalRequests: Int = 0,
    @SerializedName("characters") val characters: Int = 0,
    @SerializedName("blocked_requests") val blockedRequests: Int = 0,
    @SerializedName("character_limit") val characterLimit: Int = 500000,
    @SerializedName("characters_remaining") val charactersRemaining: Int = 500000,
    @SerializedName("limit_percent") val limitPercent: Double = 0.0
)

data class AdminTranslationUsageDto(
    @SerializedName("scope") val scope: String = "lifetime",
    @SerializedName("successful_requests") val successfulRequests: Int = 0,
    @SerializedName("failed_requests") val failedRequests: Int = 0,
    @SerializedName("prompt_tokens") val promptTokens: Int = 0,
    @SerializedName("completion_tokens") val completionTokens: Int = 0,
    @SerializedName("total_tokens") val totalTokens: Int = 0
)

data class AdminFamilyRelationDto(
    @SerializedName("direction") val direction: String,
    @SerializedName("parent_user_id") val parentUserId: String,
    @SerializedName("child_user_id") val childUserId: String,
    @SerializedName("display_name") val displayName: String
)

data class AdminUnlinkFamilyRequest(
    @SerializedName("parent_user_id") val parentUserId: String,
    @SerializedName("child_user_id") val childUserId: String
)

data class AdminUsersResponse(
    @SerializedName("ok") val ok: Boolean,
    @SerializedName("users") val users: List<AdminUserDto>,
    @SerializedName("tts_usage") val ttsUsage: AdminTtsUsageDto? = null,
    @SerializedName("translation_usage") val translationUsage: AdminTranslationUsageDto? = null
)

data class ResetTtsUsageRequest(
    @SerializedName("user_id") val userId: String? = null
)

data class GrantAccessRequest(
    @SerializedName("user_id") val userId: String
)
