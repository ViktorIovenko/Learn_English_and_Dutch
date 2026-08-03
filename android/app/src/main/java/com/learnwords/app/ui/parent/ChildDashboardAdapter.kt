package com.learnwords.app.ui.parent

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.learnwords.app.R
import com.learnwords.app.data.api.ChildDashboardDto
import com.learnwords.app.databinding.ItemChildDashboardBinding
import java.text.DateFormat
import java.util.Date

class ChildDashboardAdapter(
    private val onSelect: (ChildDashboardDto) -> Unit,
    private val onDisconnect: (ChildDashboardDto) -> Unit
) : ListAdapter<ChildDashboardAdapter.Item, ChildDashboardAdapter.Holder>(DiffCallback()) {

    data class Item(val child: ChildDashboardDto, val selected: Boolean)

    inner class Holder(private val binding: ItemChildDashboardBinding) : RecyclerView.ViewHolder(binding.root) {
        fun bind(item: Item) {
            val context = binding.root.context
            val child = item.child
            binding.tvChildName.text = child.displayName
            binding.tvChildActivity.text = if (child.summary.lastActivityTs > 0) {
                context.getString(R.string.parent_last_activity_value,
                    DateFormat.getDateTimeInstance().format(Date(child.summary.lastActivityTs)))
            } else context.getString(R.string.parent_no_activity)
            val parents = child.parents.mapNotNull { parent ->
                val name = parent.displayName.orEmpty().ifBlank { parent.firstName.orEmpty() }
                val username = parent.username?.takeIf { it.isNotBlank() }?.let { "@$it" }.orEmpty()
                listOf(name, username).filter { it.isNotBlank() }.joinToString(" ").ifBlank { null }
            }
            binding.tvChildParents.text = context.getString(
                R.string.parent_connected_adults,
                parents.ifEmpty { listOf(context.getString(R.string.family_no_connections)) }.joinToString(", ")
            )
            binding.root.isChecked = item.selected
            binding.root.setOnClickListener { onSelect(child) }
            binding.btnDisconnect.setOnClickListener { onDisconnect(child) }
        }
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int) = Holder(
        ItemChildDashboardBinding.inflate(LayoutInflater.from(parent.context), parent, false)
    )
    override fun onBindViewHolder(holder: Holder, position: Int) = holder.bind(getItem(position))

    class DiffCallback : DiffUtil.ItemCallback<Item>() {
        override fun areItemsTheSame(oldItem: Item, newItem: Item) = oldItem.child.userId == newItem.child.userId
        override fun areContentsTheSame(oldItem: Item, newItem: Item) = oldItem == newItem
    }
}
