package com.learnwords.app.data.repository

import com.learnwords.app.data.ai.OllamaService
import com.learnwords.app.data.ai.OllamaStatus
import com.learnwords.app.data.api.*
import com.learnwords.app.data.db.*
import com.learnwords.app.utils.*
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first

class AppRepository(
    private val db: AppDatabase,
    private val apiClient: ApiClient,
    private val prefs: PreferencesManager
) {
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

    suspend fun getMe(): NetworkResult<UserInfo> {
        val result = safeApiCall { api.getMe() }
        if (result is NetworkResult.Success) {
            prefs.saveIsAdmin(result.data.isAdmin == true)
        }
        return result
    }

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
                    hidden = dto.hidden,
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

    suspend fun getWordsForLesson(lesson: String): List<WordDto> {
        // Try cache first
        val cached = db.wordDao().getWordsByLesson(lesson)
        if (cached.isNotEmpty()) return cached.map { it.toDto() }

        // Fetch from server
        val result = safeApiCall { api.getLessonWords(lesson) }
        if (result is NetworkResult.Success) {
            db.wordDao().insertWords(result.data.map { it.toEntity() })
            return result.data
        }
        return emptyList()
    }

    suspend fun refreshWordsForLesson(lesson: String): List<WordDto> {
        val result = safeApiCall { api.getLessonWords(lesson) }
        if (result is NetworkResult.Success) {
            db.wordDao().deleteByLesson(lesson)
            db.wordDao().insertWords(result.data.map { it.toEntity() })
            return result.data
        }
        return db.wordDao().getWordsByLesson(lesson).map { it.toDto() }
    }

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
        safeApiCall { api.importWords(ImportWordsRequest(lesson, words)) }

    // ─── Difficult words ─────────────────────────────────────────────────────

    fun getDifficultWordsFlow(): Flow<List<WordEntity>> = db.wordDao().getDifficultWords()

    suspend fun refreshDifficultWords(): NetworkResult<List<WordDto>> {
        val result = safeApiCall { api.getDifficultWords() }
        if (result is NetworkResult.Success) {
            result.data.forEach { dto ->
                db.wordDao().insertWord(dto.toEntity().copy(difficult = true))
            }
        }
        return result
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

    suspend fun getUserLanguages(): NetworkResult<List<UserLanguageDto>> =
        safeApiCall { api.getUserLanguages() }

    suspend fun saveUserLanguages(langCodes: List<String>): NetworkResult<GenericResponse> {
        val result = safeApiCall { api.saveUserLanguages(SaveLanguagesRequest(langCodes)) }
        if (result is NetworkResult.Success) {
            prefs.saveSelectedLangs(langCodes.joinToString(","))
        }
        return result
    }

    // ─── Subscription ────────────────────────────────────────────────────────

    suspend fun getSubscription(): NetworkResult<SubscriptionDto> =
        safeApiCall { api.getSubscription() }

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
    ): NetworkResult<EnsureAudioResponse> =
        safeApiCall { api.ensureAudio(EnsureAudioRequest(wordIds, langs)) }

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

    suspend fun syncPendingProgress(): NetworkResult<GenericResponse> {
        val pending = db.progressQueueDao().getPendingEvents()
        if (pending.isEmpty()) return NetworkResult.Success(GenericResponse(true, null, null))

        val events = pending.map { entity ->
            ProgressEvent(
                scope = entity.scope,
                eventType = entity.eventType,
                eventTs = entity.eventTs,
                payload = null
            )
        }
        val result = safeApiCall { api.syncProgress(SyncProgressRequest(events)) }
        if (result is NetworkResult.Success) {
            db.progressQueueDao().markSynced(pending.map { it.id })
            db.progressQueueDao().deleteSynced()
        }
        return result
    }

    // ─── AI generation (напрямую через Ollama) ───────────────────────────────
    // Ollama вызывается напрямую с Android, минуя Flask-сервер.
    // Flask-прокси эндпоинты /api/translate/word и /api/generate/topic
    // существуют как заглушки на случай проксирования через сервер.

    suspend fun generateByTopic(
        topic: String,
        level: String,
        count: Int,
        languages: List<String>
    ): NetworkResult<List<WordDto>> {
        val service = buildOllamaService()
        return service.generateByTopic(topic, level, count, languages)
    }

    suspend fun translateWord(
        word: String,
        fromLang: String,
        toLangs: List<String> = emptyList()
    ): NetworkResult<WordDto> {
        val service = buildOllamaService()
        return service.translateWord(word, fromLang)
    }

    suspend fun checkOllamaConnection(): OllamaStatus {
        return buildOllamaService().checkAvailability()
    }

    // ─── Admin ───────────────────────────────────────────────────────────────

    suspend fun getAdminUsers(): NetworkResult<AdminUsersResponse> =
        safeApiCall { api.getAdminUsers() }

    suspend fun grantAccess(userId: String): NetworkResult<GenericResponse> =
        safeApiCall { api.grantAccess(GrantAccessRequest(userId)) }

    suspend fun revokeAccess(userId: String): NetworkResult<GenericResponse> =
        safeApiCall { api.revokeAccess(GrantAccessRequest(userId)) }

    private suspend fun buildOllamaService(): OllamaService {
        val url = prefs.ollamaUrl.first()
        val model = prefs.ollamaModel.first()
        return OllamaService(url, model)
    }
}
