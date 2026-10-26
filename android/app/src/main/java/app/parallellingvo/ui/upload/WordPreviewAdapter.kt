package app.parallellingvo.ui.upload

import android.view.LayoutInflater
import android.view.ViewGroup
import android.widget.LinearLayout
import androidx.core.widget.doAfterTextChanged
import androidx.recyclerview.widget.RecyclerView
import app.parallellingvo.R
import app.parallellingvo.data.api.WordDto
import app.parallellingvo.databinding.ItemWordPreviewBinding
import com.google.android.material.textfield.TextInputEditText
import com.google.android.material.textfield.TextInputLayout
import com.google.gson.Gson
import java.util.Locale

class WordPreviewAdapter : RecyclerView.Adapter<WordPreviewAdapter.WordViewHolder>() {
    private val languages = listOf("nl", "en", "ru", "de", "fr", "es", "it", "pt", "pl", "uk")
    private val items = mutableListOf<MutableMap<String, String?>>()
    private val gson = Gson()

    fun setItems(words: List<WordDto>) {
        items.clear()
        items.addAll(words.map { word ->
            gson.toJsonTree(word).asJsonObject.entrySet()
                .filter { (key, value) ->
                    (key in languages || key.removePrefix("ex_") in languages) && !value.isJsonNull
                }
                .associate { (key, value) -> key to (value.asString as String?) }.toMutableMap()
        })
        notifyDataSetChanged()
    }

    fun getItems(): List<Map<String, String?>> = items.map { it.toMap() }

    inner class WordViewHolder(private val binding: ItemWordPreviewBinding) :
        RecyclerView.ViewHolder(binding.root) {
        fun bind(row: MutableMap<String, String?>) {
            binding.wordFields.removeAllViews()
            for (language in languages.filter { !row[it].isNullOrBlank() }) {
                for (key in listOf(language, "ex_$language")) {
                    val context = binding.root.context
                    val label = language.uppercase(Locale.ROOT) +
                        if (key == language) "" else " · " + context.getString(R.string.word_preview_example)
                    val field = TextInputLayout(context).apply {
                        hint = label
                        boxBackgroundMode = TextInputLayout.BOX_BACKGROUND_OUTLINE
                        layoutParams = LinearLayout.LayoutParams(
                            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT
                        )
                    }
                    field.addView(TextInputEditText(context).apply {
                        setText(row[key].orEmpty())
                        doAfterTextChanged { row[key] = it?.toString()?.ifBlank { null } }
                    })
                    binding.wordFields.addView(field)
                }
            }
            binding.btnDelete.setOnClickListener {
                val position = bindingAdapterPosition
                if (position != RecyclerView.NO_POSITION) {
                    items.removeAt(position)
                    notifyItemRemoved(position)
                }
            }
        }
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): WordViewHolder =
        WordViewHolder(ItemWordPreviewBinding.inflate(LayoutInflater.from(parent.context), parent, false))

    override fun onBindViewHolder(holder: WordViewHolder, position: Int) = holder.bind(items[position])

    override fun getItemCount() = items.size
}
