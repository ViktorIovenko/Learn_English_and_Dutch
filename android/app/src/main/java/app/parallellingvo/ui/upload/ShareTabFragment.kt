package app.parallellingvo.ui.upload

import android.os.Bundle
import android.view.*
import android.text.SpannableStringBuilder
import android.text.Spanned
import android.text.style.ForegroundColorSpan
import android.text.style.RelativeSizeSpan
import androidx.core.content.ContextCompat
import com.google.android.material.card.MaterialCardView
import com.google.android.material.checkbox.MaterialCheckBox
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import app.parallellingvo.R
import app.parallellingvo.data.api.LessonDto
import app.parallellingvo.databinding.FragmentTabShareBinding
import app.parallellingvo.utils.toast
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
                requireContext().toast(getString(R.string.select_lessons))
                return@setOnClickListener
            }
            viewModel.createShare(lessons, title)
        }

        binding.btnImportShare.setOnClickListener {
            val token = binding.etToken.text.toString().trim()
            if (token.isBlank()) {
                requireContext().toast(getString(R.string.enter_token))
                return@setOnClickListener
            }
            // Navigate to share import screen or import directly
            requireContext().toast(getString(R.string.token_value, token))
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
            val card = layoutInflater.inflate(
                R.layout.item_share_lesson, binding.llShareLessons, false
            ) as MaterialCardView
            val checkBox = card.findViewById<MaterialCheckBox>(R.id.check_lesson)
            fun updateCard(checked: Boolean) {
                card.strokeColor = ContextCompat.getColor(requireContext(),
                    if (checked) R.color.colorPrimary else R.color.colorDivider)
                card.setCardBackgroundColor(ContextCompat.getColor(requireContext(),
                    if (checked) R.color.colorInfoBackground else R.color.colorSurface))
            }
            checkBox.apply {
                text = SpannableStringBuilder(lesson.lesson).apply {
                    if (lesson.wordCount > 0) {
                        append("\n")
                        val countStart = length
                        append("${lesson.wordCount} ${getString(R.string.words_label)}")
                        setSpan(RelativeSizeSpan(0.85f), countStart, length, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
                        setSpan(ForegroundColorSpan(ContextCompat.getColor(requireContext(),
                            R.color.colorTextSecondary)), countStart, length, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
                    }
                }
                isChecked = selectedLessons.contains(lesson.lesson)
                updateCard(isChecked)
                setOnCheckedChangeListener { _, checked ->
                    if (checked) {
                        selectedLessons.add(lesson.lesson)
                    } else {
                        selectedLessons.remove(lesson.lesson)
                    }
                    updateCard(checked)
                    updateSelectedCount()
                }
            }
            binding.llShareLessons.addView(card)
        }

        updateSelectedCount()
    }

    private fun updateSelectedCount() {
        val binding = _binding ?: return
        binding.tvSelectedLessons.text = when {
            renderedLessonNames.isEmpty() -> getString(R.string.no_lessons)
            selectedLessons.isEmpty() -> getString(R.string.select_lessons)
            else -> getString(R.string.selected_count, selectedLessons.size)
        }
        binding.btnCreateShare.isEnabled = !isLoading && selectedLessons.isNotEmpty()
        binding.btnCreateShare.text = if (selectedLessons.isEmpty()) {
            getString(R.string.create_link)
        } else {
            "${getString(R.string.create_link)} ? ${selectedLessons.size}"
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
