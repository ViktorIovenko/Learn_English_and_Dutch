# ParallelLingvo MCP connector

Production URL: `https://learn.iovenko.eu/mcp`

The connector is an isolated Streamable HTTP MCP resource server. It has no database, audio, Telegram persistence, Docker socket, Google credentials, Telegram token, or AI Platform credentials. Every tool call goes through the fixed internal endpoint in the main ParallelLingvo (`learn-words`) service.

## Identity and authorization

The connector uses OAuth 2.1 Authorization Code with PKCE S256 and dynamic client registration.

- OAuth issuer: `https://learn.iovenko.eu`
- authorization metadata: `/.well-known/oauth-authorization-server`
- protected-resource metadata: `/.well-known/oauth-protected-resource/mcp`
- register: `/oauth/register`
- authorize/consent: `/oauth/authorize`
- token: `/oauth/token`
- revoke: `/oauth/revoke`

Access tokens are opaque random values. Only their SHA-256 hashes are stored. Authorization codes are short-lived, single-use and bound to client, redirect URI, resource and PKCE challenge. The gateway sends the token to the internal API for server-side grant resolution; `user_id` is never accepted from a tool argument.

## Scopes

- `learning.read`: profile, entitlement, languages, settings, lessons, words, progress, recommendations.
- `learning.write`: settings, languages, lessons, words, progress, application translation/TTS operations.
- `family.read`: linked children and their progress/lessons.
- `family.write`: assignments, archive, priority lesson and difficult words for a linked child.
- `learning.files`: reserved permission for ChatGPT file import; write still also requires `learning.write`.
- `subscriptions.admin`: subscription inventory and manual grant/revoke. It is shown/granted only to a configured `ADMIN_IDS` user and is checked again on every operation.

Default consent is `learning.read`. Additional scopes must be requested and selected explicitly.

The operator page is `/admin/mcp`. It is restricted to an authenticated configured administrator and shows component health, scopes, clients and grants without tokens, bounded seven-day usage, revocation controls, and build labels.

## Tools

System: `system_info`, `system_health`, `system_capabilities`, `permissions_get`.

Account: `me_get`, `subscription_get`, `my_languages_get`, `my_languages_update`, `my_learning_settings_get`, `my_learning_settings_update`.

Learning read: `lessons_list`, `lesson_get`, `lesson_words_list`, `difficult_words_list`, `words_search`, `word_get`, `next_lesson_get`, `previous_lesson_get`, `progress_summary`, `progress_words_get`, `learning_recommendation_get`.

Learning write: `lesson_create`, `lesson_rename`, `lesson_set_hidden`, `lesson_delete`, `words_add`, `word_update`, `word_delete`, `words_mark_difficult`, `progress_record`, `progress_record_many`.

Difficult words (personal per user, word stays in its lesson): `difficult_words_list`, `difficult_words_add`, `difficult_words_remove`, `difficult_words_candidates_get` (read-only error statistics from `progress_events`; feed `suggested_word_ids` into `difficult_words_add(source="auto_errors")`). For a linked child: `family_child_difficult_words_list`, `family_child_difficult_words_add`, `family_child_difficult_words_remove`, `family_child_difficult_words_candidates_get`. Flags live in `user_word_flags` with `source` (`manual` / `parent` / `auto_errors`) and `updated_at`.

