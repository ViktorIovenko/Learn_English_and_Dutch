package com.learnwords.app.data.ai

import android.util.Log
import com.google.gson.Gson
import com.google.gson.JsonArray
import com.google.gson.JsonObject
import com.google.gson.JsonParser
import com.learnwords.app.data.api.WordDto
import com.learnwords.app.utils.NetworkResult
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import java.util.concurrent.TimeUnit

private const val TAG = "OllamaService"

/**
 * Клиент для прямого взаимодействия с Ollama API.
 *
 * Ollama REST API документация: https://github.com/ollama/ollama/blob/main/docs/api.md
 *
 * Схема запроса (POST /api/chat):
 * {
 *   "model": "llama3.1:8b",
 *   "messages": [
 *     { "role": "system", "content": "..." },
 *     { "role": "user",   "content": "..." }
 *   ],
 *   "stream": false,
 *   "format": "json"
 * }
 *
 * Схема ответа:
 * {
 *   "message": { "role": "assistant", "content": "..." },
 *   ...
 * }
 */
class OllamaService(
    private val baseUrl: String,
    private val model: String,
    private val translateTimeoutMs: Long = OllamaConfig.TIMEOUT_TRANSLATE_MS,
    private val generateTimeoutMs: Long  = OllamaConfig.TIMEOUT_GENERATE_MS
) {

    private val gson = Gson()
    private val mediaType = "application/json".toMediaType()

    // Отдельные клиенты с разными таймаутами
    private val translateClient = buildClient(translateTimeoutMs)
    private val generateClient  = buildClient(generateTimeoutMs)

    private fun buildClient(timeoutMs: Long) = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(timeoutMs, TimeUnit.MILLISECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()

    // ─── Проверка доступности Ollama ──────────────────────────────────────

    suspend fun checkAvailability(): OllamaStatus {
        return try {
            val request = Request.Builder()
                .url("${baseUrl.trimEnd('/')}/api/tags")
                .get()
                .build()
            val response = translateClient.newCall(request).execute()
            if (response.isSuccessful) {
                val body = response.body?.string() ?: ""
                val json = JsonParser().parse(body).asJsonObject
                val models = json.getAsJsonArray("models")
                    ?.mapNotNull { it.asJsonObject?.get("name")?.asString }
                    ?: emptyList()
                OllamaStatus.Available(models)
            } else {
                OllamaStatus.Error("HTTP ${response.code}")
            }
        } catch (e: Exception) {
            OllamaStatus.Error(e.message ?: "Недоступна")
        }
    }

    // ─── Перевод одного слова ─────────────────────────────────────────────

    /**
     * Переводит слово на все языки (NL, EN, RU) + генерирует примеры.
     *
     * Промпт идентичен _callOllama() из upload.js.
     */
    suspend fun translateWord(
        word: String,
        fromLang: String,
        level: String = "A2"
    ): NetworkResult<WordDto> {
        val prompt = OllamaConfig.buildTranslatePrompt(word, fromLang, level)
        return when (val result = callOllama(translateClient, prompt)) {
            is NetworkResult.Success -> {
                try {
                    val dto = parseWordObject(result.data)
                    NetworkResult.Success(dto)
                } catch (e: Exception) {
                    Log.e(TAG, "Failed to parse word: ${result.data}", e)
                    NetworkResult.Error("Не удалось разобрать ответ модели: ${e.message}")
                }
            }
            is NetworkResult.Error -> result
            else -> NetworkResult.Error("Неизвестная ошибка")
        }
    }

    // ─── Генерация слов по теме ───────────────────────────────────────────

    /**
     * Генерирует список слов по теме.
     *
     * Промпт идентичен generateByTopic() из upload.js.
     */
    suspend fun generateByTopic(
        topic: String,
        level: String,
        count: Int,
        languages: List<String>
    ): NetworkResult<List<WordDto>> {
        val prompt = OllamaConfig.buildGenerateTopicPrompt(topic, level, count, languages)
        return when (val result = callOllama(generateClient, prompt)) {
            is NetworkResult.Success -> {
                try {
                    val words = parseWordArray(result.data)
                    if (words.isEmpty()) {
                        NetworkResult.Error("Модель вернула пустой список")
                    } else {
                        NetworkResult.Success(words)
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "Failed to parse words array: ${result.data}", e)
                    NetworkResult.Error("Не удалось разобрать ответ модели: ${e.message}")
                }
            }
            is NetworkResult.Error -> result
            else -> NetworkResult.Error("Неизвестная ошибка")
        }
    }

    // ─── Внутренний вызов Ollama /api/chat ────────────────────────────────

    private suspend fun callOllama(
        client: OkHttpClient,
        userPrompt: String
    ): NetworkResult<String> {
        return try {
            val requestBody = gson.toJson(
                mapOf(
                    "model" to model,
                    "messages" to listOf(
                        mapOf("role" to "system", "content" to "You are a language assistant. Return ONLY valid JSON, no markdown fences, no explanations."),
                        mapOf("role" to "user", "content" to userPrompt)
                    ),
                    "stream" to false,
                    "format" to "json"
                )
            )

            val request = Request.Builder()
                .url("${baseUrl.trimEnd('/')}/api/chat")
                .post(requestBody.toRequestBody(mediaType))
                .build()

            Log.d(TAG, "Calling Ollama model=$model url=${baseUrl}")
            val response = client.newCall(request).execute()

            if (!response.isSuccessful) {
                return NetworkResult.Error("Ollama HTTP ${response.code}: ${response.message}")
            }

            val responseBody = response.body?.string()
                ?: return NetworkResult.Error("Пустой ответ от Ollama")

            val jsonResponse = JsonParser().parse(responseBody).asJsonObject
            val content = jsonResponse
                .getAsJsonObject("message")
                ?.get("content")?.asString
                ?: jsonResponse.get("response")?.asString
                ?: return NetworkResult.Error("Не удалось найти content в ответе Ollama")

            Log.d(TAG, "Ollama response: $content")
            NetworkResult.Success(content.trim())

        } catch (e: java.net.SocketTimeoutException) {
            NetworkResult.Error("Время ожидания истекло. Попробуйте ещё раз или используйте более лёгкую модель.")
        } catch (e: java.net.ConnectException) {
            NetworkResult.Error("Не удалось подключиться к Ollama по адресу $baseUrl\nПроверьте что Ollama запущена и доступна с телефона.")
        } catch (e: Exception) {
            Log.e(TAG, "Ollama call failed", e)
            NetworkResult.Error("Ошибка: ${e.message}")
        }
    }

    // ─── Парсинг ответов ──────────────────────────────────────────────────

    private fun parseWordObject(raw: String): WordDto {
        val cleaned = extractJson(raw)
        val obj = JsonParser().parse(cleaned).asJsonObject
        return WordDto(
            id = 0,
            lesson = null,
            number = null,
            nl = obj.getString("nl"),
            en = obj.getString("en"),
            ru = obj.getString("ru"),
            exNl = obj.getString("ex_nl"),
            exEn = obj.getString("ex_en"),
            exRu = obj.getString("ex_ru"),
            audioNl = null, audioEn = null, audioRu = null,
            difficult = false, status = null
        )
    }

    private fun parseWordArray(raw: String): List<WordDto> {
        val cleaned = extractJson(raw)
        val element = JsonParser().parse(cleaned)

        // Ollama иногда оборачивает массив в объект
        val array: JsonArray = when {
            element.isJsonArray -> element.asJsonArray
            element.isJsonObject -> {
                val obj = element.asJsonObject
                val key = obj.keySet().firstOrNull { obj.get(it).isJsonArray }
                    ?: throw Exception("Не найден массив в ответе")
                obj.getAsJsonArray(key)
            }
            else -> throw Exception("Ожидался JSON массив")
        }

        return array.mapNotNull { el ->
            try {
                val obj = el.asJsonObject
                WordDto(
                    id = 0, lesson = null, number = null,
                    nl = obj.getString("nl"),
                    en = obj.getString("en"),
                    ru = obj.getString("ru"),
                    exNl = obj.getString("ex_nl"),
                    exEn = obj.getString("ex_en"),
                    exRu = obj.getString("ex_ru"),
                    audioNl = null, audioEn = null, audioRu = null,
                    difficult = false, status = null
                )
            } catch (e: Exception) {
                Log.w(TAG, "Skipping malformed word: $el", e)
                null
            }
        }
    }

    /**
     * Извлекает JSON из ответа модели.
     * Модели иногда оборачивают JSON в markdown-блоки вроде ```json ... ```
     */
    private fun extractJson(raw: String): String {
        // Убираем markdown code fences
        val stripped = raw
            .replace(Regex("```json\\s*"), "")
            .replace(Regex("```\\s*"), "")
            .trim()

        // Ищем первый JSON-массив или объект
        val arrayStart = stripped.indexOf('[')
        val objectStart = stripped.indexOf('{')

        return when {
            arrayStart != -1 && (objectStart == -1 || arrayStart < objectStart) -> {
                val end = stripped.lastIndexOf(']')
                if (end > arrayStart) stripped.substring(arrayStart, end + 1) else stripped
            }
            objectStart != -1 -> {
                val end = stripped.lastIndexOf('}')
                if (end > objectStart) stripped.substring(objectStart, end + 1) else stripped
            }
            else -> stripped
        }
    }

    private fun JsonObject.getString(key: String): String? =
        if (has(key) && !get(key).isJsonNull) get(key).asString else null
}

/** Статус доступности Ollama */
sealed class OllamaStatus {
    data class Available(val models: List<String>) : OllamaStatus()
    data class Error(val message: String) : OllamaStatus()
}
