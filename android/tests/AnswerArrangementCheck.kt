package app.parallellingvo.ui.learn

/** Standalone checks: compile with AnswerArrangement.kt; no Android runtime required. */
fun main() {
    var checks = 0
    fun verify(condition: Boolean, message: String) {
        check(condition) { message }
        checks++
    }
    fun expect(actual: List<Int?>, expected: List<Int?>) {
        verify(actual == expected, "Expected $expected, got $actual")
    }
    expect(AnswerArrangement.place(listOf(null, null, null, null), 2, 4, 3), listOf(null, null, null, 2))
    expect(AnswerArrangement.place(listOf(0, null, 1, null), 2, 4, 2), listOf(0, null, 2, 1))
    expect(AnswerArrangement.place(listOf(null, 0, 1, 2), 3, 4, 2), listOf(0, 1, 3, 2))
    expect(AnswerArrangement.move(listOf(0, 1, 2, 3), 0, 3), listOf(1, 2, 3, 0))
    expect(AnswerArrangement.move(listOf(0, 1, 2, 3), 3, 0), listOf(3, 0, 1, 2))
    expect(AnswerArrangement.move(listOf(0, 1, null, 2), 0, 2), listOf(null, 1, 0, 2))
    // Both 'a' tiles must stay distinct, including when returned and placed again.
    val letters = listOf('a', 'a', ' ', 'b')
    var repeated = listOf<Int?>(0, 1, 2, 3)
    repeated = AnswerArrangement.remove(repeated, 1)
    repeated = AnswerArrangement.place(repeated, 1, letters.size, 1)
    verify(repeated == listOf(0, 1, 2, 3), "Repeated letters or space lost their identity")
    verify(repeated.map { it?.let(letters::get) }.joinToString("") == "aa b", "Whitespace changed")

    val states = mutableListOf<List<Int?>>()
    fun enumerate(prefix: List<Int?>) {
        if (prefix.size == 4) { states.add(prefix); return }
        enumerate(prefix + listOf<Int?>(null))
        for (tile in 0..3) if (tile !in prefix) enumerate(prefix + tile)
    }
    enumerate(emptyList())
    for (slots in states) {
        val before = slots.toList()
        for (tile in -1..6) for (target in -1..4) {
            val result = AnswerArrangement.place(slots, tile, 6, target)
            val canPlace = tile in 0 until 6 && tile !in slots && target in slots.indices && null in slots
            verify(result.size == slots.size, "Insertion changed answer length")
            verify(result.filterNotNull().distinct().size == result.filterNotNull().size, "Insertion duplicated a tile")
            if (canPlace) {
                verify(result[target] == tile, "Insertion missed requested slot")
                verify(result.filterNotNull().filter { it != tile } == slots.filterNotNull(), "Insertion lost/reordered existing tiles")
            } else verify(result == slots, "Invalid insertion changed the answer")
        }
        for (source in -1..4) for (target in -1..4) {
            val result = AnswerArrangement.move(slots, source, target)
            verify(result.size == slots.size, "Move changed answer length")
            verify(result.filterNotNull().sorted() == slots.filterNotNull().sorted(), "Move lost or duplicated tiles")
            val tile = slots.getOrNull(source)
            if (tile != null && target in slots.indices) {
                verify(result[target] == tile, "Move missed requested slot")
                verify(result.filterNotNull().filter { it != tile } == slots.filterNotNull().filter { it != tile }, "Move reordered unrelated tiles")
            } else verify(result == slots, "Invalid move changed the answer")
        }
        for (source in -1..4) {
            val result = AnswerArrangement.remove(slots, source)
            verify(result.size == slots.size, "Removal changed answer length")
            verify(result.filterNotNull() == slots.filterIndexed { index, _ -> index != source }.filterNotNull(), "Removal affected unrelated tiles")
        }
        val firstEmpty = slots.indexOfFirst { it == null }
        val tapped = AnswerArrangement.place(slots, 4, 6, null)
        verify(if (firstEmpty >= 0) tapped[firstEmpty] == 4 else tapped == slots, "Tap placement failed")
        verify(slots == before, "An operation mutated the original answer")
    }
    println("PASS: $checks assertions across ${states.size} sparse/full arrangements, repeated letters and spaces.")
}
