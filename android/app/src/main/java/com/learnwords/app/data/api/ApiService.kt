package com.learnwords.app.data.api

import retrofit2.Response
import retrofit2.http.*

interface ApiService {

    // ─── Auth ─────────────────────────────────────────────────────────────────

    @POST("api/auth/login_android")
    suspend fun loginAndroid(@Body request: LoginRequest): Response<LoginResponse>

    @POST("api/auth/login_android_token")
    suspend fun loginAndroidToken(@Body request: LoginTokenRequest): Response<LoginResponse>

    @GET("api/me")
    suspend fun getMe(): Response<UserInfo>

    @POST("api/account/type")
    suspend fun setAccountType(@Body request: AccountTypeRequest): Response<GenericResponse>

    @GET("api/family")
    suspend fun getFamily(): Response<FamilyStatusResponse>

    @GET("api/learning/streak")
    suspend fun getLearningStreak(
        @Query("tz_offset") timezoneOffsetMinutes: Int
    ): Response<LearningStreakResponse>

    @GET("api/child-learning/status")
    suspend fun getChildLearningStatus(
        @Query("tz_offset") timezoneOffsetMinutes: Int
    ): Response<ChildLearningStatusResponse>

    @GET("api/daily-goal")
    suspend fun getDailyGoal(): Response<DailyGoalResponse>

    @POST("api/daily-goal")
    suspend fun saveDailyGoal(@Body request: SaveDailyGoalRequest): Response<DailyGoalResponse>

    @GET("api/family/pairing-code")
    suspend fun getPairingCode(): Response<PairingCodeResponse>

    @POST("api/family/link")
    suspend fun linkChild(@Body request: LinkChildRequest): Response<LinkChildResponse>

    @GET("api/family/dashboard")
    suspend fun getFamilyDashboard(
        @Query("days") days: Int,
        @Query("tz_offset") timezoneOffsetMinutes: Int
    ): Response<FamilyDashboardResponse>

    @DELETE("api/family/children/{childId}")
    suspend fun unlinkChild(@Path("childId") childId: String): Response<GenericResponse>

    @PUT("api/family/children/{childId}/priority-lesson")
    suspend fun setPriorityLesson(
        @Path("childId") childId: String,
        @Body request: SetPriorityLessonRequest
    ): Response<PriorityLessonResponse>

    // ─── Lessons ──────────────────────────────────────────────────────────────

    @GET("api/lessons")
    suspend fun getLessons(): Response<List<LessonDto>>

    @GET("api/user_lessons")
    suspend fun getUserLessons(): Response<List<LessonDto>>

    @GET("api/lesson_words")
    suspend fun getLessonWords(@Query("lesson") lesson: String): Response<List<WordDto>>

    @GET("api/next_lesson")
    suspend fun getNextLesson(@Query("current") current: String): Response<LessonNavResponse>

    @GET("api/prev_lesson")
    suspend fun getPrevLesson(@Query("current") current: String): Response<LessonNavResponse>

    @POST("api/lessons/set_hidden")
    suspend fun setLessonHidden(@Body request: SetHiddenRequest): Response<GenericResponse>

    @POST("api/user_lessons/delete")
    suspend fun deleteLessons(@Body request: DeleteLessonsRequest): Response<GenericResponse>

    // ─── Words ────────────────────────────────────────────────────────────────

    @GET("api/words")
    suspend fun getWords(
        @Query("q") query: String? = null,
        @Query("page") page: Int = 1,
        @Query("per_page") perPage: Int = 50
    ): Response<WordsResponse>

    @PUT("api/words/{id}")
    suspend fun updateWord(@Path("id") id: Int, @Body request: UpdateWordRequest): Response<UpdateWordResponse>

    @DELETE("api/words/{id}")
    suspend fun deleteWord(@Path("id") id: Int): Response<GenericResponse>

    @POST("api/import-words")
    suspend fun importWords(@Body request: ImportWordsRequest): Response<ImportWordsResponse>

    @GET("api/words/nl-list")
    suspend fun getNlWordList(): Response<NlWordListResponse>

