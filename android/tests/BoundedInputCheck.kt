package app.parallellingvo.utils

import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.io.IOException
import java.io.InputStream

fun main() {
    for (size in listOf(0, 1, 8192, 9000)) {
        val data = ByteArray(size) { (it % 127).toByte() }
        val output = ByteArrayOutputStream()
        ByteArrayInputStream(data).use { it.copyBoundedTo(output, 9000) }
        check(output.toByteArray().contentEquals(data))
    }
    for (chunk in listOf(1, 8192)) {
        val input = object : InputStream() {
            override fun read(): Int = 42
            override fun read(buffer: ByteArray, offset: Int, length: Int): Int {
                val count = minOf(chunk, length)
                buffer.fill(42, offset, offset + count)
                return count // Unknown length, never EOF.
            }
        }
        val output = ByteArrayOutputStream()
        try {
            input.copyBoundedTo(output, 9000)
            error("Oversized stream accepted")
        } catch (_: IOException) {
            check(output.size() <= 9000)
        }
    }
    println("BoundedInput: 6 checks passed")
}
