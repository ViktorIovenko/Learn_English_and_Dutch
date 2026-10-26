package app.parallellingvo.utils

import java.io.IOException
import java.io.InputStream
import java.io.OutputStream

/** Enforce the limit while streaming, including chunked or dishonest responses. */
fun InputStream.copyBoundedTo(output: OutputStream, maxBytes: Long) {
    val buffer = ByteArray(8192)
    var total = 0L
    while (true) {
        val count = read(buffer)
        if (count < 0) return
        total += count
        if (total > maxBytes) throw IOException("Response exceeds size limit")
        output.write(buffer, 0, count)
    }
}
