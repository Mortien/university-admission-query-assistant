# University of Rozhok Admission Query Assistant

An intermediate-level four-person web application that answers common prospective-student questions about admission. It covers eligibility, courses, application steps, fees, dates, documents, and policies.

## Features

- Flask API and responsive HTML/CSS/JavaScript chat interface
- Chat questions can be dictated with the browser's built-in speech recognition where supported
- Purple neon admissions landing page with custom university crest, navigation, course cards, and expandable guidance subsections
- Campus life gallery with clickable classroom, campus building, and cafeteria photos
- Dedicated application procedures, fees, important dates, document, and admission policy sections
- NLTK token cleanup and semantic question matching with Sentence Transformers
- MySQL schema and seed data; SQLite is used by default for a quick local demo
- Course catalog with programme duration and course-specific annual tuition fees
- Expanded demo FAQ content covering entrance exams, application review, late applications, payment, scholarships, offers, refunds, and accommodation
- Lexical matching fallback when the transformer package or model is unavailable
- Clear low-confidence response rather than presenting a weak match as fact

## Run locally

1. Create and activate a Python virtual environment.
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and adjust database settings if needed. SQLite is the default and needs no setup.
4. Start the server: `python app.py`
5. Open `http://127.0.0.1:5000`.

The Sentence Transformer model downloads on first successful use and may take a little while. If unavailable, keyword-overlap matching is used. Replace the sample answers with the chosen university's verified information before using this for real applicants. Course names and INR fees are illustrative demo values; replace them with official information in `seed_courses()` in `database.py` and the matching seed inserts in `schema.sql`. On startup, SQLite and MySQL receive any missing demo FAQ and course records without duplicating existing entries.

## Use MySQL

1. Create the database and table by running `schema.sql` in MySQL.
2. Set `DB_DRIVER=mysql` and fill in `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, and `MYSQL_DATABASE` in your environment.
3. Run `python app.py`. The app seeds the FAQ table if it is empty.

## Four-person work split

1. **NLP:** matching pipeline, NLTK preprocessing, confidence threshold, and sample question evaluation.
2. **Backend:** Flask routes, validation, repository integration, and error handling.
3. **Database/content:** MySQL schema, FAQ seed data, and validation of university-specific answers.
4. **Frontend/integration:** responsive chat page, suggested topics, API integration, and final integration review.

## Project structure

```text
app.py              Flask routes
assistant.py        NLP matching logic
database.py         SQLite/MySQL data access and demo seed data
schema.sql          MySQL database setup
templates/index.html
static/app.js
static/style.css
```
