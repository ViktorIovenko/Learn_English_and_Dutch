package com.learnwords.app.ui.upload

import android.os.Bundle
import android.view.*
import android.widget.SearchView
import androidx.appcompat.app.AlertDialog
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import android.view.LayoutInflater
import android.view.ViewGroup
import com.learnwords.app.R
import com.learnwords.app.data.api.WordDto
import com.learnwords.app.databinding.FragmentTabWordDatabaseBinding
import com.learnwords.app.databinding.ItemWordDatabaseBinding
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch

class WordDatabaseTabFragment : Fragment() {

    private var _binding: FragmentTabWordDatabaseBinding? = null
    private val binding get() = _binding!!
    private val viewModel: UploadViewModel by viewModels({ requireParentFragment() })
    private lateinit var wordDbAdapter: WordDbAdapter
    private var duplicatesDialogShowing = false

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentTabWordDatabaseBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        wordDbAdapter = WordDbAdapter(
            onDelete = { word ->
                AlertDialog.Builder(requireContext())
                    .setTitle(R.string.delete_word_question)
                    .setMessage("${word.nl ?: word.en ?: word.ru}")
                    .setPositiveButton(R.string.delete) { _, _ -> viewModel.deleteWord(word.id) }
                    .setNegativeButton(R.string.cancel, null)
                    .show()
            },
            onAudio = { word ->
                viewModel.ensureAudio(listOf(word.id))
            }
        )
        binding.rvWords.layoutManager = LinearLayoutManager(requireContext())
        binding.rvWords.adapter = wordDbAdapter

        binding.searchView.setOnQueryTextListener(object : SearchView.OnQueryTextListener {
            override fun onQueryTextSubmit(query: String?): Boolean {
                viewModel.searchWords(query ?: "")
                return true
            }
            override fun onQueryTextChange(newText: String?) = false
        })

        binding.btnSearch.setOnClickListener {
            viewModel.searchWords(binding.searchView.query.toString())
        }

        binding.btnDuplicates.setOnClickListener {
            viewModel.checkDuplicates()
        }

        binding.btnPrevPage.setOnClickListener {
            val state = viewModel.uiState.value
            if (state.dbPage > 1) viewModel.searchWords(state.dbQuery, state.dbPage - 1)
        }

        binding.btnNextPage.setOnClickListener {
            val state = viewModel.uiState.value
            viewModel.searchWords(state.dbQuery, state.dbPage + 1)
        }

        viewModel.searchWords("")

        viewLifecycleOwner.lifecycleScope.launch {
            viewModel.uiState.collectLatest { state ->
                val binding = _binding ?: return@collectLatest
                binding.progressBar.visibility = if (state.isLoading) View.VISIBLE else View.GONE
                wordDbAdapter.submitList(state.dbWords)
                binding.tvPageInfo.text = getString(R.string.page_info, state.dbPage, state.dbTotal)
                binding.btnPrevPage.isEnabled = state.dbPage > 1
                binding.btnNextPage.isEnabled = state.dbPage * 30 < state.dbTotal

                if (state.duplicates.isNotEmpty() && !duplicatesDialogShowing) {
                    showDuplicatesDialog(state.duplicates)
                }
            }
        }
    }

    private fun showDuplicatesDialog(duplicates: List<com.learnwords.app.data.api.WordDto>) {
        duplicatesDialogShowing = true
        val message = getString(R.string.duplicates_found, duplicates.size) + "\n\n" +
            duplicates.take(30).joinToString("\n") { w ->
                listOfNotNull(w.nl, w.en, w.ru).joinToString(" / ")
            }
        AlertDialog.Builder(requireContext())
            .setTitle(getString(R.string.check_duplicates))
            .setMessage(message)
            .setPositiveButton(R.string.ok) { _, _ ->
                duplicatesDialogShowing = false
                viewModel.clearDuplicates()
            }
            .setOnCancelListener {
                duplicatesDialogShowing = false
                viewModel.clearDuplicates()
            }
            .show()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}

class WordDbAdapter(
    private val onDelete: (WordDto) -> Unit,
    private val onAudio: (WordDto) -> Unit
) : androidx.recyclerview.widget.ListAdapter<WordDto, WordDbAdapter.WordDbViewHolder>(WordDiffCallback()) {

    inner class WordDbViewHolder(private val binding: ItemWordDatabaseBinding) :
        RecyclerView.ViewHolder(binding.root) {

        fun bind(word: WordDto) {
            binding.tvNl.text = word.nl ?: "-"
            binding.tvEn.text = word.en ?: "-"
            binding.tvRu.text = word.ru ?: "-"
            binding.tvLesson.text = word.lesson ?: ""
            binding.btnDelete.setOnClickListener { onDelete(word) }
            binding.btnAudio.setOnClickListener { onAudio(word) }
            binding.ivAudioStatus.visibility =
                if (word.audioNl != null || word.audioEn != null) View.VISIBLE else View.INVISIBLE
        }
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): WordDbViewHolder {
        val binding = ItemWordDatabaseBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return WordDbViewHolder(binding)
    }

    override fun onBindViewHolder(holder: WordDbViewHolder, position: Int) {
        holder.bind(getItem(position))
    }

    class WordDiffCallback : androidx.recyclerview.widget.DiffUtil.ItemCallback<WordDto>() {
        override fun areItemsTheSame(old: WordDto, new: WordDto) = old.id == new.id
        override fun areContentsTheSame(old: WordDto, new: WordDto) = old == new
    }
}
