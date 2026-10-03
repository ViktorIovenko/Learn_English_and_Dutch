package com.learnwords.app.data.repository

import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import com.learnwords.app.data.api.*
import com.learnwords.app.data.db.*
import com.learnwords.app.utils.*
import kotlinx.coroutines.flow.Flow

class AppRepository(
    private val db: AppDatabase,
    private val apiClient: ApiClient,
    private val prefs: PreferencesManager,
    private val contentCache: WordContentCache
) {
    private val gson = Gson()
    private val api: ApiService
        get() = apiClient.service

    // ─── Auth ────────────────────────────────────────────────────────────────

    suspend fun login(userId: String, password: String, serverUrl: String): NetworkResult<LoginResponse> {
        prefs.saveServerUrl(serverUrl)
        return safeApiCall { api.loginAndroid(LoginRequest(userId, password)) }
    }

    suspend fun loginWithTelegramToken(serverUrl: String, token: String): NetworkResult<LoginResponse> {
        prefs.saveServerUrl(serverUrl)
        return safeApiCall { api.loginAndroidToken(LoginTokenRequest(token)) }
    }

    suspend fun getGoogleAuthConfig(serverUrl: String): NetworkResult<GoogleAuthConfigResponse> {
        prefs.saveServerUrl(serverUrl)
        return safeApiCall { api.getGoogleAuthConfig() }
    }

    suspend fun loginWithGoogleToken(serverUrl: String, idToken: String): NetworkResult<GoogleVerifyResponse> {
        prefs.saveServerUrl(serverUrl)
        return safeApiCall { api.verifyGoogleToken(GoogleVerifyRequest(idToken)) }
    }

    suspend fun getMe(): NetworkResult<UserInfo> {
        val result = safeApiCall { api.getMe() }
        if (result is NetworkResult.Success) {
            prefs.saveIsAdmin(result.data.isAdmin == true)
        }
        return result
    }

    suspend fun setAccountType(accountType: String): NetworkResult<GenericResponse> =
        safeApiCall { api.setAccountType(AccountTypeRequest(accountType)) }

    suspend fun getFamily(): NetworkResult<FamilyStatusResponse> =
        safeApiCall { api.getFamily() }

    suspend fun getLearningStreak(timezoneOffsetMinutes: Int): NetworkResult<LearningStreakResponse> =
        safeApiCall { api.getLearningStreak(timezoneOffsetMinutes) }

    suspend fun getChildLearningStatus(timezoneOffsetMinutes: Int): NetworkResult<ChildLearningStatusResponse> =
        safeApiCall { api.getChildLearningStatus(timezoneOffsetMinutes) }

    suspend fun getDailyGoal(): NetworkResult<DailyGoalResponse> = safeApiCall { api.getDailyGoal() }

    suspend fun saveDailyGoal(value: Int): NetworkResult<DailyGoalResponse> =
        safeApiCall { api.saveDailyGoal(SaveDailyGoalRequest(value)) }

    suspend fun getMcpUser(): NetworkResult<McpUserResponse> = safeApiCall { api.getMcpUser() }

    suspend fun setMcpEnabled(enabled: Boolean): NetworkResult<McpEnabledResponse> =
        safeApiCall { api.setMcpEnabled(McpEnabledRequest(enabled)) }

    suspend fun getPairingCode(): NetworkResult<PairingCodeResponse> =
        safeApiCall { api.getPairingCode() }

    suspend fun linkChild(token: String): NetworkResult<LinkChildResponse> =
        safeApiCall { api.linkChild(LinkChildRequest(token)) }

    suspend fun getFamilyDashboard(days: Int, timezoneOffsetMinutes: Int): NetworkResult<FamilyDashboardResponse> =
        safeApiCall { api.getFamilyDashboard(days, timezoneOffsetMinutes) }

    suspend fun unlinkChild(childId: String): NetworkResult<GenericResponse> =
        safeApiCall { api.unlinkChild(childId) }

    suspend fun setPriorityLesson(childId: String, lesson: String): NetworkResult<PriorityLessonResponse> =
        safeApiCall { api.setPriorityLesson(childId, SetPriorityLessonRequest(lesson)) }

    // ─── Lessons ─────────────────────────────────────────────────────────────

    fun getLessonsFlow(): Flow<List<LessonCacheEntity>> = db.lessonDao().getLessons()

    suspend fun refreshLessons(): NetworkResult<List<LessonDto>> {
        val result = safeApiCall { api.getLessons() }
        if (result is NetworkResult.Success) {
            val existing = db.lessonDao().getLessonsOnce().associateBy { it.lesson }
            val entities = result.data.map { dto ->
                LessonCacheEntity(
                    lesson = dto.lesson,
                    number = dto.number,
                    wordCount = dto.wordCount,
                    uploadOrder = dto.uploadOrder,
                    hidden = dto.hidden,
                    isPriority = dto.isPriority,
                    languageProgressJson = gson.toJson(dto.languageProgress),
                    lastOpenedAt = existing[dto.lesson]?.lastOpenedAt ?: 0L
                )
            }
            db.lessonDao().clearAll()
            db.lessonDao().insertLessons(entities)
        }
        return result
    }

    suspend fun setLessonHidden(lesson: String, hidden: Boolean): NetworkResult<GenericResponse> {
        val result = safeApiCall { api.setLessonHidden(SetHiddenRequest(lesson, hidden)) }
        if (result is NetworkResult.Success) {
            db.lessonDao().setHidden(lesson, hidden)
        }
        return result
    }

    suspend fun markLessonOpened(lesson: String) {
        db.lessonDao().setLastOpenedAt(lesson, System.currentTimeMillis())
    }

    /** Название следующего видимого урока относительно текущего (или null). */
    suspend fun getNextLessonTitle(current: String): String? {
        val result = safeApiCall { api.getNextLesson(current) }
        return (result as? NetworkResult.Success)?.data
            ?.takeIf { it.ok }?.next?.takeIf { it.isNotBlank() }
    }

    /** Название предыдущего видимого урока относительно текущего (или null). */
    suspend fun getPrevLessonTitle(current: String): String? {
        val result = safeApiCall { api.getPrevLesson(current) }
        return (result as? NetworkResult.Success)?.data
            ?.takeIf { it.ok }?.prev?.takeIf { it.isNotBlank() }
    }

    suspend fun deleteLessons(lessons: List<String>): NetworkResult<GenericResponse> {
        val result = safeApiCall { api.deleteLessons(DeleteLessonsRequest(lessons)) }
        if (result is NetworkResult.Success) {
            lessons.forEach { lesson ->
                db.lessonDao().deleteLesson(lesson)
                db.wordDao().deleteByLesson(lesson)
            }
        }
        return result
    }

    // ─── Words ───────────────────────────────────────────────────────────────

    suspend fun refreshWordsForLesson(lesson: String): List<WordDto> {
        val result = safeApiCall { api.getLessonWords(lesson) }
        if (result is NetworkResult.Success) {
            db.wordDao().deleteByLesson(lesson)
            db.wordDao().insertWords(result.data.map { it.toEntity() })
            return result.data
        }
        return db.wordDao().getWordsByLesson(lesson).map { it.toDto() }
    }

    suspend fun getCachedWordsForLesson(lesson: String): List<WordDto> =
        db.wordDao().getWordsByLesson(lesson).map { it.toDto() }

    suspend fun getWords(query: String?, page: Int, perPage: Int): NetworkResult<WordsResponse> =
        safeApiCall { api.getWords(query, page, perPage) }

    suspend fun updateWord(id: Int, request: UpdateWordRequest): NetworkResult<WordDto> {
        val result = safeApiCall { api.updateWord(id, request) }
        if (result is NetworkResult.Success) {
            val word = result.data.word
                ?: return NetworkResult.Error(result.data.error ?: "Empty word response")
            db.wordDao().insertWord(word.toEntity())
            return NetworkResult.Success(word)
        }
        return when (result) {
            is NetworkResult.Error -> result
            is NetworkResult.Loading -> result
            is NetworkResult.Success -> NetworkResult.Error("Unexpected update response")
        }
    }

    suspend fun deleteWord(id: Int): NetworkResult<GenericResponse> {
        val result = safeApiCall { api.deleteWord(id) }
        if (result is NetworkResult.Success) {
            db.wordDao().deleteById(id)
        }
        return result
    }

    suspend fun importWords(lesson: String, words: List<Map<String, String?>>): NetworkResult<ImportWordsResponse> =
        safeApiCall { api.importWords(ImportWordsRequest(listOf(ImportLessonRequest(lesson, words)), java.util.UUID.randomUUID().toString())) }

    suspend fun getDuplicates(): NetworkResult<List<WordDto>> {
        return when (val result = safeApiCall { api.getDuplicates() }) {
            is NetworkResult.Success -> {
                NetworkResult.Success(result.data.groups.flatMap { it.items })
            }
            is NetworkResult.Error -> result
            is NetworkResult.Loading -> result
        }
    }

    // ─── Difficult words ─────────────────────────────────────────────────────

    fun getDifficultWordsFlow(): Flow<List<WordEntity>> = db.wordDao().getDifficultWords()

    suspend fun getDifficultWordsOnce(): List<WordDto> =
        db.wordDao().getDifficultWordsOnce().map { it.toDto() }

    suspend fun refreshDifficultWords(): NetworkResult<List<WordDto>> {
        val result = safeApiCall { api.getDifficultWords() }
        if (result is NetworkResult.Success) {
            val words = result.data.items.map { it.toWordDto() }
            words.forEach { dto ->
                db.wordDao().insertWord(dto.toEntity().copy(difficult = true))
            }
            return NetworkResult.Success(words)
        }
        return when (result) {
            is NetworkResult.Error -> result
            is NetworkResult.Loading -> result
            is NetworkResult.Success -> NetworkResult.Success(emptyList())
        }
    }

    suspend fun setDifficult(wordId: Int, difficult: Boolean): NetworkResult<GenericResponse> {
        val result = safeApiCall { api.setDifficult(SetDifficultRequest(wordId, difficult)) }
        if (result is NetworkResult.Success) {
            db.wordDao().setDifficult(wordId, difficult)
        }
        return result
    }

    // ─── Languages ───────────────────────────────────────────────────────────

    suspend fun getLanguageOptions(): NetworkResult<List<LanguageOption>> =
        safeApiCall { api.getLanguageOptions() }

    suspend fun getUserLanguages(): NetworkResult<List<UserLanguageDto>> {
        val result = safeApiCall { api.getUserLanguages() }
        if (result is NetworkResult.Success) {
            val codes = result.data.sortedBy { it.priority }.map { it.langCode }
            if (codes.isNotEmpty()) prefs.saveSelectedLangs(codes.joinToString(","))
        }
        return result
    }

    suspend fun saveUserLanguages(langCodes: List<String>): NetworkResult<GenericResponse> {
        val result = safeApiCall { api.saveUserLanguages(SaveLanguagesRequest(langCodes)) }
        if (result is NetworkResult.Success) {
            prefs.saveSelectedLangs(langCodes.joinToString(","))
        }
        return result
    }

    // ─── Subscription ────────────────────────────────────────────────────────

    suspend fun getSubscription(): NetworkResult<SubscriptionDto> =
        when (val result = safeApiCall { api.getSubscription() }) {
            is NetworkResult.Success -> result.data.subscription?.let { NetworkResult.Success(it) }
                ?: NetworkResult.Error("Subscription missing in response")
            is NetworkResult.Error -> result
            is NetworkResult.Loading -> result
        }

    suspend fun verifyPurchase(
        purchaseToken: String,
        productId: String,
        packageName: String
    ): NetworkResult<VerifyPurchaseResponse> =
        safeApiCall { api.verifyPurchase(VerifyPurchaseRequest(purchaseToken, productId, packageName)) }

    // ─── Audio ───────────────────────────────────────────────────────────────

    suspend fun ensureAudio(
        wordIds: List<Int>,
        langs: List<String> = listOf("nl", "en", "ru")
    ): NetworkResult<EnsureAudioResponse> {
        val result = safeApiCall { api.ensureAudio(EnsureAudioRequest(wordIds, langs)) }
        if (result is NetworkResult.Success) {
            result.data.items.forEach { item ->
                db.wordDao().updateAudioUrls(
                    item.id, item.nl, item.en, item.ru, item.de, item.fr,
                    item.es, item.ita, item.pt, item.pl, item.uk
                )
            }
        }
        return result
    }

    // ─── Sharing ─────────────────────────────────────────────────────────────

    suspend fun getShareInfo(token: String): NetworkResult<ShareSetDto> =
        safeApiCall { api.getShareInfo(token) }

    suspend fun createShare(
        lessons: List<String>,
        title: String?,
        expiresHours: Int?
    ): NetworkResult<CreateShareResponse> =
        safeApiCall { api.createShare(CreateShareRequest(lessons, title, expiresHours)) }

    suspend fun getShareSourceLessons(): NetworkResult<List<LessonDto>> =
        safeApiCall { api.getShareSourceLessons() }

    suspend fun importShare(token: String): NetworkResult<ImportShareResponse> =
        safeApiCall { api.importShare(token) }

    // ─── Interface language ────────────────────────────────────────────────

    suspend fun getUiLanguage(): NetworkResult<UiLanguageResponse> {
        return safeApiCall { api.getUiLanguage() }
    }

    suspend fun saveUiLanguage(languageCode: String?): NetworkResult<UiLanguageResponse> {
        return safeApiCall { api.saveUiLanguage(SaveUiLanguageRequest(languageCode)) }
    }

    // ─── Progress sync ───────────────────────────────────────────────────────

    suspend fun queueProgress(scope: String, eventType: String, payloadJson: String?) {
        db.progressQueueDao().insertEvent(
            ProgressQueueEntity(
                scope = scope,
                eventType = eventType,
                eventTs = System.currentTimeMillis(),
                payload = payloadJson
            )
        )
    }

    suspend fun syncPendingProgress(): NetworkResult<SyncProgressResponse> {
        val pending = db.progressQueueDao().getPendingEvents()
        if (pending.isEmpty()) return NetworkResult.Success(SyncProgressResponse(ok = true))

        val events = pending.map { entity ->
            val state = entity.payload?.let { json ->
                runCatching {
                    gson.fromJson<Map<String, Any?>>(
                        json,
                        object : TypeToken<Map<String, Any?>>() {}.type
                    )
                }.getOrNull()
            }
            ProgressEvent(
                scope = entity.scope,
                eventType = entity.eventType,
                eventTs = entity.eventTs,
                state = state
            )
        }
        val result = safeApiCall { api.syncProgress(SyncProgressRequest(events)) }
        if (result is NetworkResult.Success) {
            db.progressQueueDao().markSynced(pending.map { it.id })
            db.progressQueueDao().deleteSynced()
            refreshLessons()
        }
        return result
    }

    // ─── AI generation (облако — AI Platform) ────────────────────────────────
    // Запросы идут через Flask-прокси /api/translate/word и /api/generate/topic,
    // который обращается к AI Platform; ключи остаются на сервере.

    suspend fun generateByTopic(
        topic: String,
        level: String,
        count: Int
    ): NetworkResult<List<WordDto>> = cloudGenerateByTopic(topic, level, count)

    suspend fun translateWord(
        word: String,
        fromLang: String
    ): NetworkResult<WordDto> = cloudTranslateWord(word, fromLang, "A2")

    private suspend fun cloudTranslateWord(
        word: String,
        fromLang: String,
        level: String,
        knownRu: String? = null
    ): NetworkResult<WordDto> {
        val cacheKey = listOf(fromLang.lowercase(), level, knownRu.orEmpty(), word.trim().lowercase())
            .joinToString("|")
        contentCache.getJson(cacheKey, AiTranslateWordResponse::class.java)
            ?.takeIf { it.ok }
            ?.let { return NetworkResult.Success(it.toGeneratedWord()) }

        return when (val result = safeApiCall {
            api.aiTranslateWord(AiTranslateWordRequest(word, fromLang, level, knownRu))
        }) {
            is NetworkResult.Success -> {
                val body = result.data
                if (body.ok) {
                    contentCache.putJson(cacheKey, body)
                    NetworkResult.Success(body.toGeneratedWord())
                } else {
                    NetworkResult.Error(body.error ?: "Cloud generation failed")
                }
            }
            is NetworkResult.Error -> NetworkResult.Error(extractCloudErrorMessage(result.message), result.code)
            else -> NetworkResult.Error("Unknown error")
        }
    }

    private fun AiTranslateWordResponse.toGeneratedWord(): WordDto = WordDto(
        id = 0, lesson = null, number = null,
        nl = nl, en = en, ru = ru,
        exNl = exNl, exEn = exEn, exRu = exRu,
        audioNl = null, audioEn = null, audioRu = null,
        difficult = false, status = null
    )

    // Дедупликация против уже сохранённых NL-слов — как в веб-версии (upload.js:
    // _fetchExistingNlWords + _deduplicateWords), чтобы не предлагать слова, которые
    // уже есть в словаре пользователя.
    private suspend fun fetchExistingNlWords(): List<String> {
        return when (val result = safeApiCall { api.getNlWordList() }) {
            is NetworkResult.Success -> if (result.data.ok) result.data.words.orEmpty() else emptyList()
            else -> emptyList()
        }
    }

    private fun stripDutchArticle(word: String): String =
        word.lowercase().trim().replace(Regex("^(de|het|een)\\s+"), "").trim()

    private suspend fun cloudGenerateByTopic(
        topic: String,
        level: String,
        count: Int
    ): NetworkResult<List<WordDto>> {
        val existingWords = fetchExistingNlWords()
        val existingSet = existingWords.map { it.lowercase().trim() }.toSet()
        val existingBase = existingWords.map { stripDutchArticle(it) }.toSet()

        val suggested = when (val result = safeApiCall {
            api.aiSuggestTopicWords(AiSuggestTopicWordsRequest(topic, "nl", level, count, existingWords))
        }) {
            is NetworkResult.Success -> {
                if (!result.data.ok) {
                    return NetworkResult.Error(result.data.error ?: "Cloud generation failed")
                }
                result.data.words.orEmpty()
            }
            is NetworkResult.Error -> return NetworkResult.Error(extractCloudErrorMessage(result.message), result.code)
            else -> return NetworkResult.Error("Unknown error")
        }

        val newWords = suggested.filter { word ->
            word.lowercase().trim() !in existingSet && stripDutchArticle(word) !in existingBase
        }
        if (newWords.isEmpty()) return NetworkResult.Success(emptyList())

        val words = mutableListOf<WordDto>()
        for (word in newWords) {
            when (val translated = cloudTranslateWord(word, "nl", level)) {
                is NetworkResult.Success -> words.add(translated.data)
                is NetworkResult.Error -> {} // skip words that failed, keep the rest
                else -> {}
            }
        }
        return NetworkResult.Success(words)
    }

    // Flask возвращает ошибки AI Platform с HTTP-кодом (400/401/502) и телом
    // {"ok": false, "error": "..."}; safeApiCall в этом случае кладёт весь текст
    // тела в message. Пытаемся достать читаемое поле "error", как это делает веб.
    private fun extractCloudErrorMessage(raw: String): String {
        return try {
            gson.fromJson(raw, com.google.gson.JsonObject::class.java)
                ?.get("error")?.takeIf { it.isJsonPrimitive }?.asString ?: raw
        } catch (e: Exception) {
            raw
        }
    }

    // ─── Admin ───────────────────────────────────────────────────────────────

    suspend fun getAdminUsers(): NetworkResult<AdminUsersResponse> =
        safeApiCall { api.getAdminUsers() }

    suspend fun grantAccess(userId: String): NetworkResult<GenericResponse> =
        safeApiCall { api.grantAccess(GrantAccessRequest(userId)) }

    suspend fun revokeAccess(userId: String): NetworkResult<GenericResponse> =
        safeApiCall { api.revokeAccess(GrantAccessRequest(userId)) }

    suspend fun adminUnlinkFamily(parentUserId: String, childUserId: String): NetworkResult<GenericResponse> =
        safeApiCall { api.adminUnlinkFamily(AdminUnlinkFamilyRequest(parentUserId, childUserId)) }

    suspend fun resetTtsUsage(userId: String? = null): NetworkResult<GenericResponse> =
        safeApiCall { api.resetTtsUsage(ResetTtsUsageRequest(userId)) }

    suspend fun resetTranslationUsage(userId: String? = null): NetworkResult<GenericResponse> =
        safeApiCall { api.resetTranslationUsage(ResetTtsUsageRequest(userId)) }
}
