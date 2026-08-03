package com.learnwords.app.ui.lessons

import android.view.LayoutInflater
import android.view.ViewGroup
import android.view.Gravity
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.TextView
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.learnwords.app.data.db.LessonCacheEntity
import com.learnwords.app.databinding.ItemLessonBinding
import com.learnwords.app.R
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import com.learnwords.app.data.api.LessonLanguageProgressDto
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class LessonAdapter(
    private val onLessonClick: (LessonCacheEntity) -> Unit,
    private val onHideToggle: (LessonCacheEntity) -> Unit,
    private val onSelectForDelete: (LessonCacheEntity) -> Unit
) : ListAdapter<LessonAdapter.LessonItem, LessonAdapter.LessonViewHolder>(DiffCallback()) {

    private val lastOpenedFormat = SimpleDateFormat("dd.MM.yyyy HH:mm", Locale.getDefault())
    private val gson = Gson()

    data class LessonItem(
        val entity: LessonCacheEntity,
        val isSelected: Boolean,
        val isDeleteMode: Boolean
    )

    inner class LessonViewHolder(private val binding: ItemLessonBinding) :
        RecyclerView.ViewHolder(binding.root) {

        fun bind(item: LessonItem) {
            val lesson = item.entity
            val context = binding.root.context
            binding.tvLessonTitle.text = if (lesson.isPriority) "⭐ ${lesson.lesson}" else lesson.lesson
            binding.tvWordCount.text = lesson.wordCount.toString()
            binding.tvNumber.text = lesson.number ?: ""
            binding.tvLastOpened.text = if (lesson.lastOpenedAt > 0L) {
                context.getString(R.string.last_opened, lastOpenedFormat.format(Date(lesson.lastOpenedAt)))
            } else {
                context.getString(R.string.last_opened_never)
            }
            binding.languageProgressContainer.removeAllViews()
            val progress: List<LessonLanguageProgressDto> = runCatching {
                gson.fromJson<List<LessonLanguageProgressDto>>(
                    lesson.languageProgressJson,
                    object : TypeToken<List<LessonLanguageProgressDto>>() {}.type
                )
            }.getOrDefault(emptyList())
            progress.forEach { language ->
                val row = LinearLayout(context).apply {
                    orientation = LinearLayout.HORIZONTAL
                    gravity = Gravity.CENTER_VERTICAL or Gravity.END
                }
                row.addView(ProgressBar(context, null, android.R.attr.progressBarStyleHorizontal).apply {
                    max = 100
                    this.progress = language.percent.coerceIn(0, 100)
                    layoutParams = LinearLayout.LayoutParams(context.resources.displayMetrics.density.times(54).toInt(),
                        context.resources.displayMetrics.density.times(10).toInt())
                })
                row.addView(TextView(context).apply {
                    text = language.code.uppercase(Locale.ROOT)
                    textSize = 11f
                    setPadding(6, 0, 4, 0)
                })
                row.addView(TextView(context).apply {
                    text = language.learnedWords.toString()
                    textSize = 12f
                })
                binding.languageProgressContainer.addView(row)
            }

            binding.root.alpha = if (lesson.hidden) 0.4f else 1.0f

            if (item.isDeleteMode) {
                binding.checkboxDelete.visibility = android.view.View.VISIBLE
                binding.btnHide.visibility = android.view.View.GONE
                binding.checkboxDelete.isChecked = item.isSelected
                binding.root.setOnClickListener { onSelectForDelete(lesson) }
                binding.checkboxDelete.setOnClickListener { onSelectForDelete(lesson) }
            } else {
                binding.checkboxDelete.visibility = android.view.View.GONE
                binding.btnHide.visibility = android.view.View.VISIBLE
                binding.btnHide.text = if (lesson.hidden) context.getString(R.string.show) else context.getString(R.string.hide)
                binding.btnHide.setOnClickListener { onHideToggle(lesson) }
                binding.root.setOnClickListener { onLessonClick(lesson) }
            }
        }
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): LessonViewHolder {
        val binding = ItemLessonBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return LessonViewHolder(binding)
    }

    override fun onBindViewHolder(holder: LessonViewHolder, position: Int) {
        holder.bind(getItem(position))
    }

    class DiffCallback : DiffUtil.ItemCallback<LessonItem>() {
        override fun areItemsTheSame(old: LessonItem, new: LessonItem) =
            old.entity.lesson == new.entity.lesson

        override fun areContentsTheSame(old: LessonItem, new: LessonItem) = old == new
    }
}
