package com.learnwords.app.ui.learn

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.learnwords.app.databinding.ItemLetterTileBinding
import kotlin.math.roundToInt

class LetterTileAdapter(
    private val onTileClick: (Int) -> Unit
) : RecyclerView.Adapter<LetterTileAdapter.TileViewHolder>() {

    private var letters: List<Char> = emptyList()
    private var usedIndices: Set<Int> = emptySet()
    private var itemSizeDp: Int = 48
    private var textSizeSp: Float = 20f

    fun setLetters(letters: List<Char>, used: Set<Int>) {
        this.letters = letters
        this.usedIndices = used
        val count = letters.size
        itemSizeDp = when {
            count >= 18 -> 34
            count >= 14 -> 38
            count >= 11 -> 42
            else -> 48
        }
        textSizeSp = when {
            count >= 18 -> 16f
            count >= 14 -> 17f
            count >= 11 -> 18f
            else -> 20f
        }
        notifyDataSetChanged()
    }

    inner class TileViewHolder(private val binding: ItemLetterTileBinding) :
        RecyclerView.ViewHolder(binding.root) {

        fun bind(letter: Char, index: Int) {
            val density = binding.root.resources.displayMetrics.density
            binding.root.layoutParams = binding.root.layoutParams.apply {
                width = (itemSizeDp * density).roundToInt()
                height = (itemSizeDp * density).roundToInt()
            }
            binding.tvLetter.textSize = textSizeSp
            binding.tvLetter.text = letter.toString().uppercase()
            val isUsed = index in usedIndices
            binding.root.alpha = if (isUsed) 0.2f else 1.0f
            binding.root.isEnabled = !isUsed
            binding.root.setOnClickListener {
                if (!isUsed) onTileClick(index)
            }
        }
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): TileViewHolder {
        val binding = ItemLetterTileBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return TileViewHolder(binding)
    }

    override fun onBindViewHolder(holder: TileViewHolder, position: Int) {
        holder.bind(letters[position], position)
    }

    override fun getItemCount() = letters.size
}