    @GET("api/words/duplicates")
    suspend fun getDuplicates(): Response<DuplicatesResponse>

    // ─── Difficult ────────────────────────────────────────────────────────────

    @GET("api/difficult_words_user")
    suspend fun getDifficultWords(): Response<DifficultWordsResponse>

    @POST("api/difficult/user_set")
    suspend fun setDifficult(@Body request: SetDifficultRequest): Response<GenericResponse>

    // ─── Languages ────────────────────────────────────────────────────────────

    @GET("api/language-options")
    suspend fun getLanguageOptions(): Response<List<LanguageOption>>

    @GET("api/user-languages")
    suspend fun getUserLanguages(): Response<List<UserLanguageDto>>

    @POST("api/user-languages")
    suspend fun saveUserLanguages(@Body request: SaveLanguagesRequest): Response<GenericResponse>

    @GET("api/ui-language")
    suspend fun getUiLanguage(): Response<UiLanguageResponse>

    @POST("api/ui-language")
    suspend fun saveUiLanguage(@Body request: SaveUiLanguageRequest): Response<UiLanguageResponse>

    // ─── Subscription ─────────────────────────────────────────────────────────

    @GET("api/subscription")
    suspend fun getSubscription(): Response<SubscriptionDto>

    /**
     * Отправляет purchase_token от Google Play на сервер для верификации
     * и активации подписки. Бэкенд должен проверить токен через
     * Google Play Developer API.
     *
     * ⚠️ ЗАГЛУШКА на стороне сервера — см. routes.py
     */
    @POST("api/subscription/verify_purchase")
    suspend fun verifyPurchase(@Body request: VerifyPurchaseRequest): Response<VerifyPurchaseResponse>

    // ─── Audio ────────────────────────────────────────────────────────────────

    @POST("api/audio/ensure")
    suspend fun ensureAudio(@Body request: EnsureAudioRequest): Response<EnsureAudioResponse>

    // ─── Sharing ──────────────────────────────────────────────────────────────

    @GET("share/{token}/info")
    suspend fun getShareInfo(@Path("token") token: String): Response<ShareSetDto>

    @POST("api/share/create")
    suspend fun createShare(@Body request: CreateShareRequest): Response<CreateShareResponse>

    @GET("api/share/source_lessons")
    suspend fun getShareSourceLessons(): Response<List<LessonDto>>

    @POST("api/share/{token}/import")
    suspend fun importShare(@Path("token") token: String): Response<ImportShareResponse>

    // ─── Progress sync ────────────────────────────────────────────────────────

    @POST("api/progress/sync")
    suspend fun syncProgress(@Body request: SyncProgressRequest): Response<SyncProgressResponse>

    @GET("api/sync/updates")
    suspend fun getSyncUpdates(@Query("since") since: Long): Response<GenericResponse>

    // ─── AI Generation (облако — AI Platform) ──────────────────────────────────

    @POST("api/generate/topic")
    suspend fun aiSuggestTopicWords(@Body request: AiSuggestTopicWordsRequest): Response<AiSuggestTopicWordsResponse>

    @POST("api/translate/word")
    suspend fun aiTranslateWord(@Body request: AiTranslateWordRequest): Response<AiTranslateWordResponse>

    // ─── Admin ────────────────────────────────────────────────────────────────

    @GET("api/admin/users")
    suspend fun getAdminUsers(): Response<AdminUsersResponse>

    @POST("api/admin/grant_access")
    suspend fun grantAccess(@Body request: GrantAccessRequest): Response<GenericResponse>

    @POST("api/admin/revoke_access")
    suspend fun revokeAccess(@Body request: GrantAccessRequest): Response<GenericResponse>

    @POST("api/admin/unlink_family")
    suspend fun adminUnlinkFamily(@Body request: AdminUnlinkFamilyRequest): Response<GenericResponse>

    @POST("api/admin/tts_usage/reset")
    suspend fun resetTtsUsage(@Body request: ResetTtsUsageRequest): Response<GenericResponse>

    @POST("api/admin/translation_usage/reset")
    suspend fun resetTranslationUsage(@Body request: ResetTtsUsageRequest): Response<GenericResponse>
}