Lesson completeness (always for ONE user): `validate_lesson_for_user(lesson_title, child_user_id?)` returns `COMPLETE`/`INCOMPLETE`, the user checked, `required_languages` (that user's live languages), `required_example_languages`, `word_count`, `complete_word_count`, `missing_languages`, `missing_fields[]` (`word_id`, `field`, `kind`, `reason`) and `problem_words[]` (missing/corrupted). Requirements are read from `user_language_preferences` of that user only — nothing is hardcoded.

Complete scenarios:

- `lesson_create_complete(title, words, idempotency_key, use_cloud=true, save_incomplete=false)` — create for the authenticated user only: their languages → words → optional cloud top-up of missing translations/examples → validation. `INCOMPLETE` rolls the lesson back and returns `LESSON_INCOMPLETE` with the validation payload (unless `save_incomplete`). Nobody is assigned.
- `lesson_assign_complete(child_user_id, lesson_title, idempotency_key, set_priority=false, word_fills=[], use_cloud=true)` — assign an existing canonical lesson to one linked child: that child's languages only → fill only what is missing (`word_fills` first, only into empty fields; then cloud, bounded to 12 provider calls per call, `fill.cloud.truncated=true` means re-run) → validation for the child → assignment → optional priority → last-5 rule. Incomplete lessons are never assigned (`LESSON_INCOMPLETE`).

Application providers: `ai_status`, `translate_word`, `generate_topic_words`, `translate_language`, `audio_ensure`.

Family: `family_status_get`, `family_children_list`, `family_child_languages_get/update`, `family_child_progress_get`, `family_child_lessons_list(status=active|archived|all)`, `family_child_lesson_words_list`, `family_child_lesson_assign`, `family_children_lesson_assign`, `family_child_lesson_unassign`, `family_child_priority_lesson_set/clear`.

Child lesson archive (per child, per parent): a child keeps at most 5 active assigned lessons (`MAX_ACTIVE_CHILD_LESSONS`). Every assignment/restore runs the cleanup: the newest 5 by `activated_at` stay, the rest get `archived_at` on `family_lesson_assignments`. The priority lesson is pinned (always kept, counts toward the 5); a manual archive of the priority lesson clears the priority first, and setting priority on an archived lesson restores it. Archiving never deletes words, progress or difficult flags; archived lessons stay readable through `family_child_lesson_words_list` / `word_get` and disappear only from the child's active list (`get_visible_lessons_for_user`). Tools: `family_child_active_lessons_list`, `family_child_archived_lessons_list`, `family_child_lesson_archive`, `family_child_lesson_restore`, `family_child_lessons_cleanup(keep<=5)`.

Files: `lesson_import_file`. ChatGPT supplies `{download_url,file_id,mime_type?,file_name?}` through `_meta["openai/fileParams"]`. Only public HTTPS URLs and UTF-8 CSV/JSON up to the configured bounded size are accepted. The default is `dry_run=true`; import requires an idempotency key.

Superuser subscriptions: `subscriptions_list`, `subscription_grant_access`, `subscription_revoke_access`. Mutations require `confirm=true`.

## Resources and prompts

Resources: `learn://me`, `learn://lessons`, `learn://lessons/{lesson_title}`, `learn://progress/summary`, `learn://family/status`.

Prompts: `create_vocabulary_lesson`, `create_complete_lesson`, `assign_lesson_to_child`, `review_difficult_words`, `analyze_learning_progress`.

## Mandatory AI rules (also embedded in the server `instructions`)

1. Creating a lesson: identify the one user from the current request, read only that user's languages, fill translations and examples for those languages only, validate, and only then treat the lesson as created (`lesson_create_complete`). Do not assign to anyone else unless asked.
2. Assigning an existing lesson to another user: read only the new user's languages, keep existing data, add only missing translations/examples, validate for that user, then assign (`lesson_assign_complete`).
3. Never fetch or process languages of family members the current task does not concern.
4. Never report a lesson as ready or assigned before its validation returned `COMPLETE` and the tool reported `saved`/`assigned=true`.

## Limits and safety

- Maximum list page: 100 items.
- Maximum word/progress batch: 100 items; TTS batch: 25 items.
- Per-token gateway rate limit: 120 calls/minute by default, stored in isolated Redis.
- Create/batch writes require idempotency keys.
- Delete and subscription mutations require explicit confirmation.
- Every lesson/word/family operation repeats ownership or link validation in the backend.
- Audit stores bounded counts and hashed client/user IDs, never word text, bearer tokens, cookies or provider credentials.

## Deployment

The production Compose services are `learn-words`, `mcp-gateway`, and `mcp-redis`. `mcp-gateway` runs as a non-root user with a read-only filesystem, dropped capabilities and no application volumes. Redis has no published port.

Required production environment keys (values must not be committed):

- `MCP_INTERNAL_TOKEN`: dedicated high-entropy shared secret used only between gateway and internal API.
- optional `MCP_ACCESS_TOKEN_TTL_SECONDS`, `MCP_AUTH_CODE_TTL_SECONDS`.

Use the project's incremental deployment workflow with infrastructure included for the first deployment or any Compose/nginx/gateway dependency change. Recreate only the three LearnWords services and reload only the proxy nginx after `nginx -t`.

## Verification

After deployment, perform an authenticated protocol flow: `initialize -> tools/list -> resources/list -> representative read -> reversible write -> read-after-write -> cleanup`. Revoke the grant and verify the same bearer is rejected. ChatGPT may cache tool schemas; remove/reconnect the connector after schema changes.
