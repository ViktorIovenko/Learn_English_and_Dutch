package com.learnwords.app.ui.upload

import android.os.Bundle
import android.view.*
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.lifecycleScope
import com.learnwords.app.databinding.FragmentTabAddWordsBinding
import com.learnwords.app.utils.toast
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.flow.onEach
import kotlinx.coroutines.flow.launchIn
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

        // Заполняем поля Ollama из настроек (только если не в фокусе, чтобы не перебивать ввод)
        viewModel.ollamaUrl.onEach { url ->
            if (!binding.etOllamaUrl.hasFocus()) binding.etOllamaUrl.setText(url)
        }.launchIn(viewLifecycleOwner.lifecycleScope)

        viewModel.ollamaModel.onEach { model ->
            if (!binding.etOllamaModel.hasFocus()) binding.etOllamaModel.setText(model)
        }.launchIn(viewLifecycleOwner.lifecycleScope)

        binding.btnCheckOllama.setOnClickListener {
            saveOllamaSettings()
            viewModel.checkOllamaConnection()
        }

        binding.btnAddRow.setOnClickListener { wordAdapter.addRow() }

        binding.btnTranslate.setOnClickListener {
            val word = binding.etWord.text.toString().trim()
            if (word.isBlank()) {
                context?.toast("Введите слово")
                return@setOnClickListener
            }
            saveOllamaSettings()
            val fromLang = binding.spinnerFromLang.selectedItem.toString().lowercase()
            viewModel.translateWord(word, fromLang, listOf("nl", "en", "ru").filter { it != fromLang })
        }

        binding.btnImport.setOnClickListener {
            val lesson = binding.etLesson.text.toString().trim()
            viewModel.importWords(lesson, wordAdapter.getItems())
        }

        lifecycleScope.launch {
            viewModel.uiState.collectLatest { state ->
                binding.progressBar.visibility = if (state.isLoading) View.VISIBLE else View.GONE

                // Статус подключения к Ollama
                state.ollamaStatus?.let { status ->
                    binding.tvOllamaStatus.text = status
                    binding.tvOllamaStatus.setTextColor(
                        if (status.startsWith("Доступна")) 0xFF2E7D32.toInt() else 0xFFC62828.toInt()
                    )
                }

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

    private fun saveOllamaSettings() {
        val url = binding.etOllamaUrl.text.toString()
        val model = binding.etOllamaModel.text.toString()
        viewModel.saveOllamaSettings(url, model)
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
