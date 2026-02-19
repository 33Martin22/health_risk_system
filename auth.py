"""
auth.py - Authentication and session management
Handles password hashing, login, logout, and role-based access control
"""

import hashlib
import hmac
import secrets
import streamlit as st
from database import get_user_by_username, create_user, log_login


def hash_password(password: str) -> str:
    """Hash a password using SHA-256 with a salt."""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{pwd_hash}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against its stored hash."""
    try:
        salt, pwd_hash = stored_hash.split(":")
        expected = hashlib.sha256((salt + password).encode()).hexdigest()
        return hmac.compare_digest(expected, pwd_hash)
    except Exception:
        return False


def validate_registration(username, password, confirm_password, full_name, email, role):
    """Validate registration form inputs."""
    errors = []
    if len(username) < 3:
        errors.append("Username must be at least 3 characters.")
    if len(password) < 6:
        errors.append("Password must be at least 6 characters.")
    if password != confirm_password:
        errors.append("Passwords do not match.")
    if not full_name.strip():
        errors.append("Full name is required.")
    if "@" not in email or "." not in email:
        errors.append("Invalid email address.")
    if role not in ['patient', 'doctor', 'admin']:
        errors.append("Invalid role selected.")
    return errors


def register_user(username, password, confirm_password, full_name, email, role):
    """Register a new user after validation."""
    errors = validate_registration(username, password, confirm_password, full_name, email, role)
    if errors:
        return False, errors

    password_hash = hash_password(password)
    success, message = create_user(username, password_hash, full_name, email, role)
    if success:
        return True, ["Registration successful! Please log in."]
    return False, [message]


def login_user(username, password):
    """Authenticate a user and set session state."""
    if not username or not password:
        return False, "Please enter username and password."

    user = get_user_by_username(username)
    if not user:
        return False, "Invalid username or password."

    if not verify_password(password, user['password_hash']):
        return False, "Invalid username or password."

    # Set session state
    st.session_state['logged_in'] = True
    st.session_state['user_id'] = user['id']
    st.session_state['username'] = user['username']
    st.session_state['full_name'] = user['full_name']
    st.session_state['role'] = user['role']
    st.session_state['email'] = user['email']

    log_login(user['id'], 'login')
    return True, "Login successful!"


def logout_user():
    """Clear session state and log the logout."""
    if 'user_id' in st.session_state:
        log_login(st.session_state['user_id'], 'logout')

    keys_to_clear = ['logged_in', 'user_id', 'username', 'full_name', 'role', 'email']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]


def is_logged_in():
    """Check if a user is currently logged in."""
    return st.session_state.get('logged_in', False)


def get_current_user():
    """Get the current logged-in user's info."""
    if not is_logged_in():
        return None
    return {
        'id': st.session_state.get('user_id'),
        'username': st.session_state.get('username'),
        'full_name': st.session_state.get('full_name'),
        'role': st.session_state.get('role'),
        'email': st.session_state.get('email'),
    }


def require_role(allowed_roles: list):
    """Check if current user has one of the allowed roles."""
    user = get_current_user()
    if not user:
        return False
    return user['role'] in allowed_roles
