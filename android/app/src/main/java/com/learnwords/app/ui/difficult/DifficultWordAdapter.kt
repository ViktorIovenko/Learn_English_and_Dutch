package com.learnwords.app.ui.difficult

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.learnwords.app.data.db.WordEntity
import com.learnwords.app.databinding.ItemDifficultWordBinding

class DifficultWordAdapter(
    private val onUnmark: (WordEntity) -> Unit
) : ListAdapter<WordEntity, DifficultWordAdapter.WordViewHolder>(DiffCallback()) {

    inner class WordViewHolder(private val binding: ItemDifficultWordBinding) :
        RecyclerView.ViewHolder(binding.root) {

        fun bind(word: WordEntity) {
            binding.tvNl.text = word.nl ?: "-"
            binding.tvEn.text = word.en ?: "-"
            binding.tvRu.text = word.ru ?: "-"
            binding.tvLesson.text = word.lesson ?: ""
            binding.tvExNl.text = word.exNl ?: ""
            binding.tvExEn.text = word.exEn ?: ""
            binding.btnUnmark.setOnClickListener { onUnmark(word) }
        }
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): WordViewHolder {
        val binding = ItemDifficultWordBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return WordViewHolder(binding)
    }

    override fun onBindViewHolder(holder: WordViewHolder, position: Int) {
        holder.bind(getItem(position))
    }

    class DiffCallback : DiffUtil.ItemCallback<WordEntity>() {
        override fun areItemsTheSame(old: WordEntity, new: WordEntity) = old.id == new.id
        override fun areContentsTheSame(old: WordEntity, new: WordEntity) = old == new
    }
}
