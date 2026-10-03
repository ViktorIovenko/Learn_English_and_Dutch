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
    val de: String? = null,
    val fr: String? = null,
    val es: String? = null,
    val ita: String? = null,
    val pt: String? = null,
    val pl: String? = null,
    val uk: String? = null,
    @ColumnInfo(name = "ex_nl") val exNl: String?,
    @ColumnInfo(name = "ex_en") val exEn: String?,
    @ColumnInfo(name = "ex_ru") val exRu: String?,
    @ColumnInfo(name = "ex_de") val exDe: String? = null,
    @ColumnInfo(name = "ex_fr") val exFr: String? = null,
    @ColumnInfo(name = "ex_es") val exEs: String? = null,
    @ColumnInfo(name = "ex_it") val exIt: String? = null,
    @ColumnInfo(name = "ex_pt") val exPt: String? = null,
    @ColumnInfo(name = "ex_pl") val exPl: String? = null,
    @ColumnInfo(name = "ex_uk") val exUk: String? = null,
    @ColumnInfo(name = "audio_nl") val audioNl: String?,
    @ColumnInfo(name = "audio_en") val audioEn: String?,
    @ColumnInfo(name = "audio_ru") val audioRu: String?,
    @ColumnInfo(name = "audio_de") val audioDe: String? = null,
    @ColumnInfo(name = "audio_fr") val audioFr: String? = null,
    @ColumnInfo(name = "audio_es") val audioEs: String? = null,
    @ColumnInfo(name = "audio_it") val audioIt: String? = null,
    @ColumnInfo(name = "audio_pt") val audioPt: String? = null,
    @ColumnInfo(name = "audio_pl") val audioPl: String? = null,
    @ColumnInfo(name = "audio_uk") val audioUk: String? = null,
    val difficult: Boolean = false,
    val status: String?,
    @ColumnInfo(name = "cached_at") val cachedAt: Long = System.currentTimeMillis()
)

@Entity(tableName = "lessons_cache")
data class LessonCacheEntity(
    @PrimaryKey val lesson: String,
    val number: String?,
    @ColumnInfo(name = "word_count") val wordCount: Int,
    @ColumnInfo(name = "upload_order") val uploadOrder: Long = 0L,
    val hidden: Boolean = false,
    @ColumnInfo(name = "is_priority") val isPriority: Boolean = false,
    @ColumnInfo(name = "language_progress_json") val languageProgressJson: String = "[]",
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

    @Query("SELECT * FROM words WHERE difficult = 1 ORDER BY lesson ASC, number ASC, id ASC")
    suspend fun getDifficultWordsOnce(): List<WordEntity>

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

    @Query("""
        UPDATE words SET
            audio_nl = COALESCE(:nl, audio_nl),
            audio_en = COALESCE(:en, audio_en),
            audio_ru = COALESCE(:ru, audio_ru),
            audio_de = COALESCE(:de, audio_de),
            audio_fr = COALESCE(:fr, audio_fr),
            audio_es = COALESCE(:es, audio_es),
            audio_it = COALESCE(:ita, audio_it),
            audio_pt = COALESCE(:pt, audio_pt),
            audio_pl = COALESCE(:pl, audio_pl),
            audio_uk = COALESCE(:uk, audio_uk)
        WHERE id = :id
    """)
    suspend fun updateAudioUrls(
        id: Int,
        nl: String?, en: String?, ru: String?, de: String?, fr: String?,
        es: String?, ita: String?, pt: String?, pl: String?, uk: String?
    )

    @Query("DELETE FROM words WHERE lesson = :lesson")
    suspend fun deleteByLesson(lesson: String)

    @Query("DELETE FROM words WHERE id = :id")
    suspend fun deleteById(id: Int)

    @Query("SELECT COUNT(*) FROM words WHERE lesson = :lesson")
    suspend fun countByLesson(lesson: String): Int
}

@Dao
interface LessonDao {
    @Query("SELECT * FROM lessons_cache ORDER BY upload_order DESC, lesson ASC")
    fun getLessons(): Flow<List<LessonCacheEntity>>

    @Query("SELECT * FROM lessons_cache ORDER BY upload_order DESC, lesson ASC")
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
    version = 6,
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
                    .addMigrations(MIGRATION_1_2, MIGRATION_2_3, MIGRATION_3_4, MIGRATION_4_5, MIGRATION_5_6)
                    .build()
                    .also { INSTANCE = it }
            }
        }

        private val MIGRATION_1_2 = object : Migration(1, 2) {
            override fun migrate(db: SupportSQLiteDatabase) {
                db.execSQL("ALTER TABLE lessons_cache ADD COLUMN last_opened_at INTEGER NOT NULL DEFAULT 0")
            }
        }

        private val MIGRATION_2_3 = object : Migration(2, 3) {
            override fun migrate(db: SupportSQLiteDatabase) {
                db.execSQL("ALTER TABLE lessons_cache ADD COLUMN language_progress_json TEXT NOT NULL DEFAULT '[]'")
            }
        }

        private val MIGRATION_3_4 = object : Migration(3, 4) {
            override fun migrate(db: SupportSQLiteDatabase) {
                db.execSQL("ALTER TABLE lessons_cache ADD COLUMN is_priority INTEGER NOT NULL DEFAULT 0")
            }
        }

        private val MIGRATION_4_5 = object : Migration(4, 5) {
            override fun migrate(db: SupportSQLiteDatabase) {
                for (column in listOf(
                    "de", "fr", "es", "ita", "pt", "pl", "uk",
                    "ex_de", "ex_fr", "ex_es", "ex_it", "ex_pt", "ex_pl", "ex_uk",
                    "audio_de", "audio_fr", "audio_es", "audio_it", "audio_pt", "audio_pl", "audio_uk"
                )) {
                    db.execSQL("ALTER TABLE words ADD COLUMN $column TEXT")
                }
            }
        }

        private val MIGRATION_5_6 = object : Migration(5, 6) {
            override fun migrate(db: SupportSQLiteDatabase) {
                db.execSQL("ALTER TABLE lessons_cache ADD COLUMN upload_order INTEGER NOT NULL DEFAULT 0")
            }
        }
    }
}
