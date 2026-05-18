package com.learnwords.app.data.ai

/**
 * Настройки Ollama.
 *
 * Ollama — локальный LLM-сервер (https://ollama.com).
 * В веб-версии браузер вызывает его напрямую на localhost:11434.
 * В Android — нужно указать IP машины в локальной сети, например:
 *   http://192.168.1.10:11434
 *
 * Пользователь настраивает URL и модель в экране загрузки слов.
 */
object OllamaConfig {

    // ⚠️ URL по умолчанию — работает только если телефон и компьютер в одной сети
    // Пользователь может изменить в настройках на экране "Добавить слова"
    const val DEFAULT_URL = "http://192.168.1.1:11434"

    // ⚠️ Модель по умолчанию — должна быть установлена: `ollama pull llama3.1:8b`
    const val DEFAULT_MODEL = "llama3.1:8b"

    const val TIMEOUT_TRANSLATE_MS = 60_000L    // 60 секунд на перевод одного слова
    const val TIMEOUT_GENERATE_MS  = 120_000L   // 2 минуты на генерацию по теме

    // ─── Промпты (идентичны веб-версии upload.js) ─────────────────────────

    fun buildTranslatePrompt(word: String, fromLang: String, level: String = "A2"): String {
        val langLabel = when (fromLang) {
            "nl" -> "Dutch"
            "en" -> "English"
            "ru" -> "Russian"
            else -> fromLang
        }
        return """
You are a language learning assistant for a Dutch course.
Translate the following $langLabel word: "$word"
CEFR level: $level

Return a JSON object with these exact keys:
- "nl": natural Dutch word/phrase (1-3 words)
- "en": natural English translation (1-3 words)
- "ru": natural Russian translation — use proper literary Russian, NOT word-for-word. The Russian must sound like a native speaker wrote it.
- "ex_nl": one short example sentence in Dutch ($level level). Surround the studied word with ** markers, e.g. "Ik moet de **rekening** betalen."
- "ex_en": the same sentence translated naturally into English. Surround the corresponding word with ** markers.
- "ex_ru": the same sentence translated naturally into Russian. Surround the corresponding word with ** markers.
- "en" must be the base/dictionary form of the word marked with ** in "ex_en"
- "ru" must be the base/dictionary form of the word marked with ** in "ex_ru"

Return ONLY a JSON object. No markdown, no code fences, no explanation.
        """.trimIndent()
    }

    fun buildGenerateTopicPrompt(
        topic: String,
        level: String,
        count: Int,
        languages: List<String>
    ): String {
        val langStr = languages.joinToString(", ")
        return """
You are a language learning assistant for a Dutch course.
Topic: "$topic"
CEFR level: $level
Number of words: $count
Languages to include: $langStr

Generate $count Dutch vocabulary words related to the topic "$topic" at $level level.

Return a JSON array of objects. Each object must have:
- "nl": Dutch word (1-3 words)
- "en": English translation (1-3 words)
- "ru": Russian translation (literary, natural)
- "ex_nl": example sentence in Dutch with the word in context. Wrap the key word with ** markers.
- "ex_en": same sentence in English. Wrap the key word with ** markers.
- "ex_ru": same sentence in Russian. Wrap the key word with ** markers.

Return ONLY a JSON array. No markdown, no code fences, no explanation.
        """.trimIndent()
    }
}
