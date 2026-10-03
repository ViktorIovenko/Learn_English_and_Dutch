package com.learnwords.app.ui.learn

import android.view.LayoutInflater
import android.content.ClipData
import android.view.View
import android.view.ViewGroup
import androidx.core.content.ContextCompat
import androidx.recyclerview.widget.RecyclerView
import com.learnwords.app.R
import com.learnwords.app.databinding.ItemAnswerSlotBinding
import kotlin.math.roundToInt

class AnswerSlotAdapter(
    private val onSlotClick: (Int) -> Unit
) : RecyclerView.Adapter<AnswerSlotAdapter.SlotViewHolder>() {

    private var slots: List<Char?> = emptyList()
    private var checkResult: CheckResult = CheckResult.NONE
    private var itemSizeDp: Int = 42
    private var itemHeightDp: Int = 50
    private var textSizeSp: Float = 19f

    fun setSlots(slots: List<Char?>, checkResult: CheckResult) {
        this.slots = slots
        this.checkResult = checkResult
        val count = slots.size
        itemSizeDp = when {
            count >= 18 -> 28
            count >= 14 -> 32
            count >= 11 -> 34
            else -> 42
        }
        itemHeightDp = when {
            count >= 18 -> 34
            count >= 14 -> 38
            count >= 11 -> 40
            else -> 50
        }
        textSizeSp = when {
            count >= 18 -> 14f
            count >= 14 -> 16f
            count >= 11 -> 16f
            else -> 19f
        }
        notifyDataSetChanged()
    }

    inner class SlotViewHolder(private val binding: ItemAnswerSlotBinding) :
        RecyclerView.ViewHolder(binding.root) {

        fun bind(char: Char?, index: Int) {
            val density = binding.root.resources.displayMetrics.density
            binding.root.layoutParams = binding.root.layoutParams.apply {
                width = (itemSizeDp * density).roundToInt()
                height = (itemHeightDp * density).roundToInt()
            }
            binding.tvLetter.textSize = textSizeSp
            binding.tvLetter.text = char?.toString()?.uppercase() ?: ""

            val context = binding.root.context
            val bgColor = when {
                char == null -> ContextCompat.getColor(context, R.color.colorSlotEmpty)
                checkResult == CheckResult.CORRECT -> ContextCompat.getColor(context, R.color.colorGameCorrect)
                checkResult == CheckResult.MASTERED -> ContextCompat.getColor(context, R.color.colorGameMastered)
                checkResult == CheckResult.WRONG -> ContextCompat.getColor(context, R.color.colorGameWrong)
                else -> ContextCompat.getColor(context, R.color.colorPrimary)
            }
            binding.root.setCardBackgroundColor(bgColor)

            if (char != null && checkResult == CheckResult.NONE) {
                binding.root.setOnClickListener { onSlotClick(index) }
                binding.root.setOnLongClickListener {
                    binding.root.startDragAndDrop(
                        ClipData.newPlainText("slot-index", index.toString()),
                        View.DragShadowBuilder(binding.root),
                        LetterDragPayload(slotIndex = index),
                        0
                    )
                    true
                }
            } else {
                binding.root.setOnClickListener(null)
                binding.root.setOnLongClickListener(null)
            }
        }
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): SlotViewHolder {
        val binding = ItemAnswerSlotBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return SlotViewHolder(binding)
    }

    override fun onBindViewHolder(holder: SlotViewHolder, position: Int) {
        holder.bind(slots.getOrNull(position), position)
    }

    override fun getItemCount() = slots.size
}
