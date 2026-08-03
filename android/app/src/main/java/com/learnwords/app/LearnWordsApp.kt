package com.learnwords.app

import android.app.Application
import com.learnwords.app.data.api.ApiClient
import com.learnwords.app.data.db.AppDatabase
import com.learnwords.app.data.repository.AppRepository
import com.learnwords.app.utils.PreferencesManager
import com.learnwords.app.utils.ChildLearningReminder
import com.learnwords.app.utils.WordContentCache

class LearnWordsApp : Application() {

    val database by lazy { AppDatabase.getInstance(this) }
    val preferencesManager by lazy { PreferencesManager(this) }
    val wordContentCache by lazy { WordContentCache(this, preferencesManager) }
    val apiClient by lazy { ApiClient(preferencesManager) }
    val repository by lazy { AppRepository(database, apiClient, preferencesManager, wordContentCache) }

    override fun onCreate() {
        super.onCreate()
        instance = this
        ChildLearningReminder.createChannel(this)
    }

    companion object {
        lateinit var instance: LearnWordsApp
            private set
    }
}
