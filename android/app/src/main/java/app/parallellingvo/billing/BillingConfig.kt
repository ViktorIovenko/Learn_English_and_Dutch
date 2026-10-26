package app.parallellingvo.billing

import app.parallellingvo.BuildConfig

/** Product IDs come from the authenticated backend; prices/offers only from Play. */
object BillingConfig {
    const val PACKAGE_NAME = BuildConfig.APPLICATION_ID
}
