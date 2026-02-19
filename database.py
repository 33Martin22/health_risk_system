"""
database.py - SQLite database setup and operations
Handles all database interactions for the Health Risk Assessment System
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = "health_risk.db"


def get_connection():
    """Get a database connection with foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    """Create all tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('patient', 'doctor', 'admin')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    """)

    # Patients table (extended profile)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            date_of_birth TEXT,
            gender TEXT,
            blood_type TEXT,
            phone TEXT,
            address TEXT,
            assigned_doctor_id INTEGER,
            status TEXT DEFAULT 'active',
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (assigned_doctor_id) REFERENCES users(id)
        )
    """)

    # Assessments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            respiratory_rate REAL,
            oxygen_saturation REAL,
            o2_scale REAL,
            systolic_bp REAL,
            heart_rate REAL,
            temperature REAL,
            consciousness TEXT,
            on_oxygen INTEGER,
            risk_level TEXT NOT NULL,
            risk_score REAL,
            notes TEXT,
            assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES users(id)
        )
    """)

    # Doctor notes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctor_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id INTEGER NOT NULL,
            patient_id INTEGER NOT NULL,
            note TEXT NOT NULL,
            is_critical INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (doctor_id) REFERENCES users(id),
            FOREIGN KEY (patient_id) REFERENCES users(id)
        )
    """)

    # Login logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS login_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            ip_address TEXT DEFAULT 'localhost',
            logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# ── USER OPERATIONS ──────────────────────────────────────────

def create_user(username, password_hash, full_name, email, role):
    """Insert a new user into the database."""
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO users (username, password_hash, full_name, email, role)
            VALUES (?, ?, ?, ?, ?)
        """, (username, password_hash, full_name, email, role))
        user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        if role == 'patient':
            conn.execute("INSERT INTO patients (user_id) VALUES (?)", (user_id,))
        conn.commit()
        return True, "User created successfully"
    except sqlite3.IntegrityError as e:
        if "username" in str(e):
            return False, "Username already exists"
        elif "email" in str(e):
            return False, "Email already exists"
        return False, str(e)
    finally:
        conn.close()


def get_user_by_username(username):
    """Fetch a user by username."""
    conn = get_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ? AND is_active = 1", (username,)
    ).fetchone()
    conn.close()
    return dict(user) if user else None


def get_user_by_id(user_id):
    """Fetch a user by ID."""
    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(user) if user else None


def log_login(user_id, action):
    """Log a login or logout event."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO login_logs (user_id, action) VALUES (?, ?)", (user_id, action)
    )
    conn.commit()
    conn.close()


# ── ASSESSMENT OPERATIONS ─────────────────────────────────────

def save_assessment(patient_id, vitals, risk_level, risk_score, notes=""):
    """Save a new assessment record."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO assessments 
        (patient_id, respiratory_rate, oxygen_saturation, o2_scale, systolic_bp,
         heart_rate, temperature, consciousness, on_oxygen, risk_level, risk_score, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        patient_id,
        vitals['respiratory_rate'], vitals['oxygen_saturation'],
        vitals['o2_scale'], vitals['systolic_bp'], vitals['heart_rate'],
        vitals['temperature'], vitals['consciousness'],
        vitals['on_oxygen'], risk_level, risk_score, notes
    ))
    conn.commit()
    conn.close()


def get_patient_assessments(patient_id):
    """Get all assessments for a patient."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM assessments WHERE patient_id = ? ORDER BY assessed_at DESC
    """, (patient_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_patients():
    """Get all patients with their user info."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT u.id, u.full_name, u.email, u.created_at, p.status, p.gender,
               p.assigned_doctor_id,
               (SELECT risk_level FROM assessments WHERE patient_id = u.id 
                ORDER BY assessed_at DESC LIMIT 1) as latest_risk,
               (SELECT COUNT(*) FROM assessments WHERE patient_id = u.id) as total_assessments
        FROM users u
        JOIN patients p ON u.id = p.user_id
        WHERE u.role = 'patient' AND u.is_active = 1
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_doctor_patients(doctor_id):
    """Get all patients assigned to a specific doctor."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT u.id, u.full_name, u.email, u.created_at, p.status, p.gender,
               (SELECT risk_level FROM assessments WHERE patient_id = u.id 
                ORDER BY assessed_at DESC LIMIT 1) as latest_risk,
               (SELECT COUNT(*) FROM assessments WHERE patient_id = u.id) as total_assessments
        FROM users u
        JOIN patients p ON u.id = p.user_id
        WHERE u.role = 'patient' AND p.assigned_doctor_id = ? AND u.is_active = 1
    """, (doctor_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── DOCTOR NOTES ──────────────────────────────────────────────

def add_doctor_note(doctor_id, patient_id, note, is_critical=False):
    """Add a doctor's note for a patient."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO doctor_notes (doctor_id, patient_id, note, is_critical)
        VALUES (?, ?, ?, ?)
    """, (doctor_id, patient_id, note, int(is_critical)))
    conn.commit()
    conn.close()


def get_patient_notes(patient_id):
    """Get all notes for a patient."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT dn.*, u.full_name as doctor_name
        FROM doctor_notes dn
        JOIN users u ON dn.doctor_id = u.id
        WHERE dn.patient_id = ?
        ORDER BY dn.created_at DESC
    """, (patient_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def assign_patient_to_doctor(patient_id, doctor_id):
    """Assign a patient to a doctor."""
    conn = get_connection()
    conn.execute(
        "UPDATE patients SET assigned_doctor_id = ? WHERE user_id = ?",
        (doctor_id, patient_id)
    )
    conn.commit()
    conn.close()


# ── ADMIN ANALYTICS ───────────────────────────────────────────

def get_system_stats():
    """Get overall system statistics for admin dashboard."""
    conn = get_connection()
    stats = {}
    stats['total_patients'] = conn.execute(
        "SELECT COUNT(*) FROM users WHERE role='patient'"
    ).fetchone()[0]
    stats['total_doctors'] = conn.execute(
        "SELECT COUNT(*) FROM users WHERE role='doctor'"
    ).fetchone()[0]
    stats['total_assessments'] = conn.execute(
        "SELECT COUNT(*) FROM assessments"
    ).fetchone()[0]
    stats['high_risk_count'] = conn.execute(
        "SELECT COUNT(*) FROM assessments WHERE risk_level='High'"
    ).fetchone()[0]
    stats['medium_risk_count'] = conn.execute(
        "SELECT COUNT(*) FROM assessments WHERE risk_level='Medium'"
    ).fetchone()[0]
    stats['low_risk_count'] = conn.execute(
        "SELECT COUNT(*) FROM assessments WHERE risk_level='Low'"
    ).fetchone()[0]
    stats['recent_logins'] = conn.execute(
        "SELECT COUNT(*) FROM login_logs WHERE logged_at >= datetime('now', '-1 day')"
    ).fetchone()[0]
    conn.close()
    return stats


def get_all_doctors():
    """Get all doctors."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, full_name, email FROM users WHERE role='doctor' AND is_active=1"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
