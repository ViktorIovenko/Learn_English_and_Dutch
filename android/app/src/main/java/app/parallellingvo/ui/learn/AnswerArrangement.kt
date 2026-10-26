package app.parallellingvo.ui.learn

/** Slots contain source tile IDs, so repeated letters remain distinct. */
internal object AnswerArrangement {
    fun place(slots: List<Int?>, tile: Int, tileCount: Int, target: Int?): List<Int?> {
        if (tile !in 0 until tileCount || tile in slots) return slots
        val destination = target ?: slots.indexOfFirst { it == null }
        if (destination !in slots.indices) return slots
        val result = slots.toMutableList()
        if (result[destination] != null) {
            val empty = (destination + 1..result.lastIndex).firstOrNull { result[it] == null }
                ?: (destination - 1 downTo 0).firstOrNull { result[it] == null }
                ?: return slots
            if (empty > destination) {
                for (index in empty downTo destination + 1) result[index] = result[index - 1]
            } else {
                for (index in empty until destination) result[index] = result[index + 1]
            }
        }
        result[destination] = tile
        return result
    }

    fun remove(slots: List<Int?>, source: Int): List<Int?> {
        if (source !in slots.indices || slots[source] == null) return slots
        return slots.toMutableList().apply { this[source] = null }
    }

    fun move(slots: List<Int?>, source: Int, target: Int): List<Int?> {
        if (source !in slots.indices || target !in slots.indices || slots[source] == null || source == target) return slots
        val result = slots.toMutableList()
        if (result[target] == null) {
            result[target] = result[source]
            result[source] = null
        } else {
            val tile = result.removeAt(source)
            result.add(target, tile)
        }
        return result
    }
}
