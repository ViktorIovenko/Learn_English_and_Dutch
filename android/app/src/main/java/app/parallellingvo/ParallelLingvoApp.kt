package app.parallellingvo

import app.parallellingvo.billing.PurchaseSyncWorker

import android.app.Application
import app.parallellingvo.data.api.ApiClient
import app.parallellingvo.data.db.AppDatabase
import app.parallellingvo.data.repository.AppRepository
import app.parallellingvo.utils.PreferencesManager
import app.parallellingvo.utils.ChildLearningReminder
import app.parallellingvo.utils.WordContentCache

class ParallelLingvoApp : Application() {

    val database by lazy { AppDatabase.getInstance(this) }
    val preferencesManager by lazy { PreferencesManager(this) }
    val wordContentCache by lazy { WordContentCache(this, preferencesManager) }
    val apiClient by lazy { ApiClient(preferencesManager) }
    val repository by lazy { AppRepository(database, apiClient, preferencesManager, wordContentCache) }

    override fun onCreate() {
        super.onCreate()
        instance = this
        ChildLearningReminder.createChannel(this)
        PurchaseSyncWorker.schedule(this)
    }

    companion object {
        lateinit var instance: ParallelLingvoApp
            private set
    }
}
