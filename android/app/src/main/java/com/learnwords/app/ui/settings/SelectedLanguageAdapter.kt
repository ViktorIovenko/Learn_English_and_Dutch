package com.learnwords.app.ui.settings

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.learnwords.app.data.api.LanguageOption
import com.learnwords.app.databinding.ItemSelectedLanguageBinding

class SelectedLanguageAdapter(
    private val onMoveUp: (String) -> Unit,
    private val onMoveDown: (String) -> Unit,
    private val onRemove: (String) -> Unit
) : RecyclerView.Adapter<SelectedLanguageAdapter.LangViewHolder>() {

    private var items: List<SelectedLangItem> = emptyList()

    data class SelectedLangItem(
        val code: String,
        val name: String,
        val flag: String?,
        val priority: Int,
        val isFirst: Boolean,
        val isLast: Boolean
    )

    fun setItems(codes: List<String>, options: List<LanguageOption>) {
        items = codes.mapIndexed { index, code ->
            val opt = options.find { it.code == code }
            SelectedLangItem(
                code = code,
                name = opt?.name ?: code.uppercase(),
                flag = opt?.flag,
                priority = index + 1,
                isFirst = index == 0,
                isLast = index == codes.lastIndex
            )
        }
        notifyDataSetChanged()
    }

    inner class LangViewHolder(private val binding: ItemSelectedLanguageBinding) :
        RecyclerView.ViewHolder(binding.root) {

        fun bind(item: SelectedLangItem) {
            binding.tvPriority.text = "${item.priority}."
            binding.tvFlag.text = item.flag ?: ""
            binding.tvName.text = item.name
            binding.tvCode.text = item.code.uppercase()
            binding.btnUp.isEnabled = !item.isFirst
            binding.btnDown.isEnabled = !item.isLast
            binding.btnUp.setOnClickListener { onMoveUp(item.code) }
            binding.btnDown.setOnClickListener { onMoveDown(item.code) }
            binding.btnRemove.setOnClickListener { onRemove(item.code) }
        }
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): LangViewHolder {
        val binding = ItemSelectedLanguageBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return LangViewHolder(binding)
    }

    override fun onBindViewHolder(holder: LangViewHolder, position: Int) {
        holder.bind(items[position])
    }

    override fun getItemCount() = items.size
}
