# Android API map

Подтверждённые факты извлечены из локального Retrofit-клиента. Base URL задаётся `BuildConfig.BASE_URL`/пользовательской настройкой; `ApiClient.kt` добавляет `X-User-Id`, `X-Client: android`, `X-Device-Language`. Клиент хранит offline-данные в Room и очередь progress sync в repository/database слоях.

## `POST /api/account/type` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `setAccountType`.
- Request DTO: `AccountTypeRequest`; response DTO: `GenericResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_account_type_save`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `POST /api/admin/grant_access` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `grantAccess`.
- Request DTO: `GrantAccessRequest`; response DTO: `GenericResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_admin_grant_access`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `POST /api/admin/revoke_access` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `revokeAccess`.
- Request DTO: `GrantAccessRequest`; response DTO: `GenericResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_admin_revoke_access`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `POST /api/admin/translation_usage/reset` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `resetTranslationUsage`.
- Request DTO: `ResetTtsUsageRequest`; response DTO: `GenericResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_admin_reset_translation_usage`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `POST /api/admin/tts_usage/reset` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `resetTtsUsage`.
- Request DTO: `ResetTtsUsageRequest`; response DTO: `GenericResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_admin_reset_tts_usage`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `POST /api/admin/unlink_family` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `adminUnlinkFamily`.
- Request DTO: `AdminUnlinkFamilyRequest`; response DTO: `GenericResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_admin_unlink_family`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `GET /api/admin/users` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `getAdminUsers`.
- Request DTO: `query/path/none`; response DTO: `AdminUsersResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_admin_users`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `POST /api/audio/ensure` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `ensureAudio`.
- Request DTO: `EnsureAudioRequest`; response DTO: `EnsureAudioResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_audio_ensure`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `GET /api/auth/google/config` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `getGoogleAuthConfig`.
- Request DTO: `query/path/none`; response DTO: `GoogleAuthConfigResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/google_auth.py` / `android_google_config`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `POST /api/auth/google/verify` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `verifyGoogleToken`.
- Request DTO: `GoogleVerifyRequest`; response DTO: `GoogleVerifyResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/google_auth.py` / `verify_android_token`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `POST /api/auth/login_android` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `loginAndroid`.
- Request DTO: `LoginRequest`; response DTO: `LoginResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `login_android`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `POST /api/auth/login_android_token` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `loginAndroidToken`.
- Request DTO: `LoginTokenRequest`; response DTO: `LoginResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `login_android_token`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `GET /api/child-learning/status` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `getChildLearningStatus`.
- Request DTO: `query/path/none`; response DTO: `ChildLearningStatusResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_child_learning_status`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `GET /api/daily-goal` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `getDailyGoal`.
- Request DTO: `query/path/none`; response DTO: `DailyGoalResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_daily_goal_get`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `POST /api/daily-goal` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `saveDailyGoal`.
- Request DTO: `SaveDailyGoalRequest`; response DTO: `DailyGoalResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_daily_goal_save`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `POST /api/difficult/user_set` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `setDifficult`.
- Request DTO: `SetDifficultRequest`; response DTO: `GenericResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_difficult_user_set`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `GET /api/difficult_words_user` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `getDifficultWords`.
- Request DTO: `query/path/none`; response DTO: `DifficultWordsResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_difficult_words_user`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `GET /api/family` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `getFamily`.
- Request DTO: `query/path/none`; response DTO: `FamilyStatusResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_family_status`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `DELETE /api/family/children/{childId}` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `unlinkChild`.
- Request DTO: `query/path/none`; response DTO: `GenericResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_family_unlink_child`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `PUT /api/family/children/{childId}/priority-lesson` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `setPriorityLesson`.
- Request DTO: `SetPriorityLessonRequest`; response DTO: `PriorityLessonResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_family_set_priority_lesson`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `GET /api/family/dashboard` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `getFamilyDashboard`.
- Request DTO: `query/path/none`; response DTO: `FamilyDashboardResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_family_dashboard`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `POST /api/family/link` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `linkChild`.
- Request DTO: `LinkChildRequest`; response DTO: `LinkChildResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_family_link`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `GET /api/family/pairing-code` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `getPairingCode`.
- Request DTO: `query/path/none`; response DTO: `PairingCodeResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_family_pairing_code`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `POST /api/generate/topic` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `aiSuggestTopicWords`.
- Request DTO: `AiSuggestTopicWordsRequest`; response DTO: `AiSuggestTopicWordsResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_generate_topic`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `POST /api/import-words` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `importWords`.
- Request DTO: `ImportWordsRequest`; response DTO: `ImportWordsResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_import_words`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `GET /api/language-options` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `getLanguageOptions`.
- Request DTO: `query/path/none`; response DTO: `List<LanguageOption>`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_language_options`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `GET /api/learning/streak` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `getLearningStreak`.
- Request DTO: `query/path/none`; response DTO: `LearningStreakResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_learning_streak`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `GET /api/lesson_words` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `getLessonWords`.
- Request DTO: `query/path/none`; response DTO: `List<WordDto>`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_lesson_words_by_title`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `GET /api/lessons` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `getLessons`.
- Request DTO: `query/path/none`; response DTO: `List<LessonDto>`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_lessons`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `POST /api/lessons/set_hidden` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `setLessonHidden`.
- Request DTO: `SetHiddenRequest`; response DTO: `GenericResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_lessons_set_hidden`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `GET /api/mcp/user` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `getMcpUser`.
- Request DTO: `query/path/none`; response DTO: `McpUserResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/mcp_api.py` / `mcp_user_status`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `POST /api/mcp/user` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `setMcpEnabled`.
- Request DTO: `McpEnabledRequest`; response DTO: `McpEnabledResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/mcp_api.py` / `mcp_user_toggle`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `GET /api/me` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `getMe`.
- Request DTO: `query/path/none`; response DTO: `UserInfo`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_me`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `GET /api/next_lesson` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `getNextLesson`.
- Request DTO: `query/path/none`; response DTO: `LessonNavResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_next_lesson`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `GET /api/prev_lesson` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `getPrevLesson`.
- Request DTO: `query/path/none`; response DTO: `LessonNavResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_prev_lesson`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `POST /api/progress/sync` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `syncProgress`.
- Request DTO: `SyncProgressRequest`; response DTO: `SyncProgressResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_progress_sync`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `POST /api/share/create` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `createShare`.
- Request DTO: `CreateShareRequest`; response DTO: `CreateShareResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_share_create`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `GET /api/share/source_lessons` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `getShareSourceLessons`.
- Request DTO: `query/path/none`; response DTO: `List<LessonDto>`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_share_source_lessons`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `POST /api/share/{token}/import` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `importShare`.
- Request DTO: `query/path/none`; response DTO: `ImportShareResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_share_import`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `GET /api/subscription` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `getSubscription`.
- Request DTO: `query/path/none`; response DTO: `SubscriptionResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_subscription_get`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `POST /api/subscription/verify_purchase` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `verifyPurchase`.
- Request DTO: `VerifyPurchaseRequest`; response DTO: `VerifyPurchaseResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_verify_purchase`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `GET /api/sync/updates` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `getSyncUpdates`.
- Request DTO: `query/path/none`; response DTO: `GenericResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_sync_updates`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `POST /api/translate/word` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `aiTranslateWord`.
- Request DTO: `AiTranslateWordRequest`; response DTO: `AiTranslateWordResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_translate_word`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `GET /api/ui-language` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `getUiLanguage`.
- Request DTO: `query/path/none`; response DTO: `UiLanguageResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_ui_language_get`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `POST /api/ui-language` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `saveUiLanguage`.
- Request DTO: `SaveUiLanguageRequest`; response DTO: `UiLanguageResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_ui_language_save`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `GET /api/user-languages` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `getUserLanguages`.
- Request DTO: `query/path/none`; response DTO: `List<UserLanguageDto>`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_user_languages_get`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `POST /api/user-languages` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `saveUserLanguages`.
- Request DTO: `SaveLanguagesRequest`; response DTO: `GenericResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_user_languages_save`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `GET /api/user_lessons` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `getUserLessons`.
- Request DTO: `query/path/none`; response DTO: `List<LessonDto>`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_user_lessons`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `POST /api/user_lessons/delete` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `deleteLessons`.
- Request DTO: `DeleteLessonsRequest`; response DTO: `GenericResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_user_lessons_delete`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `GET /api/words` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `getWords`.
- Request DTO: `query/path/none`; response DTO: `WordsResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_get_words`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `GET /api/words/duplicates` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `getDuplicates`.
- Request DTO: `query/path/none`; response DTO: `DuplicatesResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_words_duplicates`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `GET /api/words/nl-list` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `getNlWordList`.
- Request DTO: `query/path/none`; response DTO: `NlWordListResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_words_nl_list`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `DELETE /api/words/{id}` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `deleteWord`.
- Request DTO: `query/path/none`; response DTO: `GenericResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_delete_word`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `PUT /api/words/{id}` — confirmed

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `updateWord`.
- Request DTO: `UpdateWordRequest`; response DTO: `UpdateWordResponse`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `app/routes.py` / `api_update_word`.
- Примечание: Confirmed by matching local Flask method and normalized route.

## `GET /share/{token}/info` — unresolved

- Android: `android/app/src/main/java/com/learnwords/app/data/api/ApiService.kt` / `getShareInfo`.
- Request DTO: `query/path/none`; response DTO: `ShareSetDto`.
- Headers: `["X-User-Id", "X-Client", "X-Device-Language"]`.
- Backend: `not matched` / `not matched`.
- Примечание: No matching local Flask route found; compatibility review required.

## Offline/sync compatibility

`AppRepository.kt` сохраняет локальные данные через Room, ставит progress events в очередь и отправляет их в `/api/progress/sync`; `/api/sync/updates` используется для серверных delta-обновлений. Новые обязательные поля должны иметь совместимые defaults; URL, headers и DTO меняются одновременно на backend и Android.
