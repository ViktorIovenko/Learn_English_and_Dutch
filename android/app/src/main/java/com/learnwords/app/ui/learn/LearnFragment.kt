package com.learnwords.app.ui.learn

import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.content.res.ColorStateList
import android.view.*
import android.view.inputmethod.EditorInfo
import android.view.inputmethod.InputMethodManager
import android.content.Context
import android.view.DragEvent
import android.widget.EditText
import android.widget.TextView
import androidx.appcompat.app.AlertDialog
import androidx.core.content.ContextCompat
import androidx.core.os.bundleOf
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import androidx.navigation.fragment.navArgs
import androidx.recyclerview.widget.GridLayoutManager
import com.google.android.flexbox.*
import com.learnwords.app.BuildConfig
import com.learnwords.app.LearnWordsApp
import com.learnwords.app.R
import com.learnwords.app.databinding.FragmentLearnBinding
import com.learnwords.app.databinding.ItemLearnLangRowBinding
import com.learnwords.app.utils.*
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import java.time.LocalDate

class LearnFragment : Fragment() {

    private var _binding: FragmentLearnBinding? = null
    private val binding get() = _binding!!

    private val viewModel: LearnViewModel by viewModels {
        object : ViewModelProvider.Factory {
            override fun <T : androidx.lifecycle.ViewModel> create(modelClass: Class<T>): T {
                val handle = SavedStateHandle(
                    mapOf(
                        "lesson" to (arguments?.getString("lesson") ?: ""),
                        "wordSet" to (arguments?.getString("wordSet") ?: "lesson")
                    )
                )
                @Suppress("UNCHECKED_CAST")
                return LearnViewModel(handle) as T
            }
        }
    }

    private lateinit var letterAdapter: LetterTileAdapter
    private lateinit var slotAdapter: AnswerSlotAdapter
    private val audioPlayer by lazy { AudioPlayer(requireContext()) }
    private var renderedLangs: List<String> = emptyList()
    private var renderedActiveLang: String = ""
    private val timerHandler = Handler(Looper.getMainLooper())
    private val contentSyncRunnable = object : Runnable {
        override fun run() {
            viewModel.refreshLessonContent()
            timerHandler.postDelayed(this, 10_000L)
        }
    }
    private var timerSeconds = 0
    private var timerRunning = false
    private var timerGoalMinutes = 0
    private val timerRunnable = object : Runnable {
        override fun run() {
            if (timerRunning && timerSeconds > 0) {
                timerSeconds--
                if (timerSeconds == 0) timerRunning = false
                renderStandardTimer()
                saveTimerState()
            }
            if (timerRunning && timerSeconds > 0) {
                timerHandler.postDelayed(this, 1000L)
            }
        }
    }

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentLearnBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        // Letter tiles (source)
        letterAdapter = LetterTileAdapter { index ->
            viewModel.placeLetter(index)
        }
        binding.rvLetters.apply {
            val flex = FlexboxLayoutManager(context).apply {
                flexWrap = FlexWrap.WRAP
                justifyContent = JustifyContent.CENTER
            }
            layoutManager = flex
            adapter = letterAdapter
        }

        // Answer slots
        slotAdapter = AnswerSlotAdapter { slotIndex ->
            viewModel.removePlacedLetter(slotIndex)
        }
        binding.rvAnswerSlots.apply {
            val flex = FlexboxLayoutManager(context).apply {
                flexWrap = FlexWrap.WRAP
                justifyContent = JustifyContent.CENTER
            }
            layoutManager = flex
            adapter = slotAdapter
        }
        binding.rvAnswerSlots.setOnDragListener { view, event ->
            when (event.action) {
                DragEvent.ACTION_DRAG_STARTED -> event.localState is LetterDragPayload
                DragEvent.ACTION_DROP -> {
                    val payload = event.localState as? LetterDragPayload ?: return@setOnDragListener false
                    val targetPosition = answerSlotPosition(view, event.x, event.y)
                    when {
                        payload.sourceIndex != null -> viewModel.placeLetterAt(payload.sourceIndex, targetPosition)
                        payload.slotIndex != null -> viewModel.movePlacedLetter(payload.slotIndex, targetPosition)
                    }
                    true
                }
                else -> true
            }
        }

