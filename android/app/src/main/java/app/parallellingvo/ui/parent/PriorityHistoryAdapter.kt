package app.parallellingvo.ui.parent

import android.view.View
import android.view.ViewGroup
import android.widget.LinearLayout
import android.widget.TextView
import androidx.core.content.ContextCompat
import androidx.recyclerview.widget.RecyclerView
import app.parallellingvo.R
import app.parallellingvo.data.api.ChildPriorityHistoryDto

class PriorityHistoryAdapter(
    private val formatEntry: (ChildPriorityHistoryDto) -> String
) : RecyclerView.Adapter<PriorityHistoryAdapter.Holder>() {
    private var owner: String? = null
    private var entries: List<ChildPriorityHistoryDto> = emptyList()
    private var pages: List<List<ChildPriorityHistoryDto>> = emptyList()

    fun setHistory(childId: String, history: List<ChildPriorityHistoryDto>): Boolean {
        if (owner == childId && entries == history) return false
        owner = childId
        entries = history.toList()
        pages = history.chunked(10)
        notifyDataSetChanged()
        return true
    }

    class Holder(val column: LinearLayout) : RecyclerView.ViewHolder(column)

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): Holder {
        return Holder(LinearLayout(parent.context).apply {
            orientation = LinearLayout.VERTICAL
            layoutParams = RecyclerView.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)
        })
    }

    override fun onBindViewHolder(holder: Holder, position: Int) {
        val context = holder.column.context
        val density = context.resources.displayMetrics.density
        val spacing = (12 * density).toInt()
        holder.column.removeAllViews()
        pages[position].forEachIndexed { index, entry ->
            if (index > 0) holder.column.addView(View(context).apply {
                setBackgroundColor(ContextCompat.getColor(context, R.color.colorDivider))
                layoutParams = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, (density).toInt().coerceAtLeast(1))
            })
            holder.column.addView(TextView(context).apply {
                text = formatEntry(entry)
                textSize = 14f
                setTextColor(ContextCompat.getColor(context, R.color.colorTextMedium))
                setLineSpacing(3 * density, 1f)
                setPadding(0, spacing, spacing, spacing)
                layoutParams = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)
            })
        }
    }

    override fun getItemCount() = pages.size
}
