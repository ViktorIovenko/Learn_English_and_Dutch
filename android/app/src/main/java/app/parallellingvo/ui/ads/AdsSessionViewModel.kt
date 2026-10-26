package app.parallellingvo.ui.ads

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel

/** One set per navigation entry; survives view recreation and rotation. */
class AdsSessionViewModel(private val state: SavedStateHandle) : ViewModel() {
    fun recordOnce(key: String): Boolean {
        val keys = state.get<ArrayList<String>>("ad_impressions") ?: arrayListOf()
        if (key in keys) return false
        state["ad_impressions"] = ArrayList(keys + key)
        return true
    }
}
