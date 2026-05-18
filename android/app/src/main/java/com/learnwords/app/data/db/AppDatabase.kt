package com.learnwords.app.data.db

import android.content.Context
import androidx.room.*
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase
import kotlinx.coroutines.flow.Flow

// ─── Entities ─────────────────────────────────────────────────────────────────

@Entity(tableName = "words")
data class WordEntity(
    @PrimaryKey val id: Int,
    val lesson: String?,
    val number: String?,
    val nl: String?,
    val en: String?,
    val ru: String?,
    @ColumnInfo(name = "ex_nl") val exNl: String?,
    @ColumnInfo(name = "ex_en") val exEn: String?,
    @ColumnInfo(name = "ex_ru") val exRu: String?,
    @ColumnInfo(name = "audio_nl") val audioNl: String?,
    @ColumnInfo(name = "audio_en") val audioEn: String?,
    @ColumnInfo(name = "audio_ru") val audioRu: String?,
    val difficult: Boolean = false,
    val status: String?,
    @ColumnInfo(name = "cached_at") val cachedAt: Long = System.currentTimeMillis()
)

@Entity(tableName = "lessons_cache")
data class LessonCacheEntity(
    @PrimaryKey val lesson: String,
    val number: String?,
    @ColumnInfo(name = "word_count") val wordCount: Int,
    val hidden: Boolean = false,
    @ColumnInfo(name = "last_opened_at") val lastOpenedAt: Long = 0L,
    @ColumnInfo(name = "cached_at") val cachedAt: Long = System.currentTimeMillis()
)

@Entity(tableName = "progress_queue")
data class ProgressQueueEntity(
    @PrimaryKey(autoGenerate = true) val id: Int = 0,
    val scope: String,
    @ColumnInfo(name = "event_type") val eventType: String,
    @ColumnInfo(name = "event_ts") val eventTs: Long,
    val payload: String?,
    val synced: Boolean = false
)

// ─── DAOs ──────────────────────────────────────────────────────────────────────

@Dao
interface WordDao {
    @Query("SELECT * FROM words WHERE lesson = :lesson ORDER BY number ASC")
    suspend fun getWordsByLesson(lesson: String): List<WordEntity>

    @Query("SELECT * FROM words WHERE difficult = 1")
    fun getDifficultWords(): Flow<List<WordEntity>>

    @Query("SELECT * FROM words WHERE id = :id")
    suspend fun getWordById(id: Int): WordEntity?

    @Query("SELECT * FROM words WHERE (nl LIKE '%' || :q || '%' OR en LIKE '%' || :q || '%' OR ru LIKE '%' || :q || '%') LIMIT :limit OFFSET :offset")
    suspend fun searchWords(q: String, limit: Int, offset: Int): List<WordEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertWords(words: List<WordEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertWord(word: WordEntity)

    @Query("UPDATE words SET difficult = :difficult WHERE id = :id")
    suspend fun setDifficult(id: Int, difficult: Boolean)

    @Query("DELETE FROM words WHERE lesson = :lesson")
    suspend fun deleteByLesson(lesson: String)

    @Query("DELETE FROM words WHERE id = :id")
    suspend fun deleteById(id: Int)

    @Query("SELECT COUNT(*) FROM words WHERE lesson = :lesson")
    suspend fun countByLesson(lesson: String): Int
}

@Dao
interface LessonDao {
    @Query("SELECT * FROM lessons_cache ORDER BY hidden ASC, number ASC, lesson ASC")
    fun getLessons(): Flow<List<LessonCacheEntity>>

    @Query("SELECT * FROM lessons_cache ORDER BY hidden ASC, number ASC, lesson ASC")
    suspend fun getLessonsOnce(): List<LessonCacheEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertLessons(lessons: List<LessonCacheEntity>)

    @Query("UPDATE lessons_cache SET hidden = :hidden WHERE lesson = :lesson")
    suspend fun setHidden(lesson: String, hidden: Boolean)

    @Query("UPDATE lessons_cache SET last_opened_at = :openedAt WHERE lesson = :lesson")
    suspend fun setLastOpenedAt(lesson: String, openedAt: Long)

    @Query("DELETE FROM lessons_cache WHERE lesson = :lesson")
    suspend fun deleteLesson(lesson: String)

    @Query("DELETE FROM lessons_cache")
    suspend fun clearAll()
}

@Dao
interface ProgressQueueDao {
    @Query("SELECT * FROM progress_queue WHERE synced = 0")
    suspend fun getPendingEvents(): List<ProgressQueueEntity>

    @Insert
    suspend fun insertEvent(event: ProgressQueueEntity)

    @Query("UPDATE progress_queue SET synced = 1 WHERE id IN (:ids)")
    suspend fun markSynced(ids: List<Int>)

    @Query("DELETE FROM progress_queue WHERE synced = 1")
    suspend fun deleteSynced()
}

// ─── Database ──────────────────────────────────────────────────────────────────

@Database(
    entities = [WordEntity::class, LessonCacheEntity::class, ProgressQueueEntity::class],
    version = 2,
    exportSchema = false
)
abstract class AppDatabase : RoomDatabase() {

    abstract fun wordDao(): WordDao
    abstract fun lessonDao(): LessonDao
    abstract fun progressQueueDao(): ProgressQueueDao

    companion object {
        @Volatile
        private var INSTANCE: AppDatabase? = null

        fun getInstance(context: Context): AppDatabase {
            return INSTANCE ?: synchronized(this) {
                Room.databaseBuilder(
                    context.applicationContext,
                    AppDatabase::class.java,
                    "learnwords.db"
                )
                    .addMigrations(MIGRATION_1_2)
                    .build()
                    .also { INSTANCE = it }
            }
        }

        private val MIGRATION_1_2 = object : Migration(1, 2) {
            override fun migrate(db: SupportSQLiteDatabase) {
                db.execSQL("ALTER TABLE lessons_cache ADD COLUMN last_opened_at INTEGER NOT NULL DEFAULT 0")
            }
        }
    }
}
