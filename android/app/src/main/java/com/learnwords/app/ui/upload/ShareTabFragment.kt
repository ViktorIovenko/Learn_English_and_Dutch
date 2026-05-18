package com.learnwords.app.ui.upload

import android.os.Bundle
import android.view.*
import android.widget.CheckBox
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import com.learnwords.app.data.api.LessonDto
import com.learnwords.app.databinding.FragmentTabShareBinding
import com.learnwords.app.utils.toast
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch

class ShareTabFragment : Fragment() {

    private var _binding: FragmentTabShareBinding? = null
    private val binding get() = _binding!!
    private val viewModel: UploadViewModel by viewModels({ requireParentFragment() })
    private val selectedLessons = linkedSetOf<String>()
    private var renderedLessonNames: List<String> = emptyList()
    private var isLoading = false

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentTabShareBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        binding.btnCreateShare.setOnClickListener {
            val lessons = selectedLessons.toList()
            val title = binding.etTitle.text.toString().trim().ifBlank { null }
            if (lessons.isEmpty()) {
                requireContext().toast("Выберите уроки")
                return@setOnClickListener
            }
            viewModel.createShare(lessons, title)
        }

        binding.btnImportShare.setOnClickListener {
            val token = binding.etToken.text.toString().trim()
            if (token.isBlank()) {
                requireContext().toast("Введите токен")
                return@setOnClickListener
            }
            // Navigate to share import screen or import directly
            requireContext().toast("Введите токен: $token")
        }

        viewModel.loadShareLessons()

        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.uiState.collectLatest { state ->
                    val binding = _binding ?: return@collectLatest
                    isLoading = state.isLoading
                    binding.progressBar.visibility = if (state.isLoading) View.VISIBLE else View.GONE
                    updateSelectedCount()

                    renderLessons(state.shareLessons)

                    state.shareUrl?.let { url ->
                        binding.tvShareUrl.text = url
                        binding.tvShareUrl.visibility = View.VISIBLE
                    }
                }
            }
        }
    }

    private fun renderLessons(lessons: List<LessonDto>) {
        val binding = _binding ?: return
        val lessonNames = lessons.map { it.lesson }
        if (lessonNames == renderedLessonNames) {
            updateSelectedCount()
            return
        }

        renderedLessonNames = lessonNames
        selectedLessons.retainAll(lessonNames.toSet())
        binding.llShareLessons.removeAllViews()

        lessons.forEach { lesson ->
            val checkBox = CheckBox(requireContext()).apply {
                text = buildString {
                    append(lesson.lesson)
                    if (lesson.wordCount > 0) {
                        append(" (")
                        append(lesson.wordCount)
                        append(" слов)")
                    }
                }
                textSize = 16f
                isChecked = selectedLessons.contains(lesson.lesson)
                setOnCheckedChangeListener { _, checked ->
                    if (checked) {
                        selectedLessons.add(lesson.lesson)
                    } else {
                        selectedLessons.remove(lesson.lesson)
                    }
                    updateSelectedCount()
                }
            }
            binding.llShareLessons.addView(checkBox)
        }

        updateSelectedCount()
    }

    private fun updateSelectedCount() {
        val binding = _binding ?: return
        binding.tvSelectedLessons.text = when {
            renderedLessonNames.isEmpty() -> "Уроки не найдены"
            selectedLessons.isEmpty() -> "Выберите уроки"
            else -> "Выбрано: ${selectedLessons.size}"
        }
        binding.btnCreateShare.isEnabled = !isLoading && selectedLessons.isNotEmpty()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
