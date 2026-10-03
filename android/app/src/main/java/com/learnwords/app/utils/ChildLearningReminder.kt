package com.learnwords.app.utils

import android.app.AlarmManager
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import com.learnwords.app.LearnWordsApp
import com.learnwords.app.MainActivity
import com.learnwords.app.R
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import kotlinx.coroutines.withTimeoutOrNull
import java.util.Calendar
import java.util.TimeZone

object ChildLearningReminder {
    private const val PREFS = "child_learning_reminder"
    private const val KEY_ENABLED = "enabled"
    private const val KEY_PERMISSION_REQUESTED = "permission_requested"
    private const val AFTERNOON_REQUEST_CODE = 1400
    private const val EVENING_REQUEST_CODE = 2100
    private const val AFTERNOON_NOTIFICATION_ID = 1400
    private const val EVENING_NOTIFICATION_ID = 2100
    private const val CHANNEL_ID = "child_learning_daily"

    fun createChannel(context: Context) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val channel = NotificationChannel(
            CHANNEL_ID,
            context.getString(R.string.child_reminder_channel_name),
            NotificationManager.IMPORTANCE_DEFAULT
        ).apply {
            description = context.getString(R.string.child_reminder_channel_description)
        }
        context.getSystemService(NotificationManager::class.java)
            .createNotificationChannel(channel)
    }

    fun setEnabled(context: Context, enabled: Boolean) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit()
            .putBoolean(KEY_ENABLED, enabled)
            .apply()
        if (enabled) scheduleNext(context) else cancel(context)
    }

    fun isEnabled(context: Context): Boolean =
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .getBoolean(KEY_ENABLED, false)

    fun shouldRequestPermission(context: Context): Boolean =
        !context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .getBoolean(KEY_PERMISSION_REQUESTED, false)

    fun markPermissionRequested(context: Context) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit()
            .putBoolean(KEY_PERMISSION_REQUESTED, true)
            .apply()
    }

    fun scheduleNext(context: Context) {
        if (!isEnabled(context)) return
        scheduleAt(context, 14, AFTERNOON_REQUEST_CODE, ChildLearningReminderReceiver::class.java)
        scheduleAt(context, 21, EVENING_REQUEST_CODE, ChildLearningEveningReminderReceiver::class.java)
    }

    private fun scheduleAt(
        context: Context,
        hour: Int,
        requestCode: Int,
        receiverClass: Class<out BroadcastReceiver>
    ) {
        val now = Calendar.getInstance()
        val next = Calendar.getInstance().apply {
            set(Calendar.HOUR_OF_DAY, hour)
            set(Calendar.MINUTE, 0)
            set(Calendar.SECOND, 0)
            set(Calendar.MILLISECOND, 0)
            if (!after(now)) add(Calendar.DAY_OF_YEAR, 1)
        }
        val alarmManager = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager
        alarmManager.setAndAllowWhileIdle(
            AlarmManager.RTC_WAKEUP,
            next.timeInMillis,
            reminderPendingIntent(context, requestCode, receiverClass)
        )
    }

    fun showAfternoon(context: Context) {
        if (!isEnabled(context)) return
        showNotification(
            context,
            AFTERNOON_NOTIFICATION_ID,
            context.getString(R.string.child_reminder_title),
            context.getString(R.string.child_reminder_text)
        )
    }

    fun showEvening(context: Context, todayCount: Int, dailyGoal: Int) {
        if (!isEnabled(context)) return
        showNotification(
            context,
            EVENING_NOTIFICATION_ID,
            context.getString(R.string.child_evening_reminder_title),
            context.getString(R.string.child_evening_reminder_text, todayCount, dailyGoal)
        )
    }

    private fun showNotification(context: Context, notificationId: Int, title: String, text: String) {
        createChannel(context)
        val openApp = PendingIntent.getActivity(
            context,
            notificationId,
            Intent(context, MainActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP
            },
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        val notification = NotificationCompat.Builder(context, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_star_24)
            .setContentTitle(title)
            .setContentText(text)
            .setContentIntent(openApp)
            .setAutoCancel(true)
            .setPriority(NotificationCompat.PRIORITY_DEFAULT)
            .build()
        try {
            NotificationManagerCompat.from(context).notify(notificationId, notification)
        } catch (_: SecurityException) {
            // Android 13+: permission may not have been granted yet.
        }
    }

    private fun cancel(context: Context) {
        val alarmManager = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager
        alarmManager.cancel(reminderPendingIntent(
            context, AFTERNOON_REQUEST_CODE, ChildLearningReminderReceiver::class.java
        ))
        alarmManager.cancel(reminderPendingIntent(
            context, EVENING_REQUEST_CODE, ChildLearningEveningReminderReceiver::class.java
        ))
        NotificationManagerCompat.from(context).cancel(AFTERNOON_NOTIFICATION_ID)
        NotificationManagerCompat.from(context).cancel(EVENING_NOTIFICATION_ID)
    }

    private fun reminderPendingIntent(
        context: Context,
        requestCode: Int,
        receiverClass: Class<out BroadcastReceiver>
    ): PendingIntent =
        PendingIntent.getBroadcast(
            context,
            requestCode,
            Intent(context, receiverClass),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
}

class ChildLearningReminderReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent?) {
        if (!ChildLearningReminder.isEnabled(context)) return
        ChildLearningReminder.showAfternoon(context)
        ChildLearningReminder.scheduleNext(context)
    }
}

class ChildLearningEveningReminderReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent?) {
        if (!ChildLearningReminder.isEnabled(context)) return
        val pendingResult = goAsync()
        CoroutineScope(SupervisorJob() + Dispatchers.IO).launch {
            try {
                val app = context.applicationContext as? LearnWordsApp ?: return@launch
                val now = System.currentTimeMillis()
                val timezoneOffsetMinutes = -(TimeZone.getDefault().getOffset(now) / 60_000)
                when (val result = withTimeoutOrNull(8_000L) {
                    app.repository.getChildLearningStatus(timezoneOffsetMinutes)
                }) {
                    is NetworkResult.Success -> {
                        val status = result.data
                        if (status.isChild && !status.goalComplete) {
                            ChildLearningReminder.showEvening(
                                context,
                                status.todayCount,
                                status.dailyGoal
                            )
                        }
                    }
                    else -> Unit
                }
            } finally {
                ChildLearningReminder.scheduleNext(context)
                pendingResult.finish()
            }
        }
    }
}

class ChildLearningReminderRestoreReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent?) {
        if (ChildLearningReminder.isEnabled(context)) {
            ChildLearningReminder.scheduleNext(context)
        }
    }
}
