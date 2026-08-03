package com.learnwords.app.ui.parent

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.AdapterView
import android.widget.ArrayAdapter
import androidx.appcompat.app.AlertDialog
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.findNavController
import com.learnwords.app.MainActivity
import com.learnwords.app.R
import com.learnwords.app.data.api.ChildDashboardDto
import com.learnwords.app.databinding.FragmentParentDashboardBinding
import com.learnwords.app.utils.toast
import java.text.DateFormat
import java.util.Date
import kotlinx.coroutines.launch

class ParentDashboardFragment : Fragment() {
    private var _binding: FragmentParentDashboardBinding? = null
    private val binding get() = _binding!!
    private val viewModel: ParentDashboardViewModel by viewModels()
    private var ignoreSelections = false
    private lateinit var childrenAdapter: ChildDashboardAdapter

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentParentDashboardBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        binding.swipeRefresh.setOnRefreshListener { viewModel.refresh() }
        childrenAdapter = ChildDashboardAdapter(
            onSelect = { viewModel.selectChild(it.userId) },
            onDisconnect = { confirmDisconnect(it) }
        )
        binding.rvChildren.adapter = childrenAdapter
        binding.spinnerPeriod.adapter = ArrayAdapter(
            requireContext(),
            android.R.layout.simple_spinner_item,
            listOf(getString(R.string.parent_period_7), getString(R.string.parent_period_30), getString(R.string.parent_period_90))
        ).apply { setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item) }
        binding.spinnerPeriod.onItemSelectedListener = object : AdapterView.OnItemSelectedListener {
            override fun onItemSelected(parent: AdapterView<*>?, view: View?, position: Int, id: Long) {
                if (!ignoreSelections) viewModel.setDays(listOf(7, 30, 90)[position])
            }
            override fun onNothingSelected(parent: AdapterView<*>?) = Unit
        }
        binding.btnConnectChild.setOnClickListener { findNavController().navigate(R.id.languageSettingsFragment) }
        binding.btnSavePriority.setOnClickListener {
            val state = viewModel.uiState.value
            val child = state.children.firstOrNull { it.userId == state.selectedChildId }
                ?: return@setOnClickListener
            val index = binding.spinnerPriorityLesson.selectedItemPosition
            viewModel.setPriorityLesson(child.availableLessons.getOrNull(index - 1)?.lesson.orEmpty())
        }

        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.uiState.collect { render(it) }
            }
        }
    }

    private fun render(state: ParentDashboardUiState) {
        binding.swipeRefresh.isRefreshing = state.isLoading
        binding.progressBar.visibility = if (state.isLoading && state.children.isEmpty()) View.VISIBLE else View.GONE
        if (state.accessRevoked) {
            (activity as? MainActivity)?.setParentNavigationVisible(false)
            if (findNavController().currentDestination?.id == R.id.parentDashboardFragment) {
                findNavController().navigate(R.id.lessonsFragment)
            }
            return
        }
        state.error?.let {
            requireContext().toast(it, long = true)
            viewModel.clearError()
        }
        val selectedIndex = state.children.indexOfFirst { it.userId == state.selectedChildId }.coerceAtLeast(0)
        childrenAdapter.submitList(state.children.map { ChildDashboardAdapter.Item(it, it.userId == state.selectedChildId) })
        ignoreSelections = true
        binding.spinnerPeriod.setSelection(listOf(7, 30, 90).indexOf(state.days).coerceAtLeast(1), false)
        ignoreSelections = false
        val child = state.children.getOrNull(selectedIndex)
        binding.content.visibility = if (child == null) View.GONE else View.VISIBLE
        if (child != null) renderChild(child)
    }

    private fun renderChild(child: ChildDashboardDto) {
        val summary = child.summary
        val priorityLabels = listOf(getString(R.string.parent_priority_none)) + child.availableLessons.map { lesson ->
            if (lesson.lessonIndex > 0) "${lesson.lessonIndex}. ${lesson.lessonTitle.ifBlank { lesson.lesson }}"
            else lesson.lessonTitle.ifBlank { lesson.lesson }
        }
        binding.spinnerPriorityLesson.adapter = ArrayAdapter(
            requireContext(),
            android.R.layout.simple_spinner_item,
            priorityLabels
        ).apply { setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item) }
        binding.spinnerPriorityLesson.setSelection(
            child.availableLessons.indexOfFirst { it.lesson == child.priorityLesson } + 1,
            false
        )
        binding.tvPriorityStatus.text = if (child.priorityLesson.isBlank()) {
            getString(R.string.parent_priority_not_set)
        } else {
            getString(R.string.parent_priority_current, child.priorityLesson)
        }
        binding.tvPriorityHistory.text = if (child.priorityHistory.isEmpty()) {
            getString(R.string.parent_priority_history_empty)
        } else {
            child.priorityHistory.joinToString("\n\n") { item ->
                val started = DateFormat.getDateTimeInstance().format(Date(item.startedAt))
                val ended = if (item.isActive || item.endedAt == null) {
                    getString(R.string.parent_priority_now)
                } else {
                    DateFormat.getDateTimeInstance().format(Date(item.endedAt))
                }
                getString(
                    R.string.parent_priority_history_item,
                    item.lesson,
                    started,
                    ended,
                    formatLearningTime(item.durationSeconds)
                )
            }
        }
        val status = when (summary.todayStatusMilestone) {
            5 -> getString(R.string.child_status_5)
            10 -> getString(R.string.child_status_10)
            15 -> getString(R.string.child_status_15)
            20 -> getString(R.string.child_status_20)
            25 -> getString(R.string.child_status_25)
            else -> ""
        }
        binding.valueTodayProgress.text = buildString {
            append("${summary.todayWords} / ${summary.dailyGoal}")
            if (status.isNotBlank()) append(" · $status")
        }
        binding.valueStudiedToday.text = getString(
            if (summary.studiedToday) R.string.common_yes else R.string.common_no
        )
        binding.valueTimeToday.text = formatLearningTime(summary.todayLearningSeconds)
        binding.valueWords.text = summary.wordsCount.toString()
        binding.valueLessons.text = summary.lessonsCount.toString()
        binding.valueLearningDays.text = summary.learningDays.toString()
        binding.valueLearningStreak.text = getString(R.string.learning_streak_value, summary.learningStreakDays)
        binding.valueActiveLessons.text = summary.activeLessons.toString()
        binding.valueCorrect.text = summary.correctAnswers.toString()
        binding.valueSuccess.text = getString(R.string.parent_percent, summary.successRate)
        binding.learningChart.setData(child.daily)
        binding.tvLastActivity.text = if (summary.lastActivityTs > 0) {
            getString(R.string.parent_last_activity_value, DateFormat.getDateTimeInstance().format(Date(summary.lastActivityTs)))
        } else {
            getString(R.string.parent_no_activity)
        }
        val latest = child.latestProgress
        binding.tvLatestProgress.text = if (latest == null) {
            getString(R.string.parent_no_progress)
        } else {
            getString(R.string.parent_latest_value, latest.lesson.ifBlank { "—" }, latest.passed, latest.total)
        }
    }

    private fun formatLearningTime(seconds: Int): String {
        if (seconds <= 0) return getString(R.string.parent_zero_minutes)
        if (seconds < 60) return getString(R.string.parent_less_than_minute)
        val minutes = (seconds / 60.0).toInt().coerceAtLeast(1)
        if (minutes < 60) return getString(R.string.parent_minutes, minutes)
        val hours = minutes / 60
        val rest = minutes % 60
        return if (rest > 0) getString(R.string.parent_hours_minutes, hours, rest)
        else getString(R.string.parent_hours, hours)
    }

    private fun confirmDisconnect(child: ChildDashboardDto) {
        AlertDialog.Builder(requireContext())
            .setTitle(R.string.parent_disconnect)
            .setMessage(getString(R.string.parent_disconnect_confirm, child.displayName))
            .setPositiveButton(R.string.parent_disconnect) { _, _ -> viewModel.unlinkChild(child.userId) }
            .setNegativeButton(android.R.string.cancel, null)
            .show()
    }

    override fun onResume() {
        super.onResume()
        viewModel.refresh()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
