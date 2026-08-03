package com.learnwords.app.ui.parent

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.util.AttributeSet
import android.view.View
import androidx.core.content.ContextCompat
import com.learnwords.app.R
import com.learnwords.app.data.api.ChildDailyProgress
import kotlin.math.max

class LearningChartView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null
) : View(context, attrs) {
    private val density = resources.displayMetrics.density
    private val correctPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.rgb(34, 197, 94) }
    private val incorrectPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.rgb(239, 68, 68) }
    private val activityPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.rgb(96, 165, 250) }
    private val axisPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = ContextCompat.getColor(context, R.color.colorChartAxis)
        strokeWidth = density
    }
    private val textPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = ContextCompat.getColor(context, R.color.colorChartAxisText)
        textSize = 10f * resources.displayMetrics.scaledDensity
        textAlign = Paint.Align.CENTER
    }
    private var data: List<ChildDailyProgress> = emptyList()

    fun setData(items: List<ChildDailyProgress>) {
        data = items
        contentDescription = items.joinToString("; ") {
            "${it.date}: ${it.correct} correct, ${it.incorrect} incorrect"
        }
        requestLayout()
        invalidate()
    }

    override fun onMeasure(widthMeasureSpec: Int, heightMeasureSpec: Int) {
        val desiredWidth = max(suggestedMinimumWidth, (data.size * 34f * density).toInt())
        val desiredHeight = (210f * density).toInt()
        setMeasuredDimension(
            resolveSize(desiredWidth, widthMeasureSpec),
            resolveSize(desiredHeight, heightMeasureSpec)
        )
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        if (data.isEmpty()) return
        val left = 8f * density
        val right = width - 8f * density
        val chartTop = 10f * density
        val chartBottom = height - 28f * density
        canvas.drawLine(left, chartBottom, right, chartBottom, axisPaint)
        val step = (right - left) / data.size
        val barWidth = minOf(16f * density, step * 0.58f)
        val maxAnswers = max(1, data.maxOf { it.correct + it.incorrect })
        val labelEvery = when {
            data.size <= 7 -> 1
            data.size <= 30 -> 5
            else -> 15
        }

        data.forEachIndexed { index, day ->
            val centerX = left + step * index + step / 2f
            val total = day.correct + day.incorrect
            var bottom = chartBottom
            if (total > 0) {
                val correctHeight = (chartBottom - chartTop) * day.correct / maxAnswers
                if (correctHeight > 0f) {
                    canvas.drawRect(centerX - barWidth / 2f, bottom - correctHeight, centerX + barWidth / 2f, bottom, correctPaint)
                    bottom -= correctHeight
                }
                val incorrectHeight = (chartBottom - chartTop) * day.incorrect / maxAnswers
                if (incorrectHeight > 0f) {
                    canvas.drawRect(centerX - barWidth / 2f, bottom - incorrectHeight, centerX + barWidth / 2f, bottom, incorrectPaint)
                }
            } else if (day.events > 0) {
                canvas.drawRect(centerX - barWidth / 2f, chartBottom - 5f * density, centerX + barWidth / 2f, chartBottom, activityPaint)
            }
            if (index % labelEvery == 0 || index == data.lastIndex) {
                val label = if (day.date.length >= 10) "${day.date.substring(8, 10)}.${day.date.substring(5, 7)}" else day.date
                canvas.drawText(label, centerX, height - 8f * density, textPaint)
            }
        }
    }
}
