package com.learnwords.app.ui.upload

import android.os.Bundle
import android.view.*
import android.widget.ArrayAdapter
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.lifecycleScope
import com.learnwords.app.databinding.FragmentTabTopicBinding
import com.learnwords.app.utils.toast
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.flow.onEach
import kotlinx.coroutines.flow.launchIn
import kotlinx.coroutines.launch

class TopicTabFragment : Fragment() {

    private var _binding: FragmentTabTopicBinding? = null
    private val binding get() = _binding!!
    private val viewModel: UploadViewModel by viewModels({ requireParentFragment() })
    private lateinit var wordAdapter: WordPreviewAdapter

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentTabTopicBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        val levels = listOf("A1", "A2", "B1", "B2", "C1", "C2")
        binding.spinnerLevel.adapter = ArrayAdapter(requireContext(),
            android.R.layout.simple_spinner_item, levels).also {
            it.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
        }

        wordAdapter = WordPreviewAdapter()
        binding.rvGeneratedWords.adapter = wordAdapter

        // Заполняем поля Ollama из настроек (только если не в фокусе)
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

        binding.btnGenerate.setOnClickListener {
            val topic = binding.etTopic.text.toString().trim()
            if (topic.isBlank()) {
                context?.toast("Введите тему")
                return@setOnClickListener
            }
            saveOllamaSettings()
            val level = binding.spinnerLevel.selectedItem.toString()
            val count = binding.etWordCount.text.toString().toIntOrNull() ?: 10
            viewModel.generateByTopic(topic, level, count, listOf("nl", "en", "ru"))
        }

        binding.btnImport.setOnClickListener {
            val lesson = binding.etLesson.text.toString().trim().ifBlank {
                binding.etTopic.text.toString().trim()
            }
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

                if (state.generatedWords.isNotEmpty()) {
                    val rows = state.generatedWords.map { dto ->
                        WordPreviewAdapter.WordRow(
                            nl = dto.nl ?: "", en = dto.en ?: "", ru = dto.ru ?: "",
                            exNl = dto.exNl ?: "", exEn = dto.exEn ?: "", exRu = dto.exRu ?: ""
                        )
                    }
                    wordAdapter.setItems(rows)
                    binding.btnImport.isEnabled = true
                } else {
                    binding.btnImport.isEnabled = false
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
