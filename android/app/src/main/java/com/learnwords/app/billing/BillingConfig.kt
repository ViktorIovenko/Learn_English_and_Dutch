package com.learnwords.app.billing

/**
 * ══════════════════════════════════════════════════════════════════
 *  ЗАГЛУШКИ — заменить после настройки Google Play Console
 * ══════════════════════════════════════════════════════════════════
 *
 * Как настроить:
 * 1. Зайди в Google Play Console → твоё приложение
 * 2. Монетизация → Подписки → Создать подписку
 * 3. Скопируй ID продукта (например "learnwords_monthly") → SUBSCRIPTION_MONTHLY_ID
 * 4. Создай ещё одну подписку для годовой (необязательно) → SUBSCRIPTION_YEARLY_ID
 * 5. BASE64_PUBLIC_KEY: Google Play Console → Настройки → Лицензирование
 */
object BillingConfig {

    // ── ⚠️ ЗАГЛУШКА: замени на реальный ID из Google Play Console ──────────
    const val SUBSCRIPTION_MONTHLY_ID = "learnwords_monthly"   // TODO: замени
    const val SUBSCRIPTION_YEARLY_ID  = "learnwords_yearly"    // TODO: замени (или удали если не нужно)

    // ── ⚠️ ЗАГЛУШКА: ключ из Google Play Console → Настройки → Лицензирование ──
    const val BASE64_PUBLIC_KEY = "REPLACE_WITH_YOUR_BASE64_PUBLIC_KEY"  // TODO: замени

    // Список всех ID продуктов для запроса деталей
    val ALL_SUBSCRIPTION_IDS = listOf(SUBSCRIPTION_MONTHLY_ID, SUBSCRIPTION_YEARLY_ID)

    // Цены — будут заменены реальными из Google Play при загрузке
    const val PRICE_MONTHLY_FALLBACK = "€4.99 / месяц"
    const val PRICE_YEARLY_FALLBACK  = "€39.99 / год"
}
