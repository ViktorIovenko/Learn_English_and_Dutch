package com.learnwords.app.ui.lessons

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.learnwords.app.data.db.LessonCacheEntity
import com.learnwords.app.databinding.ItemLessonBinding
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class LessonAdapter(
    private val onLessonClick: (LessonCacheEntity) -> Unit,
    private val onHideToggle: (LessonCacheEntity) -> Unit,
    private val onSelectForDelete: (LessonCacheEntity) -> Unit
) : ListAdapter<LessonAdapter.LessonItem, LessonAdapter.LessonViewHolder>(DiffCallback()) {

    private val lastOpenedFormat = SimpleDateFormat("dd.MM.yyyy HH:mm", Locale.getDefault())

    data class LessonItem(
        val entity: LessonCacheEntity,
        val isSelected: Boolean,
        val isDeleteMode: Boolean
    )

    inner class LessonViewHolder(private val binding: ItemLessonBinding) :
        RecyclerView.ViewHolder(binding.root) {

        fun bind(item: LessonItem) {
            val lesson = item.entity
            binding.tvLessonTitle.text = lesson.lesson
            binding.tvWordCount.text = "${lesson.wordCount} слов"
            binding.tvNumber.text = lesson.number ?: ""
            binding.tvLastOpened.text = if (lesson.lastOpenedAt > 0L) {
                "Последний раз: ${lastOpenedFormat.format(Date(lesson.lastOpenedAt))}"
            } else {
                "Последний раз: не открывался"
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
                binding.btnHide.text = if (lesson.hidden) "Показать" else "Скрыть"
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
