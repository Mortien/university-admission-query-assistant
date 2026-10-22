"""Small repository layer with MySQL support and SQLite demo fallback."""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent


class AdmissionRepository:
    def __init__(self) -> None:
        self.mysql = os.getenv("DB_DRIVER", "sqlite").lower() == "mysql"
        self.connection = None
        if self.mysql:
            try:
                import mysql.connector
            except ImportError as exc:
                raise RuntimeError("Install mysql-connector-python to use MySQL.") from exc
            self.connection = mysql.connector.connect(
                host=os.getenv("MYSQL_HOST", "localhost"),
                port=int(os.getenv("MYSQL_PORT", "3306")),
                user=os.getenv("MYSQL_USER", "root"),
                password=os.getenv("MYSQL_PASSWORD", ""),
                database=os.getenv("MYSQL_DATABASE", "admission_assistant"),
            )
            self._seed_mysql_if_empty()
        else:
            self.connection = sqlite3.connect(BASE_DIR / "admissions.db", check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            self._initialize_sqlite()

    def _initialize_sqlite(self) -> None:
        self.connection.execute("""CREATE TABLE IF NOT EXISTS faqs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, question TEXT NOT NULL, answer TEXT NOT NULL,
            category TEXT NOT NULL, keywords TEXT DEFAULT '')""")
        self.connection.execute("""CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, degree_level TEXT NOT NULL,
            duration TEXT NOT NULL, annual_fee REAL NOT NULL, currency TEXT NOT NULL DEFAULT 'INR',
            description TEXT NOT NULL)""")
        self._seed_missing_faqs(sqlite=True)
        self._seed_missing_courses(sqlite=True)
        self.connection.commit()

    def _seed_mysql_if_empty(self) -> None:
        cursor = self.connection.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS courses (
            id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(200) NOT NULL UNIQUE,
            degree_level VARCHAR(80) NOT NULL, duration VARCHAR(80) NOT NULL,
            annual_fee DECIMAL(12,2) NOT NULL, currency VARCHAR(8) NOT NULL DEFAULT 'INR',
            description TEXT NOT NULL)""")
        self._seed_missing_faqs(sqlite=False)
        self._seed_missing_courses(sqlite=False)
        self.connection.commit()
        cursor.close()

    def _seed_missing_courses(self, sqlite: bool) -> None:
        placeholder = "?" if sqlite else "%s"
        cursor = self.connection.cursor()
        cursor.execute("SELECT name FROM courses")
        existing = {row[0] for row in cursor.fetchall()}
        rows = [row for row in seed_courses() if row[0] not in existing]
        if not rows:
            cursor.close()
            return
        cursor.executemany(
            f"INSERT INTO courses (name, degree_level, duration, annual_fee, currency, description) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})",
            rows,
        )
        cursor.close()

    def _seed_missing_faqs(self, sqlite: bool) -> None:
        placeholder = "?" if sqlite else "%s"
        cursor = self.connection.cursor()
        cursor.execute("SELECT question FROM faqs")
        existing = {row[0] for row in cursor.fetchall()}
        rows = [row for row in seed_faqs() if row[0] not in existing]
        if rows:
            cursor.executemany(f"INSERT INTO faqs (question, answer, category, keywords) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})", rows)
        cursor.close()

    def all_faqs(self) -> list[dict[str, Any]]:
        cursor = self.connection.cursor()
        cursor.execute("SELECT question, answer, category, keywords FROM faqs")
        rows = cursor.fetchall()
        cursor.close()
        if self.mysql:
            return [dict(zip(("question", "answer", "category", "keywords"), row)) for row in rows]
        return [dict(row) for row in rows]

    def categories(self) -> list[str]:
        cursor = self.connection.cursor()
        cursor.execute("SELECT DISTINCT category FROM faqs ORDER BY category")
        rows = cursor.fetchall()
        cursor.close()
        return [row[0] for row in rows]

    def all_courses(self) -> list[dict[str, Any]]:
        cursor = self.connection.cursor()
        cursor.execute("SELECT name, degree_level, duration, annual_fee, currency, description FROM courses ORDER BY name")
        rows = cursor.fetchall()
        cursor.close()
        names = ("name", "degree_level", "duration", "annual_fee", "currency", "description")
        return [dict(zip(names, row)) for row in rows] if self.mysql else [dict(row) for row in rows]


def seed_faqs() -> list[tuple[str, str, str, str]]:
    return [
        ("What are the eligibility requirements for undergraduate admission?", "Applicants should have completed higher secondary education or an equivalent qualification. Subject and minimum-mark requirements vary by course, so check the course's official admission notice.", "Eligibility", "requirements qualification marks undergraduate subjects"),
        ("Which courses are available?", "The university offers undergraduate and postgraduate programmes across several departments. Browse the Courses section of the official university website for the current list and course-specific details.", "Courses", "programmes degrees departments subjects"),
        ("How do I apply for admission?", "Create an account on the university admission portal, complete the online application, upload the requested documents, pay the application fee, and submit before the deadline. Save the application reference number.", "Application", "apply application portal form submit process"),
        ("What are the tuition fees?", "Fees depend on the programme, year of study, and applicant category. Consult the latest official fee schedule or contact the admissions office before making a payment.", "Fees", "tuition cost payment charges scholarship"),
        ("When is the application deadline?", "Application dates change each admission cycle. Check the current year's official admission notice and portal for opening dates, deadlines, and counselling dates.", "Important Dates", "deadline last date schedule timeline dates"),
        ("Which documents are required?", "Commonly requested documents include academic transcripts and certificates, proof of identity, a recent photograph, and category or entrance-exam certificates where applicable. Follow the course-specific checklist on the portal.", "Documents", "certificates transcripts identity id photo upload"),
        ("Can I edit my application after submitting it?", "Correction windows and edit rules vary by admission cycle. Sign in to the portal and read the current admission notice, or contact the admissions office before submitting another application.", "Policies", "edit correction change submitted application"),
        ("How can I check my application status?", "Sign in to the admission portal with your registered account to view your application status, messages, and any pending document requests.", "Application", "status track application login portal"),
        ("Are scholarships or fee concessions available?", "Scholarships and fee concessions may be available under university or government schemes. Eligibility and application dates vary; check the official scholarship page and submit supporting documents by the stated deadline.", "Fees", "scholarship concession financial aid"),
        ("How do I contact the admissions office?", "Use the contact details published on the university's official admissions website. Include your application number in admission-related enquiries when available.", "Policies", "contact email phone help support"),
        ("Is there an entrance examination?", "Some programmes may require an entrance examination, portfolio, or interview. Requirements differ by course; check the current official course notice before applying.", "Eligibility", "entrance exam test interview portfolio selection"),
        ("How are admission applications reviewed?", "Applications are checked against course eligibility and document requirements. Some programmes may also consider entrance-test results, portfolios, interviews, or counselling rounds.", "Application", "review selection merit shortlist admission criteria"),
        ("Can I apply after the deadline?", "Late applications are accepted only if the university announces an extension or vacancy round. Check the official portal for current notices before submitting or paying a fee.", "Important Dates", "late extension deadline vacancy round last date"),
        ("How do I pay the application fee?", "Use the payment method shown in the official application portal and save the receipt or transaction reference. The application fee and refund rules are set for each admission cycle.", "Application", "application fee pay payment receipt transaction"),
        ("Are scholarships available for students?", "Scholarships or fee concessions may be offered by the university or government. Check each scheme's eligibility rules, required documents, and application dates on the official scholarship page.", "Fees", "scholarships financial aid grants concessions"),
        ("What happens after I receive an admission offer?", "Follow the offer instructions and deadline to accept your place, submit any remaining documents, and pay the stated admission fee. Keep copies of your offer and payment receipt.", "Application", "offer accept confirm seat admission fee enrollment"),
        ("Can I request a refund after paying fees?", "Refund eligibility and deadlines depend on the current university policy and applicable rules. Review the official refund policy before requesting a cancellation or refund.", "Policies", "refund cancellation withdrawal tuition fee return"),
        ("Is campus accommodation available?", "Accommodation availability, eligibility, and charges vary by admission year. Contact the university's student services or accommodation office for current details.", "Policies", "hostel residence housing accommodation dorm"),
        ("Can I pay tuition fees in instalments?", "Instalment options depend on the programme and current university fee policy. Check the official fee schedule or ask the accounts office before choosing a payment plan.", "Fees", "installments instalments payment plan monthly tuition"),
        ("What file format should I use for uploaded documents?", "Use the file types, size limits, and scan quality shown in the application portal. Make sure every page is clear, readable, and correctly oriented before uploading.", "Documents", "upload pdf jpg jpeg size format scan readable"),
        ("Can I correct my application details after submission?", "Use the portal's correction window if one is announced. If a correction option is unavailable, contact admissions with your application reference and the details that need correction.", "Application", "correction edit update application details change"),
        ("What is a waitlist and how will I know if I am selected?", "A waitlist means eligible applicants may be offered a place if seats become available. Check the official portal and your registered email for status changes and response deadlines.", "Important Dates", "waitlist waiting list selection vacant seats offer"),
        ("Can transfer students receive credit for previous study?", "Transfer-credit decisions depend on the programme, prior coursework, and university rules. Submit transcripts and course descriptions to the relevant academic office for an official assessment.", "Eligibility", "transfer credit prior study transfer student equivalency"),
        ("When does student orientation take place?", "Orientation dates are published by the university for each admission cycle. Check your offer communication, student portal, and official academic calendar for the latest schedule.", "Important Dates", "orientation induction welcome week academic calendar"),
        ("Does the university provide disability support?", "Contact the university's student support or accessibility office to discuss available accommodations, documentation, and arrangements for your programme.", "Policies", "disability accessibility accommodation support adjustments"),
        ("Are public transport or campus shuttle options available?", "Transport routes, schedules, and availability vary by campus and term. Check the university's transport or student services information for current details.", "Policies", "bus shuttle transport commute public transit"),
        ("Can I change my course after admission?", "Course changes are subject to seat availability, eligibility, academic approval, and university deadlines. Contact admissions or the academic department before making a decision.", "Policies", "change switch transfer course programme major after admission"),
        ("Where can I find the academic calendar?", "The academic calendar is published through the university's official website or student portal. It includes term dates, examinations, holidays, and other key academic events.", "Important Dates", "academic calendar semester term exam holiday schedule"),
    ]


def seed_courses() -> list[tuple[str, str, str, float, str, str]]:
    """Illustrative demo catalog; replace names and amounts with official data."""
    return [
        ("BSc Computer Science", "Undergraduate", "3 years", 45000, "INR", "Study programming, algorithms, databases, and computer systems."),
        ("BCom", "Undergraduate", "3 years", 30000, "INR", "Study accounting, finance, business, and commerce."),
        ("BA English", "Undergraduate", "3 years", 25000, "INR", "Study literature, language, and communication."),
        ("BBA", "Undergraduate", "3 years", 50000, "INR", "Study management, marketing, finance, and business operations."),
        ("MBA", "Postgraduate", "2 years", 90000, "INR", "Postgraduate programme in management and business leadership."),
        ("BA History", "Undergraduate", "3 years", 26000, "INR", "Explore historical periods, cultures, sources, and research methods."),
        ("BSc Mathematics", "Undergraduate", "3 years", 32000, "INR", "Build foundations in pure mathematics, statistics, and applied problem solving."),
        ("BSc Physics", "Undergraduate", "3 years", 35000, "INR", "Study classical and modern physics with laboratory learning."),
        ("MCom", "Postgraduate", "2 years", 40000, "INR", "Advanced study in commerce, accounting, finance, and business research."),
        ("MCA", "Postgraduate", "2 years", 70000, "INR", "Postgraduate study in software development, computing, and information systems."),
        ("BA Economics", "Undergraduate", "3 years", 28000, "INR", "Study economic theory, public policy, markets, and quantitative methods."),
        ("BSc Chemistry", "Undergraduate", "3 years", 34000, "INR", "Explore chemical principles through lectures, laboratory work, and analysis."),
        ("BSc Biotechnology", "Undergraduate", "3 years", 42000, "INR", "Learn how biology and technology are used in research and applied sciences."),
        ("MA English", "Postgraduate", "2 years", 36000, "INR", "Advanced study in literature, criticism, language, and research."),
        ("MSc Mathematics", "Postgraduate", "2 years", 48000, "INR", "Advanced study in mathematical theory, modelling, and applied methods."),
    ]


def get_repository() -> AdmissionRepository:
    return AdmissionRepository()
