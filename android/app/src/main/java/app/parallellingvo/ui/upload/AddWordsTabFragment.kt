package app.parallellingvo.ui.upload

import android.os.Bundle
import android.view.*
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.lifecycleScope
import app.parallellingvo.R
import app.parallellingvo.databinding.FragmentTabAddWordsBinding
import app.parallellingvo.utils.toast
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch

class AddWordsTabFragment : Fragment() {

    private var _binding: FragmentTabAddWordsBinding? = null
    private val binding get() = _binding!!
    private val viewModel: UploadViewModel by viewModels({ requireParentFragment() })
    private lateinit var wordAdapter: WordPreviewAdapter
    private var displayedWords: List<app.parallellingvo.data.api.WordDto>? = null

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentTabAddWordsBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        wordAdapter = WordPreviewAdapter()
        binding.rvWords.adapter = wordAdapter

        binding.btnTranslate.setOnClickListener {
            if (binding.etLesson.text.toString().isBlank()) {
                context?.toast(getString(R.string.enter_lesson_title))
                return@setOnClickListener
            }
            val words = binding.etWord.text.toString().lineSequence()
                .map { it.trim() }.filter { it.isNotEmpty() }.distinctBy { it.lowercase() }.toList()
            if (words.isEmpty()) {
                context?.toast(getString(R.string.enter_word))
                return@setOnClickListener
            }
            val fromLang = binding.spinnerFromLang.selectedItem.toString().lowercase()
            viewModel.translateWords(words, fromLang)
        }

        binding.btnImport.setOnClickListener {
            val lesson = binding.etLesson.text.toString().trim()
            viewModel.importWords(lesson, wordAdapter.getItems())
        }

        viewLifecycleOwner.lifecycleScope.launch {
            viewModel.uiState.collectLatest { state ->
                binding.progressBar.visibility = if (state.isLoading) View.VISIBLE else View.GONE

                if (displayedWords != state.generatedWords) {
                    displayedWords = state.generatedWords
                    wordAdapter.setItems(state.generatedWords)
                }
                binding.btnTranslate.isEnabled = !state.isLoading
                binding.btnImport.isEnabled = !state.isLoading && wordAdapter.itemCount > 0

                state.error?.let {
                    context?.toast(it)
                    viewModel.clearMessages()
                }
                state.success?.let {
                    context?.toast(it)
                    viewModel.clearMessages()
                }
            }
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
        displayedWords = null
    }
}
