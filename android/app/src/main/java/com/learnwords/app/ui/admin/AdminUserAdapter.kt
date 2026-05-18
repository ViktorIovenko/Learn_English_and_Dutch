package com.learnwords.app.ui.admin

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.google.android.material.button.MaterialButton
import com.learnwords.app.R
import com.learnwords.app.data.api.AdminUserDto
import java.text.SimpleDateFormat
import java.util.*

class AdminUserAdapter(
    private val onGrant: (AdminUserDto) -> Unit,
    private val onRevoke: (AdminUserDto) -> Unit
) : ListAdapter<AdminUserDto, AdminUserAdapter.VH>(DIFF) {

    inner class VH(view: View) : RecyclerView.ViewHolder(view) {
        val tvUserId: TextView = view.findViewById(R.id.tv_user_id)
        val tvName: TextView = view.findViewById(R.id.tv_name)
        val tvStatus: TextView = view.findViewById(R.id.tv_status)
        val btnGrant: MaterialButton = view.findViewById(R.id.btn_grant)
        val btnRevoke: MaterialButton = view.findViewById(R.id.btn_revoke)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): VH {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_admin_user, parent, false)
        return VH(view)
    }

    override fun onBindViewHolder(holder: VH, position: Int) {
        val user = getItem(position)

        holder.tvUserId.text = user.userId
        val name = listOf(user.firstName, user.username).filter { it.isNotBlank() }.joinToString(" / @")
        holder.tvName.text = name.ifBlank { "—" }

        when {
            user.isUnlimited -> {
                holder.tvStatus.text = "Безлимитный"
                holder.tvStatus.setTextColor(0xFF2E7D32.toInt())
            }
            user.status == "active" -> {
                val exp = user.currentPeriodEndsAt?.let { formatDate(it) } ?: "∞"
                holder.tvStatus.text = "Активна до $exp"
                holder.tvStatus.setTextColor(0xFF1565C0.toInt())
            }
            user.status == "trial" -> {
                val exp = user.trialEndsAt?.let { formatDate(it) } ?: "?"
                val now = System.currentTimeMillis()
                if ((user.trialEndsAt ?: 0) > now) {
                    holder.tvStatus.text = "Trial до $exp"
                    holder.tvStatus.setTextColor(0xFFE65100.toInt())
                } else {
                    holder.tvStatus.text = "Trial истёк"
                    holder.tvStatus.setTextColor(0xFFC62828.toInt())
                }
            }
            else -> {
                holder.tvStatus.text = "Нет подписки"
                holder.tvStatus.setTextColor(0xFF757575.toInt())
            }
        }

        holder.btnGrant.setOnClickListener { onGrant(user) }
        holder.btnRevoke.isEnabled = user.isUnlimited || user.status == "active"
        holder.btnRevoke.setOnClickListener { onRevoke(user) }
    }

    private fun formatDate(ms: Long): String {
        return SimpleDateFormat("dd.MM.yy", Locale.getDefault()).format(Date(ms))
    }

    companion object {
        private val DIFF = object : DiffUtil.ItemCallback<AdminUserDto>() {
            override fun areItemsTheSame(a: AdminUserDto, b: AdminUserDto) = a.userId == b.userId
            override fun areContentsTheSame(a: AdminUserDto, b: AdminUserDto) = a == b
        }
    }
}
