package com.learnwords.app.ui.upload

import android.text.Editable
import android.text.TextWatcher
import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.learnwords.app.databinding.ItemWordPreviewBinding

class WordPreviewAdapter : RecyclerView.Adapter<WordPreviewAdapter.WordViewHolder>() {

    data class WordRow(
        var nl: String = "",
        var en: String = "",
        var ru: String = "",
        var exNl: String = "",
        var exEn: String = "",
        var exRu: String = ""
    )

    private val items = mutableListOf<WordRow>()

    fun setItems(rows: List<WordRow>) {
        items.clear()
        items.addAll(rows)
        notifyDataSetChanged()
    }

    fun addRow() {
        items.add(WordRow())
        notifyItemInserted(items.lastIndex)
    }

    fun getItems(): List<Map<String, String?>> = items.map { row ->
        mapOf(
            "nl" to row.nl.ifBlank { null },
            "en" to row.en.ifBlank { null },
            "ru" to row.ru.ifBlank { null },
            "ex_nl" to row.exNl.ifBlank { null },
            "ex_en" to row.exEn.ifBlank { null },
            "ex_ru" to row.exRu.ifBlank { null }
        )
    }

    inner class WordViewHolder(private val binding: ItemWordPreviewBinding) :
        RecyclerView.ViewHolder(binding.root) {

        fun bind(row: WordRow, position: Int) {
            binding.etNl.setText(row.nl)
            binding.etEn.setText(row.en)
            binding.etRu.setText(row.ru)
            binding.etExNl.setText(row.exNl)
            binding.etExEn.setText(row.exEn)
            binding.etExRu.setText(row.exRu)

            binding.etNl.addTextChangedListener(object : TextWatcher {
                override fun afterTextChanged(s: Editable?) { items[position].nl = s.toString() }
                override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
                override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {}
            })
            binding.etEn.addTextChangedListener(object : TextWatcher {
                override fun afterTextChanged(s: Editable?) { items[position].en = s.toString() }
                override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
                override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {}
            })
            binding.etRu.addTextChangedListener(object : TextWatcher {
                override fun afterTextChanged(s: Editable?) { items[position].ru = s.toString() }
                override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
                override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {}
            })

            binding.btnDelete.setOnClickListener {
                items.removeAt(position)
                notifyItemRemoved(position)
                notifyItemRangeChanged(position, items.size)
            }
        }
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): WordViewHolder {
        val binding = ItemWordPreviewBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return WordViewHolder(binding)
    }

    override fun onBindViewHolder(holder: WordViewHolder, position: Int) {
        holder.bind(items[position], position)
    }

    override fun getItemCount() = items.size
}
