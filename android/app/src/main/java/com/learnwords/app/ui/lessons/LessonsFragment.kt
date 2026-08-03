package com.learnwords.app.ui.lessons

import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.*
import androidx.appcompat.app.AlertDialog
import androidx.core.os.bundleOf
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import com.learnwords.app.LearnWordsApp
import com.learnwords.app.R
import com.learnwords.app.databinding.FragmentLessonsBinding
import com.learnwords.app.utils.gone
import com.learnwords.app.utils.secToMinSec
import com.learnwords.app.utils.toast
import com.learnwords.app.utils.visible
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import java.time.LocalDate

class LessonsFragment : Fragment() {

    private var _binding: FragmentLessonsBinding? = null
    private val binding get() = _binding!!
    private val viewModel: LessonsViewModel by viewModels()
    private lateinit var adapter: LessonAdapter

    // Таймер для обычного аккаунта: обратный отсчёт дневной цели в минутах,
    // тот же принцип и то же хранилище (prefs.timerSeconds/timerDate), что и
    // на экране урока (LearnFragment) и в веб-версии (счётчик "10:00" → "0:00",
    // сохраняется на весь день, не сбрасывается при переходах между экранами).
    // Для детского аккаунта вместо него показывается "сделано / цель"
    // (см. tv_today_summary в тулбаре) — как и на вебе (child-daily-goal).
    private val timerHandler = Handler(Looper.getMainLooper())
    private var timerSeconds = 0
    private var timerGoalMinutes = 0
    private var timerRunning = true
    private val timerRunnable = object : Runnable {
        override fun run() {
            if (timerRunning && timerSeconds > 0) {
                timerSeconds--
                if (timerSeconds == 0) timerRunning = false
                renderTodaySummary()
                saveTimerState()
            }
            if (timerRunning && timerSeconds > 0) {
                timerHandler.postDelayed(this, 1000L)
            }
        }
    }

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentLessonsBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        adapter = LessonAdapter(
            onLessonClick = { lesson ->
                viewModel.markLessonOpened(lesson.lesson)
                findNavController().navigate(
                    R.id.action_lessonsFragment_to_learnFragment,
                    bundleOf("lesson" to lesson.lesson)
                )
            },
            onHideToggle = { lesson ->
                viewModel.toggleHidden(lesson.lesson, lesson.hidden)
            },
            onSelectForDelete = { lesson ->
                viewModel.toggleDeleteSelection(lesson.lesson)
            }
        )
        binding.rvLessons.adapter = adapter

        binding.swipeRefresh.setOnRefreshListener { viewModel.refresh() }

        binding.btnDeleteMode.setOnClickListener {
            if (viewModel.uiState.value.isDeleteMode) {
                showDeleteConfirmation()
            } else {
                viewModel.enterDeleteMode()
            }
        }

        binding.btnCancelDelete.setOnClickListener {
            viewModel.exitDeleteMode()
        }

        binding.btnTodayPause.setOnClickListener {
            timerRunning = !timerRunning
            timerHandler.removeCallbacks(timerRunnable)
            if (timerRunning && lifecycle.currentState.isAtLeast(Lifecycle.State.RESUMED)) {
                timerHandler.post(timerRunnable)
            }
            renderTodaySummary()
            saveTimerState()
        }

        binding.btnTodayRestart.setOnClickListener {
            timerSeconds = timerGoalMinutes * 60
            timerRunning = true
            timerHandler.removeCallbacks(timerRunnable)
            if (lifecycle.currentState.isAtLeast(Lifecycle.State.RESUMED)) {
                timerHandler.post(timerRunnable)
            }
            renderTodaySummary()
            saveTimerState()
        }

        viewLifecycleOwner.lifecycleScope.launch {
            viewModel.lessons.collectLatest { lessons ->
                val binding = _binding ?: return@collectLatest
                val state = viewModel.uiState.value
                val items = lessons.map { entity ->
                    LessonAdapter.LessonItem(
                        entity = entity,
                        isSelected = entity.lesson in state.selectedForDelete,
                        isDeleteMode = state.isDeleteMode
                    )
                }
                adapter.submitList(items)
                binding.tvEmpty.visibility = if (lessons.isEmpty()) View.VISIBLE else View.GONE
            }
        }

