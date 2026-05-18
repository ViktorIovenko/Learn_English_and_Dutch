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

    // ─── Lessons ──────────────────────────────────────────────────────────────

    @GET("api/lessons")
    suspend fun getLessons(): Response<List<LessonDto>>

    @GET("api/user_lessons")
    suspend fun getUserLessons(): Response<List<LessonDto>>

    @GET("api/lesson_words")
    suspend fun getLessonWords(@Query("lesson") lesson: String): Response<List<WordDto>>

    @GET("api/next_lesson")
    suspend fun getNextLesson(@Query("current") current: String): Response<LessonDto>

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
    suspend fun getNlWordList(): Response<List<String>>

    @GET("api/words/duplicates")
    suspend fun getDuplicates(): Response<List<WordDto>>

    // ─── Difficult ────────────────────────────────────────────────────────────

    @GET("api/difficult_words_user")
    suspend fun getDifficultWords(): Response<List<WordDto>>

    @POST("api/difficult/user_set")
    suspend fun setDifficult(@Body request: SetDifficultRequest): Response<GenericResponse>

    // ─── Languages ────────────────────────────────────────────────────────────

    @GET("api/language-options")
    suspend fun getLanguageOptions(): Response<List<LanguageOption>>

    @GET("api/user-languages")
    suspend fun getUserLanguages(): Response<List<UserLanguageDto>>

    @POST("api/user-languages")
    suspend fun saveUserLanguages(@Body request: SaveLanguagesRequest): Response<GenericResponse>

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
    suspend fun syncProgress(@Body request: SyncProgressRequest): Response<GenericResponse>

    @GET("api/sync/updates")
    suspend fun getSyncUpdates(@Query("since") since: Long): Response<GenericResponse>

    // ─── AI Generation ────────────────────────────────────────────────────────

    @POST("api/generate/topic")
    suspend fun generateByTopic(@Body request: GenerateByTopicRequest): Response<List<WordDto>>

    @POST("api/translate/word")
    suspend fun translateWord(@Body request: TranslateWordRequest): Response<WordDto>

    // ─── Admin ────────────────────────────────────────────────────────────────

    @GET("api/admin/users")
    suspend fun getAdminUsers(): Response<AdminUsersResponse>

    @POST("api/admin/grant_access")
    suspend fun grantAccess(@Body request: GrantAccessRequest): Response<GenericResponse>

    @POST("api/admin/revoke_access")
    suspend fun revokeAccess(@Body request: GrantAccessRequest): Response<GenericResponse>
}
