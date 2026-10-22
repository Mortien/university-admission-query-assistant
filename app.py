"""Flask web application for answering university admission questions."""
from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from assistant import AdmissionAssistant
from database import get_repository

BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
repository = get_repository()
assistant = AdmissionAssistant(repository)


@app.get("/")
def index():
    faqs = repository.all_faqs()
    section_specs = [
        ("procedures", "Application procedures", "Application", "A clear path from account creation to submission."),
        ("fees", "Fees and scholarships", "Fees", "Tuition, payment guidance, and possible support."),
        ("dates", "Important dates", "Important Dates", "Deadlines and dates can change each admission cycle."),
        ("documents", "Required documents", "Documents", "Prepare your files before starting the application."),
        ("policies", "Admission policies", "Policies", "Rules, corrections, and official contact information."),
    ]
    sections = [
        {"id": section_id, "title": title, "category": category, "description": description,
         "items": [faq for faq in faqs if faq["category"] == category]}
        for section_id, title, category, description in section_specs
    ]
    return render_template("index.html", categories=repository.categories(), courses=repository.all_courses(), sections=sections)


@app.post("/api/ask")
def ask():
    payload = request.get_json(silent=True) or {}
    question = str(payload.get("question", "")).strip()
    if not question:
        return jsonify({"error": "Please enter a question."}), 400
    if len(question) > 500:
        return jsonify({"error": "Please keep your question under 500 characters."}), 400
    return jsonify(assistant.answer(question))


@app.get("/api/categories")
def categories():
    return jsonify(repository.categories())


@app.get("/api/courses")
def courses():
    return jsonify(repository.all_courses())


if __name__ == "__main__":
    # Bind to the local network so a phone on the same Wi-Fi can open the app.
    app.run(host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG") == "1")