        binding.btnNext.setOnClickListener { viewModel.nextWord() }
        binding.btnPrev.setOnClickListener { viewModel.previousWord() }
        binding.btnDifficult.setOnClickListener { viewModel.toggleDifficult() }
        binding.btnDeleteWord.setOnClickListener { confirmDeleteCurrentWord() }
        binding.btnBack.setOnClickListener { findNavController().navigateUp() }
        binding.btnDailyPause.setOnClickListener {
            timerRunning = !timerRunning
            timerHandler.removeCallbacks(timerRunnable)
            if (timerRunning && lifecycle.currentState.isAtLeast(Lifecycle.State.RESUMED)) {
                timerHandler.post(timerRunnable)
            }
            renderStandardTimer()
            saveTimerState()
        }
        binding.btnDailyRestart.setOnClickListener {
            timerSeconds = timerGoalMinutes * 60
            timerRunning = true
            timerHandler.removeCallbacks(timerRunnable)
            if (lifecycle.currentState.isAtLeast(Lifecycle.State.RESUMED)) {
                timerHandler.post(timerRunnable)
            }
            renderStandardTimer()
            saveTimerState()
        }

        // Навигация между уроками (скрыта в режиме «сложные слова»)
        val showLessonNav = !viewModel.isDifficultMode
        binding.lessonNavRow.visibility = if (showLessonNav) View.VISIBLE else View.GONE
        binding.btnPrevLesson.visibility = if (showLessonNav) View.VISIBLE else View.GONE
        binding.btnNextLesson.visibility = if (showLessonNav) View.VISIBLE else View.GONE
        binding.btnPrevLesson.setOnClickListener { viewModel.goToPrevLesson() }
        binding.btnNextLesson.setOnClickListener { viewModel.goToNextLesson() }

        // Language filter chips
        binding.chipGroupLang.setOnCheckedStateChangeListener { group, checkedIds ->
            val chip = group.findViewById<com.google.android.material.chip.Chip>(checkedIds.firstOrNull() ?: return@setOnCheckedStateChangeListener)
            chip?.tag?.toString()?.let { lang ->
                if (lang != viewModel.uiState.value.activeLang) viewModel.setActiveLang(lang)
            }
        }

        viewLifecycleOwner.lifecycleScope.launch {
            viewModel.uiState.collectLatest { state ->
                renderState(state)
            }
        }

