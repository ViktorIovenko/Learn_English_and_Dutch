package com.learnwords.app.ui.upload

import androidx.fragment.app.Fragment
import androidx.viewpager2.adapter.FragmentStateAdapter

class UploadPagerAdapter(fragment: Fragment) : FragmentStateAdapter(fragment) {

    override fun getItemCount() = 4

    override fun createFragment(position: Int): Fragment = when (position) {
        0 -> WordDatabaseTabFragment()
        1 -> TopicTabFragment()
        2 -> AddWordsTabFragment()
        3 -> ShareTabFragment()
        else -> AddWordsTabFragment()
    }
}
