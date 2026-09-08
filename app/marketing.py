from __future__ import annotations

from flask import Blueprint, abort, render_template

marketing = Blueprint("marketing", __name__)


BLOG_POSTS = [
    {
        "slug": "one-word-three-languages",
        "title": "One word. Three languages. One learning flow.",
        "excerpt": "A simple way to keep several languages connected instead of studying each one in isolation.",
        "date": "2026-09-08",
        "read_time": "4 min read",
        "category": "Method",
        "intro": "Learning several languages at the same time can become confusing when every language lives in a separate notebook, app or routine. LearnWord is built around a different idea: keep related translations together and practise them as one multilingual unit.",
        "sections": [
            {
                "heading": "Build one mental connection",
                "paragraphs": [
                    "Instead of creating separate word lists for each language, place the word and its translations next to each other. This makes comparison fast and keeps the vocabulary connected.",
                    "You can still choose one main learning language while keeping extra translations available when they are useful."
                ],
                "bullets": []
            },
            {
                "heading": "Useful when languages overlap",
                "paragraphs": [
                    "For multilingual learners, similar words, false friends and different sentence structures become easier to notice when the languages are visible together."
                ],
                "bullets": [
                    "Compare translations without switching between apps.",
                    "Keep several target languages inside one lesson.",
                    "Return to difficult words without rebuilding your list."
                ]
            }
        ]
    },
    {
        "slug": "small-lessons-daily-routine",
        "title": "Why small vocabulary lessons are easier to keep",
        "excerpt": "Turn a long list of words into short lessons that are easier to repeat during the day.",
        "date": "2026-09-06",
        "read_time": "3 min read",
        "category": "Study tips",
        "intro": "A vocabulary list feels much lighter when it is divided into clear lessons. The goal is not to finish the biggest list possible, but to create a routine you can repeat consistently.",
        "sections": [
            {
                "heading": "Keep each session focused",
                "paragraphs": [
                    "A short lesson gives you a clear starting and finishing point. It is easier to repeat on a phone, during a commute or in a few free minutes between other tasks."
                ],
                "bullets": [
                    "Create lessons around a topic, chapter or course unit.",
                    "Mark difficult words instead of restarting the entire lesson.",
                    "Use audio when you want to add pronunciation practice."
                ]
            },
            {
                "heading": "Repeat what needs attention",
                "paragraphs": [
                    "Not every word deserves the same amount of time. A separate difficult-words view helps you concentrate on the vocabulary that still needs work."
                ],
                "bullets": []
            }
        ]
    },
    {
        "slug": "multilingual-learning-on-the-go",
        "title": "Multilingual learning that fits on your phone",
        "excerpt": "Lessons, progress, audio and cached study data can make mobile vocabulary practice much more practical.",
        "date": "2026-09-03",
        "read_time": "3 min read",
        "category": "Product",
        "intro": "Language study often happens away from a desk. A lightweight mobile-first interface makes it easier to open a lesson, practise a few words and continue later without navigating through a complex course platform.",
        "sections": [
            {
                "heading": "Designed for quick practice",
                "paragraphs": [
                    "LearnWord combines a Telegram bot with a Telegram Mini App, so navigation and study can stay close to the messaging app you already use."
                ],
                "bullets": [
                    "Open your lessons quickly.",
                    "Track progress word by word.",
                    "Use cached data for a smoother mobile experience.",
                    "Keep pronunciation audio close to the vocabulary."
                ]
            },
            {
                "heading": "Start simple, expand later",
                "paragraphs": [
                    "The same structure can grow from three languages to a larger multilingual setup without changing the basic learning habit: lesson, word, translations, repetition."
                ],
                "bullets": []
            }
        ]
    }
]


@marketing.get("/site")
def landing():
    return render_template("marketing/landing.html", posts=BLOG_POSTS[:3])


@marketing.get("/blog")
def blog():
    return render_template("marketing/blog.html", posts=BLOG_POSTS)


@marketing.get("/blog/<slug>")
def blog_post(slug: str):
    post = next((item for item in BLOG_POSTS if item["slug"] == slug), None)
    if not post:
        abort(404)
    return render_template("marketing/blog_post.html", post=post)


def init_marketing(app) -> None:
    app.register_blueprint(marketing)