        viewLifecycleOwner.lifecycleScope.launch {
            viewModel.navigateToLesson.collect { lessonTitle ->
                findNavController().navigate(
                    R.id.action_learn_to_learn,
                    bundleOf("lesson" to lessonTitle, "wordSet" to "lesson")
                )
            }
        }
    }

    private fun renderState(state: LearnUiState) {
        if (state.isLoading) {
            binding.progressBar.visible()
            binding.contentGroup.gone()
            return
        }
        binding.progressBar.gone()
        binding.contentGroup.visible()
        binding.dailyGoalRow.visibility = View.VISIBLE
        binding.btnDailyPause.visibility = if (state.isChild) View.GONE else View.VISIBLE
        binding.btnDailyRestart.visibility = if (state.isChild) View.GONE else View.VISIBLE
        if (state.isChild) {
            timerHandler.removeCallbacks(timerRunnable)
            timerGoalMinutes = 0
            binding.tvDailyGoal.text = "${state.todayCount} / ${state.dailyGoal}"
        } else {
            ensureStandardTimer(state.goalValue)
        }
        binding.tvDailyStatus.text = when (state.statusMilestone) {
            5 -> getString(R.string.child_status_5)
            10 -> getString(R.string.child_status_10)
            15 -> getString(R.string.child_status_15)
            20 -> getString(R.string.child_status_20)
            25 -> getString(R.string.child_status_25)
            else -> ""
        }
        if (!state.isChild) binding.tvDailyStatus.text = ""

        if (state.isFinished) {
            showFinishedDialog()
            return
        }

        val word = state.currentWord ?: return
        binding.tvLessonTitle.text = viewModel.lessonTitle

        val isAllMode = state.activeLang == "all"
        val answerChecked = state.checkResult != CheckResult.NONE
        val activeWord = cleanLearnText(word.getWordByLang(state.activeLang) ?: "")

        // Button: "Проверить" → "Следующее слово" после проверки или в режиме ALL
        if (isAllMode || answerChecked) {
            binding.btnCheck.text = getString(R.string.btn_next_word)
            binding.btnCheck.setOnClickListener { viewModel.nextWord() }
            binding.btnCheck.isEnabled = true
        } else {
            binding.btnCheck.text = getString(R.string.btn_check)
            binding.btnCheck.setOnClickListener { viewModel.checkAnswer() }
            binding.btnCheck.isEnabled = true
        }

        // Скрываем тайлы в режиме ALL
        binding.rvAnswerSlots.visibility = if (isAllMode) View.GONE else View.VISIBLE
        binding.rvLetters.visibility = if (isAllMode) View.GONE else View.VISIBLE

        // Строки языков — динамически по availableLangs (не только NL/EN/RU):
        // исправляет «итальянский не появился» — раньше строки были жёстко
        // свёрстаны под три языка.
        renderLangRows(word, state, activeWord, answerChecked, isAllMode)
        binding.tvExample.visibility = View.GONE

        // Progress bar
        binding.progressBar2.progress = if (state.words.isNotEmpty())
            ((state.currentIndex + 1) * 100 / state.words.size)
        else 0
        binding.tvProgress.text = "${state.currentIndex + 1} / ${state.words.size}"

        // Difficult word shortcut
        binding.btnDifficult.setImageResource(
            if (word.difficult) R.drawable.ic_star_24 else R.drawable.ic_star_border_24
        )
        binding.btnDifficult.contentDescription =
            if (word.difficult) getString(R.string.remove_from_difficult) else getString(R.string.add_to_difficult)
        binding.btnDeleteWord.visibility = if (word.editable) View.VISIBLE else View.GONE

        // Lang chips
        setupLangChips(state.availableLangs, state.activeLang)

        // Letter tiles
        letterAdapter.setLetters(state.scrambledLetters, state.usedSlots.toSet())

        // Answer slots
        slotAdapter.setSlots(state.placedLetters, state.checkResult)

        // Check result styling
        when (state.checkResult) {
            CheckResult.CORRECT -> {
                binding.root.setBackgroundColor(ContextCompat.getColor(requireContext(), R.color.colorGameCorrectOverlay))
            }
            CheckResult.MASTERED -> {
                binding.root.setBackgroundColor(ContextCompat.getColor(requireContext(), R.color.colorGameMasteredOverlay))
            }
            CheckResult.WRONG -> {
                binding.root.setBackgroundColor(ContextCompat.getColor(requireContext(), R.color.colorGameWrongOverlay))
            }
            CheckResult.NONE -> {
                binding.root.setBackgroundColor(ContextCompat.getColor(requireContext(), R.color.colorBackground))
            }
        }

        binding.btnPrev.isEnabled = state.currentIndex > 0
        binding.btnNext.isEnabled = state.currentIndex < state.words.size - 1

        state.error?.let {
            requireContext().toast(it)
            viewModel.clearError()
        }
    }

    private fun ensureStandardTimer(goalMinutes: Int) {
        if (timerGoalMinutes == goalMinutes) return
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
            renderStandardTimer()
            timerHandler.removeCallbacks(timerRunnable)
            if (lifecycle.currentState.isAtLeast(Lifecycle.State.RESUMED) && timerRunning) {
                timerHandler.post(timerRunnable)
            }
        }
    }

    private fun renderStandardTimer() {
        binding.tvDailyGoal.text = "%d:%02d".format(timerSeconds / 60, timerSeconds % 60)
        binding.btnDailyPause.setImageResource(if (timerRunning) R.drawable.ic_pause_24 else R.drawable.ic_play_24)
    }

    private fun saveTimerState() {
        if (timerGoalMinutes <= 0) return
        lifecycleScope.launch {
            LearnWordsApp.instance.preferencesManager.saveTimerState(
                timerSeconds.toLong(), LocalDate.now().toString(), timerRunning
            )
        }
    }

    override fun onResume() {
        super.onResume()
        timerHandler.removeCallbacks(contentSyncRunnable)
        timerHandler.post(contentSyncRunnable)
        if (!viewModel.uiState.value.isChild && timerGoalMinutes > 0 &&
            timerRunning && timerSeconds > 0) {
            timerHandler.removeCallbacks(timerRunnable)
            timerHandler.post(timerRunnable)
        }
    }

    override fun onPause() {
        timerHandler.removeCallbacks(timerRunnable)
        timerHandler.removeCallbacks(contentSyncRunnable)
        saveTimerState()
        super.onPause()
    }

    private fun setupLangChips(langs: List<String>, active: String) {
        if (langs == renderedLangs && active == renderedActiveLang) return
        renderedLangs = langs
        renderedActiveLang = active
        binding.chipGroupLang.removeAllViews()
        // Чипы компактные (ширина по тексту), чтобы ALL + 4-5 языков помещались
        // на экране БЕЗ прокрутки — раньше фиксированные 56dp выталкивали
        // последний язык (IT) за край HorizontalScrollView, и кнопка «терялась».
        binding.chipGroupLang.chipSpacingHorizontal = dp(4)
        val chipHeight = dp(34)
        val chipTextSize = 12.5f
        langs.forEach { lang ->
            val chip = com.google.android.material.chip.Chip(requireContext()).apply {
                text = if (lang == "all") getString(R.string.lang_all) else lang.uppercase()
                tag = lang
                isCheckable = true
                isChecked = lang == active
                isCheckedIconVisible = false
                chipMinHeight = chipHeight.toFloat()
                minHeight = chipHeight
                minWidth = dp(44)
                textSize = chipTextSize
                textAlignment = View.TEXT_ALIGNMENT_CENTER
                gravity = Gravity.CENTER
                chipStartPadding = dp(4).toFloat()
                chipEndPadding = dp(4).toFloat()
                textStartPadding = dp(4).toFloat()
                textEndPadding = dp(4).toFloat()
                chipBackgroundColor = ColorStateList.valueOf(
                    ContextCompat.getColor(
                        requireContext(),
                        if (lang == active) R.color.colorChipActive else R.color.colorChipInactive
                    )
                )
                setPadding(0, 0, 0, 0)
                layoutParams = com.google.android.material.chip.ChipGroup.LayoutParams(
                    ViewGroup.LayoutParams.WRAP_CONTENT,
                    chipHeight
                )
                shapeAppearanceModel = shapeAppearanceModel
                    .toBuilder()
                    .setAllCornerSizes(dp(17).toFloat())
                    .build()
            }
            binding.chipGroupLang.addView(chip)
        }
    }

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()

    private fun answerSlotPosition(container: View, x: Float, y: Float): Int {
        val recyclerView = container as androidx.recyclerview.widget.RecyclerView
        val child = recyclerView.findChildViewUnder(x, y)
        if (child != null) {
            val position = recyclerView.getChildAdapterPosition(child)
            if (position != androidx.recyclerview.widget.RecyclerView.NO_POSITION) {
                val beforeCenter = x < child.left + child.width / 2f
                return (position + if (beforeCenter) 0 else 1)
                    .coerceIn(0, slotAdapter.itemCount)
            }
        }
        return slotAdapter.itemCount
    }

    private fun cleanLearnText(value: String): String =
        value.replace("**", "").trim()

    /**
     * Строит строки карточки по СПИСКУ языков урока (как на вебе), а не по
     * фиксированным NL/EN/RU. Строка активного языка скрыта до проверки
     * (иначе ответ виден заранее); в режиме ALL показываются все.
     */
    private fun renderLangRows(
        word: com.learnwords.app.data.api.WordDto,
        state: LearnUiState,
        activeWord: String,
        answerChecked: Boolean,
        isAllMode: Boolean
    ) {
        val container = binding.langRowsContainer
        container.removeAllViews()
        state.availableLangs.filter { it != "all" }.forEach { lang ->
            val show = isAllMode || lang != state.activeLang || answerChecked
            if (!show) return@forEach
            val rawWord = word.getWordByLang(lang).orEmpty()
            // У этого слова нет перевода на язык → строку не показываем вовсе
            // (раньше выводился «-»). Исключение: активный язык после проверки.
            if (rawWord.isBlank() && !(lang == state.activeLang && answerChecked)) return@forEach
            val row = ItemLearnLangRowBinding.inflate(layoutInflater, container, false)
            row.tvLangLabel.text = lang.uppercase()
            row.tvLangWord.text =
                if (lang == state.activeLang && answerChecked) activeWord
                else cleanLearnText(rawWord)
            val rawExample = word.getExampleByLang(lang).orEmpty()
            val example = cleanLearnText(rawExample)
            row.tvLangExample.text = example
            row.tvLangExample.visibility = if (example.isNotBlank()) View.VISIBLE else View.GONE
            setupAudioButton(row.btnLangAudio, word.getAudioByLang(lang), true, lang)
            setupEditableText(row.tvLangWord, rawWord, lang, false, word.editable)
            setupEditableText(row.tvLangExample, rawExample, lang, true, word.editable && example.isNotBlank())
            container.addView(row.root)
        }
    }

    private fun setupEditableText(
        textView: TextView,
        value: String,
        lang: String,
        isExample: Boolean,
        enabled: Boolean
    ) {
        if (!enabled) {
            textView.setOnClickListener(null)
            return
        }
        textView.setOnClickListener {
            startInlineEdit(textView, value, lang, isExample)
        }
    }

    private fun startInlineEdit(textView: TextView, originalValue: String, lang: String, isExample: Boolean) {
        val parent = textView.parent as? ViewGroup ?: return
        val index = parent.indexOfChild(textView)
        if (index < 0 || parent.getChildAt(index) is EditText) return

        val editText = EditText(requireContext()).apply {
            id = View.generateViewId()
            layoutParams = textView.layoutParams
            setText(cleanLearnText(originalValue))
            setTextColor(textView.currentTextColor)
            textSize = textView.textSize / resources.displayMetrics.scaledDensity
            typeface = textView.typeface
            background = null
            backgroundTintList = null
            setSingleLine(!isExample)
            maxLines = if (isExample) 3 else 1
            imeOptions = EditorInfo.IME_ACTION_DONE
            setSelectAllOnFocus(true)
            setPadding(textView.paddingLeft, textView.paddingTop, textView.paddingRight, textView.paddingBottom)
        }

        var committed = false
        fun commit() {
            if (committed) return
            committed = true
            val newValue = editText.text?.toString()?.trim().orEmpty()
            parent.removeViewAt(index)
            parent.addView(textView, index)
            textView.visibility = View.VISIBLE
            if (newValue.isNotBlank() && newValue != cleanLearnText(originalValue)) {
                viewModel.updateCurrentText(lang, isExample, newValue)
            }
        }

        parent.removeViewAt(index)
        parent.addView(editText, index)
        editText.requestFocus()
        editText.post {
            val imm = requireContext().getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager
            imm.showSoftInput(editText, InputMethodManager.SHOW_IMPLICIT)
        }
        editText.setOnEditorActionListener { _, actionId, event ->
            val isEnter = event?.keyCode == KeyEvent.KEYCODE_ENTER && event.action == KeyEvent.ACTION_UP
            if (actionId == EditorInfo.IME_ACTION_DONE || isEnter) {
                commit()
                true
            } else {
                false
            }
        }
        editText.setOnFocusChangeListener { _, hasFocus ->
            if (!hasFocus) commit()
        }
        editText.setOnClickListener {
            if (editText.hasFocus()) commit()
        }
    }

    private fun setupAudioButton(button: View, url: String?, rowVisible: Boolean, lang: String) {
        if (rowVisible) {
            button.visibility = View.VISIBLE
            button.alpha = if (url.isNullOrBlank()) 0.55f else 1.0f
            button.setOnClickListener {
                if (url.isNullOrBlank()) {
                    requireContext().toast(getString(R.string.prepare_audio))
                    viewModel.ensureAudioForCurrent(lang)
                } else {
                    audioPlayer.play(fullAudioUrl(url))
                }
            }
        } else {
            button.visibility = View.GONE
            button.setOnClickListener(null)
        }
    }

    private fun fullAudioUrl(url: String): String =
        if (url.startsWith("http")) url
        else "${runBlocking { LearnWordsApp.instance.preferencesManager.serverUrl.first() }.trimEnd('/')}$url"

    private fun confirmDeleteCurrentWord() {
        val word = viewModel.uiState.value.currentWord ?: return
        val title = cleanLearnText(word.nl ?: word.en ?: word.ru ?: "")
        AlertDialog.Builder(requireContext())
            .setTitle(R.string.delete_word_question)
            .setMessage(title.ifBlank { getString(R.string.delete_word_message) })
            .setPositiveButton(R.string.delete) { _, _ -> viewModel.deleteCurrentWord() }
            .setNegativeButton(R.string.cancel, null)
            .show()
    }

    private fun showFinishedDialog() {
        AlertDialog.Builder(requireContext())
            .setTitle(R.string.lesson_finished)
            .setMessage(getString(R.string.lesson_finished_message, viewModel.lessonTitle))
            .setPositiveButton(R.string.to_lessons) { _, _ -> findNavController().navigateUp() }
            .setNeutralButton(R.string.repeat) { _, _ -> viewModel.loadWords() }
            .setCancelable(false)
            .show()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        timerHandler.removeCallbacks(timerRunnable)
        saveTimerState()
        audioPlayer.release()
        _binding = null
    }

    companion object {
    }
}
