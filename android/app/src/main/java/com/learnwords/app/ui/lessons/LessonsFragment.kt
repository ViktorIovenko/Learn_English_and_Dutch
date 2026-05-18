package com.learnwords.app.ui.lessons

import android.os.Bundle
import android.view.*
import androidx.appcompat.app.AlertDialog
import androidx.core.os.bundleOf
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import com.learnwords.app.R
import com.learnwords.app.databinding.FragmentLessonsBinding
import com.learnwords.app.utils.gone
import com.learnwords.app.utils.toast
import com.learnwords.app.utils.visible
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch

class LessonsFragment : Fragment() {

    private var _binding: FragmentLessonsBinding? = null
    private val binding get() = _binding!!
    private val viewModel: LessonsViewModel by viewModels()
    private lateinit var adapter: LessonAdapter

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentLessonsBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        adapter = LessonAdapter(
            onLessonClick = { lesson ->
                viewModel.markLessonOpened(lesson.lesson)
                findNavController().navigate(
                    R.id.action_lessonsFragment_to_learnFragment,
                    bundleOf("lesson" to lesson.lesson)
                )
            },
            onHideToggle = { lesson ->
                viewModel.toggleHidden(lesson.lesson, lesson.hidden)
            },
            onSelectForDelete = { lesson ->
                viewModel.toggleDeleteSelection(lesson.lesson)
            }
        )
        binding.rvLessons.adapter = adapter

        binding.swipeRefresh.setOnRefreshListener { viewModel.refresh() }

        binding.btnDeleteMode.setOnClickListener {
            if (viewModel.uiState.value.isDeleteMode) {
                showDeleteConfirmation()
            } else {
                viewModel.enterDeleteMode()
            }
        }

        binding.btnCancelDelete.setOnClickListener {
            viewModel.exitDeleteMode()
        }

        viewLifecycleOwner.lifecycleScope.launch {
            viewModel.lessons.collectLatest { lessons ->
                val binding = _binding ?: return@collectLatest
                val state = viewModel.uiState.value
                val items = lessons.map { entity ->
                    LessonAdapter.LessonItem(
                        entity = entity,
                        isSelected = entity.lesson in state.selectedForDelete,
                        isDeleteMode = state.isDeleteMode
                    )
                }
                adapter.submitList(items)
                binding.tvEmpty.visibility = if (lessons.isEmpty()) View.VISIBLE else View.GONE
            }
        }

        viewLifecycleOwner.lifecycleScope.launch {
            viewModel.uiState.collectLatest { state ->
                val binding = _binding ?: return@collectLatest
                binding.swipeRefresh.isRefreshing = state.isLoading

                if (state.isDeleteMode) {
                    binding.btnDeleteMode.text = "Удалить (${state.selectedForDelete.size})"
                    binding.btnCancelDelete.visible()
                } else {
                    binding.btnDeleteMode.text = "Удалить уроки"
                    binding.btnCancelDelete.gone()
                }

                // Re-submit list when delete mode or selection changes
                val lessons = viewModel.lessons.value
                val items = lessons.map { entity ->
                    LessonAdapter.LessonItem(
                        entity = entity,
                        isSelected = entity.lesson in state.selectedForDelete,
                        isDeleteMode = state.isDeleteMode
                    )
                }
                adapter.submitList(items)

                state.error?.let {
                    requireContext().toast(it)
                    viewModel.clearError()
                }
            }
        }
    }

    private fun showDeleteConfirmation() {
        val count = viewModel.uiState.value.selectedForDelete.size
        if (count == 0) {
            requireContext().toast("Выберите уроки для удаления")
            return
        }
        AlertDialog.Builder(requireContext())
            .setTitle("Удалить уроки")
            .setMessage("Удалить $count урок(а/ов) и все слова в них?")
            .setPositiveButton("Удалить") { _, _ -> viewModel.deleteSelected() }
            .setNegativeButton("Отмена") { _, _ -> viewModel.exitDeleteMode() }
            .show()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
