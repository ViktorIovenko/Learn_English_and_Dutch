package com.learnwords.app

import android.app.Application
import com.learnwords.app.data.api.ApiClient
import com.learnwords.app.data.db.AppDatabase
import com.learnwords.app.data.repository.AppRepository
import com.learnwords.app.utils.PreferencesManager

class LearnWordsApp : Application() {

    val database by lazy { AppDatabase.getInstance(this) }
    val preferencesManager by lazy { PreferencesManager(this) }
    val apiClient by lazy { ApiClient(preferencesManager) }
    val repository by lazy { AppRepository(database, apiClient, preferencesManager) }

    override fun onCreate() {
        super.onCreate()
        instance = this
    }

    companion object {
        lateinit var instance: LearnWordsApp
            private set
    }
}
