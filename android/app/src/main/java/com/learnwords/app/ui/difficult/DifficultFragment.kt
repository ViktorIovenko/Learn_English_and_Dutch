package com.learnwords.app.ui.difficult

import android.os.Bundle
import android.view.*
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.lifecycleScope
import com.learnwords.app.databinding.FragmentDifficultBinding
import com.learnwords.app.utils.toast
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch

class DifficultFragment : Fragment() {

    private var _binding: FragmentDifficultBinding? = null
    private val binding get() = _binding!!
    private val viewModel: DifficultViewModel by viewModels()
    private lateinit var adapter: DifficultWordAdapter

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentDifficultBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        adapter = DifficultWordAdapter(onUnmark = { word ->
            viewModel.unmarkDifficult(word.id)
        })
        binding.rvDifficultWords.adapter = adapter

        binding.swipeRefresh.setOnRefreshListener { viewModel.refresh() }

        lifecycleScope.launch {
            viewModel.words.collectLatest { words ->
                adapter.submitList(words)
                binding.tvEmpty.visibility = if (words.isEmpty()) View.VISIBLE else View.GONE
            }
        }

        lifecycleScope.launch {
            viewModel.uiState.collectLatest { state ->
                binding.swipeRefresh.isRefreshing = state.isLoading
                state.error?.let {
                    requireContext().toast(it)
                    viewModel.clearError()
                }
            }
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
