package com.learnwords.app.ui.learn

import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.content.res.ColorStateList
import android.view.*
import android.view.inputmethod.EditorInfo
import android.view.inputmethod.InputMethodManager
import android.content.Context
import android.widget.EditText
import android.widget.TextView
import androidx.appcompat.app.AlertDialog
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
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
import com.learnwords.app.databinding.DialogWordResultBinding
import com.learnwords.app.utils.*
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking

class LearnFragment : Fragment() {

    private var _binding: FragmentLearnBinding? = null
    private val binding get() = _binding!!

    private val viewModel: LearnViewModel by viewModels {
        object : ViewModelProvider.Factory {
            override fun <T : androidx.lifecycle.ViewModel> create(modelClass: Class<T>): T {
                val handle = SavedStateHandle(mapOf("lesson" to (arguments?.getString("lesson") ?: "")))
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
    private var resultDialog: AlertDialog? = null
    private val timerHandler = Handler(Looper.getMainLooper())
    private var timerRemainingSeconds = TIMER_TOTAL_SECONDS
    private var timerRunning = true
    private var timerLastTickMs = 0L
    private val timerRunnable = object : Runnable {
        override fun run() {
            updateTimerTick()
            timerHandler.postDelayed(this, 1000L)
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

        binding.btnCheck.setOnClickListener { viewModel.checkAnswer() }
        binding.btnNext.setOnClickListener { viewModel.nextWord() }
        binding.btnPrev.setOnClickListener { viewModel.previousWord() }
        binding.btnDifficult.setOnClickListener { viewModel.toggleDifficult() }
        binding.btnDeleteWord.setOnClickListener { confirmDeleteCurrentWord() }
        binding.btnBack.setOnClickListener { findNavController().navigateUp() }
        binding.btnTimerPause.setOnClickListener { toggleTimerPause() }
        binding.btnTimerRestart.setOnClickListener { restartTimer() }
        restoreTimerState()

        // Language filter chips
        binding.chipGroupLang.setOnCheckedStateChangeListener { group, checkedIds ->
            val chip = group.findViewById<com.google.android.material.chip.Chip>(checkedIds.firstOrNull() ?: return@setOnCheckedStateChangeListener)
            chip?.tag?.toString()?.let { lang ->
                if (lang != viewModel.uiState.value.activeLang) viewModel.setActiveLang(lang)
            }
        }

        lifecycleScope.launch {
            viewModel.uiState.collectLatest { state ->
                renderState(state)
            }
        }
    }

    private fun restoreTimerState() {
        lifecycleScope.launch {
            val saved = LearnWordsApp.instance.preferencesManager.timerSeconds.first()
            timerRemainingSeconds = saved
                .takeIf { it in 1L..TIMER_TOTAL_SECONDS.toLong() }
                ?.toInt()
                ?: TIMER_TOTAL_SECONDS
            timerRunning = timerRemainingSeconds > 0
            timerLastTickMs = System.currentTimeMillis()
            renderTimer()
            timerHandler.removeCallbacks(timerRunnable)
            timerHandler.post(timerRunnable)
        }
    }

    private fun updateTimerTick() {
        if (!timerRunning || timerRemainingSeconds <= 0) {
            renderTimer()
            return
        }
        val now = System.currentTimeMillis()
        val delta = ((now - timerLastTickMs) / 1000L).toInt()
        if (delta > 0) {
            timerRemainingSeconds = (timerRemainingSeconds - delta).coerceAtLeast(0)
            timerLastTickMs = now
            if (timerRemainingSeconds == 0) timerRunning = false
            renderTimer()
            saveTimerState()
        }
    }

    private fun toggleTimerPause() {
        timerRunning = !timerRunning
        timerLastTickMs = System.currentTimeMillis()
        renderTimer()
        saveTimerState()
    }

    private fun restartTimer() {
        timerRemainingSeconds = TIMER_TOTAL_SECONDS
        timerRunning = true
        timerLastTickMs = System.currentTimeMillis()
        renderTimer()
        saveTimerState()
    }

    private fun renderTimer() {
        val minutes = timerRemainingSeconds / 60
        val seconds = timerRemainingSeconds % 60
        binding.tvTimer.text = "%d:%02d".format(minutes, seconds)
        binding.btnTimerPause.setImageResource(
            if (timerRunning) R.drawable.ic_pause_24 else R.drawable.ic_play_24
        )
        binding.btnTimerPause.contentDescription =
            if (timerRunning) "Пауза" else "Продолжить"
        binding.btnTimerPause.isEnabled = timerRemainingSeconds > 0
        binding.btnTimerPause.alpha = if (timerRemainingSeconds > 0) 1.0f else 0.45f
        binding.tvTimer.setTextColor(
            ContextCompat.getColor(
                requireContext(),
                if (timerRemainingSeconds == 0) R.color.colorSecondary else R.color.colorPrimary
            )
        )
    }

    private fun saveTimerState() {
        lifecycleScope.launch {
            LearnWordsApp.instance.preferencesManager.saveTimerState(
                timerRemainingSeconds.toLong(),
                ""
            )
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

        if (state.isFinished) {
            showFinishedDialog()
            return
        }

        val word = state.currentWord ?: return
        binding.tvLessonTitle.text = viewModel.lesson

        val answerChecked = state.checkResult != CheckResult.NONE
        val activeWord = cleanLearnText(word.getWordByLang(state.activeLang) ?: "")
        val activeExample = cleanLearnText(word.getExampleByLang(state.activeLang) ?: "")

        binding.btnCheck.text = if (answerChecked) "Проверено" else "Проверить"
        binding.btnCheck.isEnabled = !answerChecked
        binding.rvAnswerSlots.visibility = View.VISIBLE
        binding.rvLetters.visibility = View.VISIBLE

        val nlText = cleanLearnText(word.nl ?: "-")
        val enText = cleanLearnText(word.en ?: "-")
        val ruText = cleanLearnText(word.ru ?: "-")
        val nlExample = cleanLearnText(word.exNl ?: "")
        val enExample = cleanLearnText(word.exEn ?: "")
        val ruExample = cleanLearnText(word.exRu ?: "")

        binding.tvWordNl.text = if (state.activeLang == "nl" && answerChecked) activeWord else nlText
        binding.tvWordEn.text = if (state.activeLang == "en" && answerChecked) activeWord else enText
        binding.tvWordRu.text = if (state.activeLang == "ru" && answerChecked) activeWord else ruText

        val showNl = state.activeLang != "nl" || answerChecked
        val showEn = state.activeLang != "en" || answerChecked
        val showRu = state.activeLang != "ru" || answerChecked
        binding.tvWordNlRow.visibility = if (showNl) View.VISIBLE else View.GONE
        binding.tvWordEnRow.visibility = if (showEn) View.VISIBLE else View.GONE
        binding.tvWordRuRow.visibility = if (showRu) View.VISIBLE else View.GONE

        binding.tvExampleNl.text = nlExample
        binding.tvExampleEn.text = enExample
        binding.tvExampleRu.text = ruExample
        binding.tvExampleNl.visibility = if (showNl && nlExample.isNotBlank()) View.VISIBLE else View.GONE
        binding.tvExampleEn.visibility = if (showEn && enExample.isNotBlank()) View.VISIBLE else View.GONE
        binding.tvExampleRu.visibility = if (showRu && ruExample.isNotBlank()) View.VISIBLE else View.GONE
        binding.tvExample.visibility = View.GONE
        setupRowAudioButtons(word, showNl, showEn, showRu)
        setupInlineEditors(word, showNl, showEn, showRu)

        // Progress bar
        binding.progressBar2.progress = if (state.words.isNotEmpty())
            ((state.currentIndex + 1) * 100 / state.words.size)
        else 0
        binding.tvProgress.text = "${state.currentIndex + 1} / ${state.words.size}"

        // Difficult star
        binding.btnDifficult.text = if (word.difficult) "★" else "☆"
        binding.btnDifficult.contentDescription =
            if (word.difficult) "Убрать из сложных слов" else "Добавить в сложные слова"
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
                binding.root.setBackgroundColor(0x2200CC44.toInt())
            }
            CheckResult.WRONG -> {
                binding.root.setBackgroundColor(0x22CC0000.toInt())
            }
            CheckResult.NONE -> {
                binding.root.setBackgroundColor(ContextCompat.getColor(requireContext(), R.color.colorBackground))
            }
        }

        binding.btnPrev.isEnabled = state.currentIndex > 0
        binding.btnNext.isEnabled = state.currentIndex < state.words.size - 1

        if (state.showResultDialog && resultDialog?.isShowing != true) {
            showResultDialog(state)
        }

        state.error?.let {
            requireContext().toast(it)
            viewModel.clearError()
        }
    }

    private fun setupLangChips(langs: List<String>, active: String) {
        if (langs == renderedLangs && active == renderedActiveLang) return
        renderedLangs = langs
        renderedActiveLang = active
        binding.chipGroupLang.removeAllViews()
        val availableWidth = resources.displayMetrics.widthPixels - dp(108)
        val chipWidth = (availableWidth / langs.size.coerceAtLeast(1)).coerceIn(dp(52), dp(70))
        val chipHeight = dp(34)
        val chipTextSize = if (langs.size >= 4) 13f else 14f
        langs.forEach { lang ->
            val chip = com.google.android.material.chip.Chip(requireContext()).apply {
                text = lang.uppercase()
                tag = lang
                isCheckable = true
                isChecked = lang == active
                isCheckedIconVisible = false
                chipMinHeight = chipHeight.toFloat()
                minHeight = chipHeight
                minWidth = chipWidth
                textSize = chipTextSize
                textAlignment = View.TEXT_ALIGNMENT_CENTER
                gravity = Gravity.CENTER
                chipStartPadding = 0f
                chipEndPadding = 0f
                textStartPadding = 0f
                textEndPadding = 0f
                chipBackgroundColor = ColorStateList.valueOf(
                    if (lang == active) 0xFFD0D0D0.toInt() else 0xFFE9E9E9.toInt()
                )
                setPadding(0, 0, 0, 0)
                layoutParams = com.google.android.material.chip.ChipGroup.LayoutParams(
                    chipWidth,
                    chipHeight
                ).apply {
                    marginEnd = dp(4)
                }
                shapeAppearanceModel = shapeAppearanceModel
                    .toBuilder()
                    .setAllCornerSizes(dp(17).toFloat())
                    .build()
            }
            binding.chipGroupLang.addView(chip)
        }
    }

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()

    private fun cleanLearnText(value: String): String =
        value.replace("**", "").trim()

    private fun setupInlineEditors(
        word: com.learnwords.app.data.api.WordDto,
        showNl: Boolean,
        showEn: Boolean,
        showRu: Boolean
    ) {
        setupEditableText(binding.tvWordNl, word.nl.orEmpty(), "nl", false, showNl && word.editable)
        setupEditableText(binding.tvExampleNl, word.exNl.orEmpty(), "nl", true, showNl && word.editable)
        setupEditableText(binding.tvWordEn, word.en.orEmpty(), "en", false, showEn && word.editable)
        setupEditableText(binding.tvExampleEn, word.exEn.orEmpty(), "en", true, showEn && word.editable)
        setupEditableText(binding.tvWordRu, word.ru.orEmpty(), "ru", false, showRu && word.editable)
        setupEditableText(binding.tvExampleRu, word.exRu.orEmpty(), "ru", true, showRu && word.editable)
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

    private fun setupRowAudioButtons(
        word: com.learnwords.app.data.api.WordDto,
        showNl: Boolean,
        showEn: Boolean,
        showRu: Boolean
    ) {
        setupAudioButton(binding.btnAudioNl, word.audioNl, showNl, "nl")
        setupAudioButton(binding.btnAudioEn, word.audioEn, showEn, "en")
        setupAudioButton(binding.btnAudioRu, word.audioRu, showRu, "ru")
    }

    private fun setupAudioButton(button: View, url: String?, rowVisible: Boolean, lang: String) {
        if (rowVisible) {
            button.visibility = View.VISIBLE
            button.alpha = if (url.isNullOrBlank()) 0.55f else 1.0f
            button.setOnClickListener {
                if (url.isNullOrBlank()) {
                    requireContext().toast("Готовлю аудио, нажмите ещё раз через пару секунд")
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

    private fun showResultDialog(state: LearnUiState) {
        val dialogBinding = DialogWordResultBinding.inflate(layoutInflater)
        val word = state.currentWord ?: return

        dialogBinding.tvResultTitle.text = "Неправильно"
        dialogBinding.tvCorrectAnswer.text = cleanLearnText(word.getWordByLang(state.activeLang) ?: "")
        dialogBinding.tvWordNl.text = "NL: ${cleanLearnText(word.nl ?: "-")}"
        dialogBinding.tvWordEn.text = "EN: ${cleanLearnText(word.en ?: "-")}"
        dialogBinding.tvWordRu.text = "RU: ${cleanLearnText(word.ru ?: "-")}"
        dialogBinding.tvExampleNl.text = cleanLearnText(word.exNl ?: "")
        dialogBinding.tvExampleEn.text = cleanLearnText(word.exEn ?: "")
        dialogBinding.tvExampleRu.text = cleanLearnText(word.exRu ?: "")

        resultDialog = AlertDialog.Builder(requireContext())
            .setView(dialogBinding.root)
            .setCancelable(true)
            .create()

        dialogBinding.btnNextWord.setOnClickListener {
            resultDialog?.dismiss()
            viewModel.nextWord()
        }
        dialogBinding.btnClose.setOnClickListener {
            resultDialog?.dismiss()
            viewModel.dismissResult()
        }
        resultDialog?.setOnDismissListener {
            resultDialog = null
            viewModel.dismissResult()
        }
        resultDialog?.show()
    }

    private fun confirmDeleteCurrentWord() {
        val word = viewModel.uiState.value.currentWord ?: return
        val title = cleanLearnText(word.nl ?: word.en ?: word.ru ?: "")
        AlertDialog.Builder(requireContext())
            .setTitle("Удалить слово?")
            .setMessage(title.ifBlank { "Это слово будет удалено из урока." })
            .setPositiveButton("Удалить") { _, _ -> viewModel.deleteCurrentWord() }
            .setNegativeButton("Отмена", null)
            .show()
    }

    private fun showFinishedDialog() {
        AlertDialog.Builder(requireContext())
            .setTitle("Урок завершён!")
            .setMessage("Вы прошли все слова урока \"${viewModel.lesson}\"")
            .setPositiveButton("К урокам") { _, _ -> findNavController().navigateUp() }
            .setNeutralButton("Повторить") { _, _ -> viewModel.loadWords() }
            .setCancelable(false)
            .show()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        timerHandler.removeCallbacks(timerRunnable)
        saveTimerState()
        audioPlayer.release()
        resultDialog?.dismiss()
        resultDialog = null
        _binding = null
    }

    companion object {
        private const val TIMER_TOTAL_SECONDS = 10 * 60
    }
}