        viewLifecycleOwner.lifecycleScope.launch {
            viewModel.uiState.collectLatest { state ->
                val binding = _binding ?: return@collectLatest
                binding.swipeRefresh.isRefreshing = state.isLoading
                binding.tvLearningStreak.text = getString(R.string.learning_streak_value, state.learningStreakDays)
                if (state.isChild) {
                    timerHandler.removeCallbacks(timerRunnable)
                    timerGoalMinutes = 0
                } else {
                    ensureStandardTimer(state.dailyGoalMinutes)
                }
                renderTodaySummary()

                if (state.isDeleteMode) {
                    binding.btnDeleteMode.text = getString(R.string.delete_lessons_count, state.selectedForDelete.size)
                    binding.btnCancelDelete.visible()
                } else {
                    binding.btnDeleteMode.text = getString(R.string.delete_lessons)
                    binding.btnCancelDelete.gone()
                }

                // Re-submit list when delete mode or selection changes
                val lessons = viewModel.lessons.value
                val items = lessons.map { entity ->
                    LessonAdapter.LessonItem(
                        entity = entity,
                        isSelected = entity.lesson in state.selectedForDelete,
                        isDeleteMode = state.isDeleteMode
                    )
                }
                adapter.submitList(items)

                state.error?.let {
                    requireContext().toast(it)
                    viewModel.clearError()
                }
            }
        }
    }

    private fun ensureStandardTimer(goalMinutes: Int) {
        if (goalMinutes <= 0 || timerGoalMinutes == goalMinutes) return
        timerGoalMinutes = goalMinutes
        viewLifecycleOwner.lifecycleScope.launch {
            val prefs = LearnWordsApp.instance.preferencesManager
            val savedDate = prefs.timerDate.first()
            val savedSeconds = prefs.timerSeconds.first().toInt()
            val hasSavedState = savedDate == LocalDate.now().toString() &&
                savedSeconds in 0..goalMinutes * 60
            timerSeconds = if (hasSavedState) {
                savedSeconds
            } else goalMinutes * 60
            timerRunning = timerSeconds > 0 && (!hasSavedState || prefs.timerRunning.first())
            renderTodaySummary()
            timerHandler.removeCallbacks(timerRunnable)
            if (lifecycle.currentState.isAtLeast(Lifecycle.State.RESUMED) && timerRunning) {
                timerHandler.post(timerRunnable)
            }
        }
    }

    private fun saveTimerState() {
        if (timerGoalMinutes <= 0) return
        lifecycleScope.launch {
            LearnWordsApp.instance.preferencesManager.saveTimerState(
                timerSeconds.toLong(), LocalDate.now().toString(), timerRunning
            )
        }
    }

    private fun renderTodaySummary() {
        val binding = _binding ?: return
        val state = viewModel.uiState.value
        if (state.isChild) {
            binding.tvTodaySummary.text = getString(R.string.today_correct_words_value, state.todayCorrectWords, state.todayGoal)
            binding.btnTodayPause.gone()
            binding.btnTodayRestart.gone()
        } else {
            binding.tvTodaySummary.text = getString(R.string.today_timer_value, timerSeconds.toLong().secToMinSec())
            binding.btnTodayPause.visible()
            binding.btnTodayRestart.visible()
            binding.btnTodayPause.setImageResource(if (timerRunning) R.drawable.ic_pause_24 else R.drawable.ic_play_24)
        }
    }

    override fun onResume() {
        super.onResume()
        // Форсируем перечитывание сохранённого состояния (могла смениться дата).
        timerGoalMinutes = 0
        if (!viewModel.uiState.value.isChild) {
            ensureStandardTimer(viewModel.uiState.value.dailyGoalMinutes)
        }
    }

    override fun onPause() {
        timerHandler.removeCallbacks(timerRunnable)
        saveTimerState()
        super.onPause()
    }

    private fun showDeleteConfirmation() {
        val count = viewModel.uiState.value.selectedForDelete.size
        if (count == 0) {
            requireContext().toast(getString(R.string.select_lessons_to_delete))
            return
        }
        AlertDialog.Builder(requireContext())
            .setTitle(R.string.delete_lessons)
            .setMessage(getString(R.string.delete_lessons_message, count))
            .setPositiveButton(R.string.delete) { _, _ -> viewModel.deleteSelected() }
            .setNegativeButton(R.string.cancel) { _, _ -> viewModel.exitDeleteMode() }
            .show()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        timerHandler.removeCallbacks(timerRunnable)
        _binding = null
    }
}
