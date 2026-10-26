package app.parallellingvo.utils

import kotlinx.coroutines.*

fun main() = runBlocking {
    SessionBoundary.withSession { SessionBoundary.withSession { check(SessionBoundary.generation % 2L == 0L) } }
    val start = SessionBoundary.generation
    val entered = CompletableDeferred<Unit>()
    val release = CompletableDeferred<Unit>()
    val active = launch {
        SessionBoundary.withSession { entered.complete(Unit); release.await() }
    }
    entered.await()
    var staleExecuted = false
    val stale = launch(start = CoroutineStart.UNDISPATCHED) {
        SessionBoundary.withSession { staleExecuted = true }
    }
    val transition = launch {
        SessionBoundary.transition {
            check(SessionBoundary.generation % 2L == 1L)
            SessionBoundary.withSession { }
        }
    }
    joinAll(active, transition, stale)
    check(active.isCancelled)
    check(stale.isCancelled && !staleExecuted)
    check(SessionBoundary.generation == start + 2)
    val cleanupEntered = CompletableDeferred<Unit>()
    val finishCleanup = CompletableDeferred<Unit>()
    var cleaned = false
    val logout = launch {
        SessionBoundary.transition { cleanupEntered.complete(Unit); finishCleanup.await(); cleaned = true }
    }
    cleanupEntered.await()
    logout.cancel()
    finishCleanup.complete(Unit)
    logout.join()
    check(cleaned && SessionBoundary.generation % 2L == 0L)
    try { SessionBoundary.transition { throw IllegalStateException("cleanup failure") } }
    catch (_: IllegalStateException) { }
    check(SessionBoundary.generation % 2L == 0L)
    println("SessionBoundary: nested calls, transition ordering, stale work and cancellation checks passed")
}
