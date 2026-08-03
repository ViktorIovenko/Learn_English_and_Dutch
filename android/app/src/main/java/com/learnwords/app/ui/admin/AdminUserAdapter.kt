package com.learnwords.app.ui.admin

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import android.widget.LinearLayout
import androidx.core.content.ContextCompat
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.google.android.material.button.MaterialButton
import com.learnwords.app.R
import com.learnwords.app.data.api.AdminUserDto
import com.learnwords.app.data.api.AdminFamilyRelationDto
import java.text.SimpleDateFormat
import java.util.*

class AdminUserAdapter(
    private val onGrant: (AdminUserDto) -> Unit,
    private val onRevoke: (AdminUserDto) -> Unit,
    private val onUnlinkFamily: (AdminFamilyRelationDto) -> Unit,
    private val onResetTts: (AdminUserDto) -> Unit,
    private val onResetTranslation: (AdminUserDto) -> Unit
) : ListAdapter<AdminUserDto, AdminUserAdapter.VH>(DIFF) {

    inner class VH(view: View) : RecyclerView.ViewHolder(view) {
        val tvUserId: TextView = view.findViewById(R.id.tv_user_id)
        val tvName: TextView = view.findViewById(R.id.tv_name)
        val tvStatus: TextView = view.findViewById(R.id.tv_status)
        val tvAccountType: TextView = view.findViewById(R.id.tv_account_type)
        val familyRelations: LinearLayout = view.findViewById(R.id.family_relations_container)
        val tvTtsUsage: TextView = view.findViewById(R.id.tv_tts_usage)
        val tvTranslationUsage: TextView = view.findViewById(R.id.tv_translation_usage)
        val btnGrant: MaterialButton = view.findViewById(R.id.btn_grant)
        val btnRevoke: MaterialButton = view.findViewById(R.id.btn_revoke)
        val btnResetTts: MaterialButton = view.findViewById(R.id.btn_reset_tts)
        val btnResetTranslation: MaterialButton = view.findViewById(R.id.btn_reset_translation)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): VH {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_admin_user, parent, false)
        return VH(view)
    }

    override fun onBindViewHolder(holder: VH, position: Int) {
        val user = getItem(position)
        val context = holder.itemView.context

        holder.tvUserId.text = user.userId
        val name = listOf(user.firstName, user.username).filter { it.isNotBlank() }.joinToString(" / @")
        holder.tvName.text = name.ifBlank { "—" }

        holder.tvAccountType.text = context.getString(
            if (user.accountType == "child") R.string.admin_account_child else R.string.admin_account_standard
        )
        holder.familyRelations.removeAllViews()
        user.familyRelations.forEach { relation ->
            holder.familyRelations.addView(MaterialButton(context).apply {
                text = context.getString(
                    if (relation.direction == "parent_of") R.string.admin_relation_child
                    else R.string.admin_relation_parent,
                    relation.displayName
                )
                textSize = 11f
                isAllCaps = false
                setOnClickListener { onUnlinkFamily(relation) }
            })
        }
        holder.tvTtsUsage.text = context.getString(
            R.string.tts_usage_user,
            user.ttsTotalRequests,
            user.ttsSuccessfulRequests,
            user.ttsFailedRequests
        )
        holder.tvTranslationUsage.text = context.getString(
            R.string.translation_usage_user,
            user.translationTotalTokens,
            user.translationPromptTokens,
            user.translationCompletionTokens,
            user.translationSuccessfulRequests,
            user.translationFailedRequests
        )

        when {
            user.isUnlimited -> {
                holder.tvStatus.text = context.getString(R.string.unlimited)
                holder.tvStatus.setTextColor(ContextCompat.getColor(context, R.color.colorCorrect))
            }
            user.status == "active" -> {
                val exp = user.currentPeriodEndsAt?.let { formatDate(it) } ?: "∞"
                holder.tvStatus.text = context.getString(R.string.active_until, exp)
                holder.tvStatus.setTextColor(ContextCompat.getColor(context, R.color.colorStatusActive))
            }
            user.status == "trial" -> {
                val exp = user.trialEndsAt?.let { formatDate(it) } ?: "?"
                val now = System.currentTimeMillis()
                if ((user.trialEndsAt ?: 0) > now) {
                    holder.tvStatus.text = context.getString(R.string.trial_until, exp)
                    holder.tvStatus.setTextColor(ContextCompat.getColor(context, R.color.colorStatusTrial))
                } else {
                    holder.tvStatus.text = context.getString(R.string.trial_expired)
                    holder.tvStatus.setTextColor(ContextCompat.getColor(context, R.color.colorWrong))
                }
            }
            else -> {
                holder.tvStatus.text = context.getString(R.string.no_subscription)
                holder.tvStatus.setTextColor(ContextCompat.getColor(context, R.color.colorTextSecondary))
            }
        }

        holder.btnGrant.setOnClickListener { onGrant(user) }
        holder.btnRevoke.isEnabled = user.isUnlimited || user.status == "active"
        holder.btnRevoke.setOnClickListener { onRevoke(user) }
        holder.btnResetTts.setOnClickListener { onResetTts(user) }
        holder.btnResetTranslation.setOnClickListener { onResetTranslation(user) }
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
