package app.parallellingvo.utils

import kotlin.coroutines.AbstractCoroutineContextElement
import kotlin.coroutines.CoroutineContext
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.Job
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext

/** Account changes and account-owned work share one boundary, including late responses. */
object SessionBoundary {
    private val mutex = Mutex()
    private val stateLock = Any()
    private var activeOperation: Job? = null
    private var pendingTransitions = 0
    @Volatile var generation: Long = 0L
        private set

    private class Lease(val generation: Long) : AbstractCoroutineContextElement(Key) {
        companion object Key : CoroutineContext.Key<Lease>
    }

    suspend fun <T> withSession(block: suspend () -> T): T {
        val lease = currentCoroutineContext()[Lease]
        val expected = lease?.generation ?: generation
        if (lease != null) {
            ensureCurrent(expected)
            return block()
        }
        return mutex.withLock {
            ensureCurrent(expected)
            withContext(Lease(expected)) {
                val operation = currentCoroutineContext()[Job]
                synchronized(stateLock) {
                    if (pendingTransitions > 0) throw CancellationException("Account session changing")
                    activeOperation = operation
                }
                try { block() } finally {
                    synchronized(stateLock) { if (activeOperation === operation) activeOperation = null }
                }
            }
        }
    }

    private fun ensureCurrent(expected: Long) {
        if (generation != expected) throw CancellationException("Account session changed")
    }

    suspend fun <T> transition(cancelRequests: () -> Unit = {}, block: suspend () -> T): T =
        withContext(NonCancellable + Dispatchers.IO) {
            val inheritedLease = currentCoroutineContext()[Lease]
            if (inheritedLease != null) {
                ensureCurrent(inheritedLease.generation)
                performTransition(block)
            } else {
                val operation = synchronized(stateLock) {
                    pendingTransitions += 1
                    activeOperation
                }
                try {
                    // Interrupt in-flight audio/AI before waiting for their session lock.
                    operation?.cancel(CancellationException("Account session changing"))
                    cancelRequests()
                    mutex.withLock { performTransition(block) }
                } finally {
                    synchronized(stateLock) { pendingTransitions -= 1 }
                }
            }
        }

    private suspend fun <T> performTransition(block: suspend () -> T): T {
        generation += 1L
        return try {
            withContext(Lease(generation)) { block() }
        } finally { generation += 1L }
    }
}
