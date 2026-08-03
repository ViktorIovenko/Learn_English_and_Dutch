package com.learnwords.app.ui.upload

import android.os.Bundle
import android.view.*
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.lifecycleScope
import com.learnwords.app.R
import com.learnwords.app.databinding.FragmentTabAddWordsBinding
import com.learnwords.app.utils.toast
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch

class AddWordsTabFragment : Fragment() {

    private var _binding: FragmentTabAddWordsBinding? = null
    private val binding get() = _binding!!
    private val viewModel: UploadViewModel by viewModels({ requireParentFragment() })
    private lateinit var wordAdapter: WordPreviewAdapter

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentTabAddWordsBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        wordAdapter = WordPreviewAdapter()
        binding.rvWords.adapter = wordAdapter

        binding.btnAddRow.setOnClickListener { wordAdapter.addRow() }

        binding.btnTranslate.setOnClickListener {
            val word = binding.etWord.text.toString().trim()
            if (word.isBlank()) {
                context?.toast(getString(R.string.enter_word))
                return@setOnClickListener
            }
            val fromLang = binding.spinnerFromLang.selectedItem.toString().lowercase()
            viewModel.translateWord(word, fromLang)
        }

        binding.btnImport.setOnClickListener {
            val lesson = binding.etLesson.text.toString().trim()
            viewModel.importWords(lesson, wordAdapter.getItems())
        }

        lifecycleScope.launch {
            viewModel.uiState.collectLatest { state ->
                binding.progressBar.visibility = if (state.isLoading) View.VISIBLE else View.GONE

                // Добавляем переведённое слово в список (только если список пустой)
                if (state.generatedWords.isNotEmpty() && wordAdapter.itemCount == 0) {
                    val rows = state.generatedWords.map { dto ->
                        WordPreviewAdapter.WordRow(
                            nl = dto.nl ?: "",
                            en = dto.en ?: "",
                            ru = dto.ru ?: "",
                            exNl = dto.exNl ?: "",
                            exEn = dto.exEn ?: "",
                            exRu = dto.exRu ?: ""
                        )
                    }
                    wordAdapter.setItems(rows)
                }

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
    }
}
