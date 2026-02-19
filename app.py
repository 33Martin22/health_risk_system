"""
app.py - Main Streamlit Application
AI-Powered Health Risk Assessment and Monitoring System
"""

import streamlit as st
import pandas as pd
from datetime import datetime

# Page config MUST be first
st.set_page_config(
    page_title="Health Risk Assessment System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Local imports
from database import initialize_database, save_assessment, get_patient_assessments, \
    get_all_patients, get_doctor_patients, add_doctor_note, get_patient_notes, \
    assign_patient_to_doctor, get_system_stats, get_all_doctors, get_user_by_id
from auth import login_user, logout_user, register_user, is_logged_in, get_current_user
from model import predict_risk, check_abnormal_vitals, RECOMMENDATIONS
from utils import (apply_theme, render_header, render_metric_card, render_risk_badge,
                   render_risk_gauge, render_probability_bars, render_assessment_history_chart,
                   render_risk_distribution_pie, render_vitals_chart,
                   highlight_abnormal_vitals, simulated_email_alert, format_datetime)
from reports import generate_pdf_report

# Initialize DB on startup
initialize_database()
apply_theme()


# ══════════════════════════════════════════════════════════════
# AUTH PAGES
# ══════════════════════════════════════════════════════════════

def page_login():
    """Login page."""
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center; padding: 40px 0 20px;">
            <div style="font-size:4rem;">🏥</div>
            <h1 style="font-family:'DM Serif Display',serif;color:#1a4a7a;font-size:2rem;margin:0;">
                Health Risk System
            </h1>
            <p style="color:#64748b;margin-top:8px;">AI-Powered Health Assessment Platform</p>
        </div>
        """, unsafe_allow_html=True)

        tab_login, tab_register = st.tabs(["🔐 Login", "📝 Register"])

        with tab_login:
            st.markdown("<br>", unsafe_allow_html=True)
            username = st.text_input("Username", placeholder="Enter your username", key="login_user")
            password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_pass")

            if st.button("Login →", key="btn_login"):
                if username and password:
                    success, message = login_user(username, password)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("Please fill in all fields.")

            st.markdown("""
            <div style="background:#f0f9ff;border-radius:10px;padding:14px;margin-top:16px;font-size:0.85rem;color:#0369a1;">
                <strong>Demo Accounts:</strong><br>
                👤 Patient: <code>patient1</code> / <code>pass123</code><br>
                👨‍⚕️ Doctor: <code>doctor1</code> / <code>pass123</code><br>
                🔑 Admin: <code>admin</code> / <code>admin123</code>
            </div>
            """, unsafe_allow_html=True)

        with tab_register:
            st.markdown("<br>", unsafe_allow_html=True)
            reg_name = st.text_input("Full Name", placeholder="John Doe", key="reg_name")
            reg_email = st.text_input("Email", placeholder="john@example.com", key="reg_email")
            reg_user = st.text_input("Username", placeholder="johndoe", key="reg_user")
            reg_role = st.selectbox("Role", ["patient", "doctor"], key="reg_role",
                                    format_func=lambda x: "👤 Patient" if x == "patient" else "👨‍⚕️ Doctor")
            reg_pass = st.text_input("Password", type="password", key="reg_pass")
            reg_confirm = st.text_input("Confirm Password", type="password", key="reg_confirm")

            if st.button("Create Account →", key="btn_register"):
                success, messages = register_user(reg_user, reg_pass, reg_confirm, reg_name, reg_email, reg_role)
                if success:
                    st.success(messages[0])
                else:
                    for msg in messages:
                        st.error(msg)


# ══════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════

def render_sidebar():
    """Render the sidebar navigation."""
    user = get_current_user()
    with st.sidebar:
        st.markdown(f"""
        <div style="padding:20px 10px 10px; text-align:center;">
            <div style="width:60px;height:60px;border-radius:50%;background:rgba(255,255,255,0.2);
                        display:flex;align-items:center;justify-content:center;
                        font-size:1.8rem;margin:0 auto 10px;">
                {'👤' if user['role']=='patient' else '👨‍⚕️' if user['role']=='doctor' else '🔑'}
            </div>
            <div style="font-weight:700;font-size:1rem;">{user['full_name']}</div>
            <div style="font-size:0.8rem;opacity:0.7;margin-top:4px;text-transform:capitalize;">
                {user['role']}
            </div>
        </div>
        <hr style="border-color:rgba(255,255,255,0.15);margin:10px 0;">
        """, unsafe_allow_html=True)

        if user['role'] == 'patient':
            pages = {
                "🩺 Risk Assessment": "assess",
                "📊 My Dashboard": "dashboard",
                "📋 My History": "history",
            }
        elif user['role'] == 'doctor':
            pages = {
                "🏠 Doctor Portal": "doctor_home",
                "👥 My Patients": "patients",
                "🔍 Search Patients": "search",
            }
        else:  # admin
            pages = {
                "📈 Admin Dashboard": "admin",
                "👥 All Patients": "all_patients",
                "📋 Audit Logs": "audit",
            }

        if 'current_page' not in st.session_state:
            st.session_state['current_page'] = list(pages.values())[0]

        for label, page_key in pages.items():
            is_active = st.session_state.get('current_page') == page_key
            btn_style = "background:rgba(255,255,255,0.2);" if is_active else ""
            if st.button(label, key=f"nav_{page_key}", use_container_width=True):
                st.session_state['current_page'] = page_key
                st.rerun()

        st.markdown("<br>" * 3, unsafe_allow_html=True)
        if st.button("🚪 Logout", key="btn_logout", use_container_width=True):
            logout_user()
            st.rerun()

    return st.session_state.get('current_page', list(pages.values())[0])


# ══════════════════════════════════════════════════════════════
# PATIENT PAGES
# ══════════════════════════════════════════════════════════════

def page_assess():
    """Risk Assessment page for patients."""
    user = get_current_user()
    render_header("Risk Assessment", "Enter your current vital signs for AI-powered risk classification")

    with st.form("vitals_form"):
        st.markdown('<div class="section-title">📋 Vital Signs Input</div>', unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            respiratory_rate = st.number_input("🌬️ Respiratory Rate (breaths/min)", min_value=0, max_value=60, value=16)
            oxygen_saturation = st.number_input("💨 Oxygen Saturation (%)", min_value=50, max_value=100, value=98)
            o2_scale = st.number_input("🔵 O2 Scale", min_value=0, max_value=5, value=1)

        with col2:
            systolic_bp = st.number_input("🩸 Systolic BP (mmHg)", min_value=50, max_value=300, value=120)
            heart_rate = st.number_input("❤️ Heart Rate (bpm)", min_value=20, max_value=250, value=80)
            temperature = st.number_input("🌡️ Temperature (°C)", min_value=30.0, max_value=45.0, value=37.0, step=0.1)

        with col3:
            consciousness = st.selectbox("🧠 Consciousness Level", 
                options=['A', 'V', 'P', 'U'],
                format_func=lambda x: {
                    'A': '🟢 A — Alert',
                    'V': '🟡 V — Verbal Response',
                    'P': '🟠 P — Pain Response',
                    'U': '🔴 U — Unresponsive'
                }[x]
            )
            on_oxygen = st.selectbox("🫁 Currently on Oxygen?",
                options=[0, 1],
                format_func=lambda x: "✅ Yes" if x == 1 else "❌ No"
            )
            notes = st.text_area("📝 Additional Notes (optional)", height=108)

        submitted = st.form_submit_button("🔍 Assess Risk Now", use_container_width=True)

    if submitted:
        vitals = {
            'respiratory_rate': respiratory_rate,
            'oxygen_saturation': oxygen_saturation,
            'o2_scale': o2_scale,
            'systolic_bp': systolic_bp,
            'heart_rate': heart_rate,
            'temperature': temperature,
            'consciousness': consciousness,
            'on_oxygen': on_oxygen,
        }

        with st.spinner("🤖 Analyzing vitals..."):
            risk_level, risk_score, probabilities = predict_risk(vitals)
            abnormal = check_abnormal_vitals(vitals)

        # Save to DB
        save_assessment(user['id'], vitals, risk_level, risk_score, notes)

        # Results
        st.markdown("---")
        st.markdown('<div class="section-title">📊 Assessment Results</div>', unsafe_allow_html=True)

        col1, col2 = st.columns([1, 1])

        with col1:
            render_risk_badge(risk_level)
            st.plotly_chart(render_risk_gauge(risk_score, risk_level), use_container_width=True)

        with col2:
            st.plotly_chart(render_probability_bars(probabilities), use_container_width=True)
            highlight_abnormal_vitals(abnormal)

        simulated_email_alert(user['full_name'], risk_level)

        # Recommendations
        st.markdown("---")
        st.markdown('<div class="section-title">💊 Recommendations</div>', unsafe_allow_html=True)
        alert_class = f"alert-{risk_level.lower()}"
        recs = RECOMMENDATIONS.get(risk_level, [])
        recs_html = "".join([f"<div style='margin:4px 0;'>{r}</div>" for r in recs])
        st.markdown(f'<div class="{alert_class}">{recs_html}</div>', unsafe_allow_html=True)

        # PDF Download
        st.markdown("---")
        pdf_bytes = generate_pdf_report(
            patient_info=user,
            vitals=vitals,
            risk_level=risk_level,
            risk_score=risk_score,
            probabilities=probabilities,
            recommendations=recs,
            abnormal_vitals=abnormal
        )
        st.download_button(
            label="📄 Download PDF Report",
            data=pdf_bytes,
            file_name=f"health_report_{user['username']}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )


def page_patient_dashboard():
    """Patient dashboard with charts."""
    user = get_current_user()
    render_header("My Health Dashboard", f"Welcome back, {user['full_name']}")

    assessments = get_patient_assessments(user['id'])

    if not assessments:
        st.info("No assessments yet. Go to Risk Assessment to get started!")
        return

    latest = assessments[0]
    total = len(assessments)
    high_count = sum(1 for a in assessments if a['risk_level'] == 'High')

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card("Total Assessments", total, "📊", "")
    with col2:
        color = {'Low': 'success', 'Medium': 'warning', 'High': 'danger'}.get(latest['risk_level'], '')
        render_metric_card("Latest Risk", latest['risk_level'], "🩺", color)
    with col3:
        render_metric_card("High Risk Episodes", high_count, "⚠️", "danger" if high_count > 0 else "success")
    with col4:
        render_metric_card("Last Assessed", format_datetime(latest['assessed_at'])[:10], "📅", "")

    col1, col2 = st.columns(2)
    with col1:
        fig = render_assessment_history_chart(assessments)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = render_risk_distribution_pie(assessments)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    fig = render_vitals_chart(assessments)
    if fig:
        st.plotly_chart(fig, use_container_width=True)


def page_patient_history():
    """Patient assessment history table."""
    user = get_current_user()
    render_header("Assessment History", "All your previous health assessments")

    assessments = get_patient_assessments(user['id'])

    if not assessments:
        st.info("No assessments found.")
        return

    for a in assessments:
        risk = a['risk_level']
        color = {'Low': '#d1fae5', 'Medium': '#fef3c7', 'High': '#fee2e2'}.get(risk, '#f8fafc')
        border = {'Low': '#2ecc71', 'Medium': '#f39c12', 'High': '#e74c3c'}.get(risk, '#e2e8f0')

        with st.expander(f"📋 {format_datetime(a['assessed_at'])} — {risk} Risk"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Risk Level", risk)
                st.metric("Confidence", f"{a['risk_score']:.1f}%")
            with col2:
                st.metric("Heart Rate", f"{a['heart_rate']} bpm")
                st.metric("Respiratory Rate", f"{a['respiratory_rate']}")
            with col3:
                st.metric("SpO2", f"{a['oxygen_saturation']}%")
                st.metric("Systolic BP", f"{a['systolic_bp']} mmHg")
            if a.get('notes'):
                st.markdown(f"**Notes:** {a['notes']}")


# ══════════════════════════════════════════════════════════════
# DOCTOR PAGES
# ══════════════════════════════════════════════════════════════

def page_doctor_home():
    """Doctor portal home."""
    user = get_current_user()
    render_header("Doctor Portal", f"Welcome, Dr. {user['full_name']}")

    patients = get_doctor_patients(user['id'])
    all_p = get_all_patients()

    col1, col2, col3 = st.columns(3)
    with col1:
        render_metric_card("My Patients", len(patients), "👥", "")
    with col2:
        high_risk = sum(1 for p in patients if p.get('latest_risk') == 'High')
        render_metric_card("High Risk Patients", high_risk, "🚨", "danger" if high_risk > 0 else "success")
    with col3:
        render_metric_card("Total Assessments", sum(p.get('total_assessments', 0) for p in patients), "📊", "")

    # Critical patients alert
    critical = [p for p in patients if p.get('latest_risk') == 'High']
    if critical:
        st.markdown("### 🚨 Critical Patients Requiring Attention")
        for p in critical:
            st.markdown(f"""
            <div class="alert-high">
                🔴 <strong>{p['full_name']}</strong> — High Risk | 
                {p['total_assessments']} assessments | {p['email']}
            </div>
            """, unsafe_allow_html=True)


def page_doctor_patients():
    """Doctor's patient list with notes."""
    user = get_current_user()
    render_header("My Patients", "Manage and monitor your assigned patients")

    patients = get_doctor_patients(user['id'])

    if not patients:
        st.info("No patients assigned to you yet.")

        # Assign patients
        st.markdown("### Assign a Patient")
        all_p = get_all_patients()
        unassigned = [p for p in all_p if not p.get('assigned_doctor_id')]
        if unassigned:
            selected = st.selectbox("Select patient to assign",
                options=[p['id'] for p in unassigned],
                format_func=lambda x: next(p['full_name'] for p in unassigned if p['id'] == x)
            )
            if st.button("Assign to Me"):
                assign_patient_to_doctor(selected, user['id'])
                st.success("Patient assigned!")
                st.rerun()
        return

    for p in patients:
        risk = p.get('latest_risk', 'Unknown')
        color_cls = {'Low': 'success', 'Medium': 'warning', 'High': 'danger'}.get(risk, '')

        with st.expander(f"👤 {p['full_name']} — {risk or 'No assessment'} Risk"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Email:** {p['email']}")
                st.write(f"**Total Assessments:** {p['total_assessments']}")
                st.write(f"**Latest Risk:** {risk or 'N/A'}")
            with col2:
                # View patient assessments
                assessments = get_patient_assessments(p['id'])
                if assessments:
                    latest = assessments[0]
                    st.metric("Last HR", f"{latest['heart_rate']} bpm")
                    st.metric("Last SpO2", f"{latest['oxygen_saturation']}%")

            # Doctor notes
            st.markdown("**📝 Add Note:**")
            note_text = st.text_area("Note", key=f"note_{p['id']}", height=80)
            is_critical = st.checkbox("Mark as Critical", key=f"crit_{p['id']}")
            if st.button("Save Note", key=f"save_note_{p['id']}"):
                if note_text:
                    add_doctor_note(user['id'], p['id'], note_text, is_critical)
                    st.success("Note saved!")
                    st.rerun()

            # Show existing notes
            notes = get_patient_notes(p['id'])
            if notes:
                st.markdown("**Previous Notes:**")
                for note in notes[:3]:
                    crit_badge = "🚨 CRITICAL — " if note['is_critical'] else ""
                    st.markdown(f"""
                    <div style="background:#f8fafc;border-radius:8px;padding:10px;margin:4px 0;
                                border-left:3px solid {'#e74c3c' if note['is_critical'] else '#1a4a7a'};">
                        <small style="color:#64748b;">{crit_badge}{format_datetime(note['created_at'])}</small><br>
                        {note['note']}
                    </div>
                    """, unsafe_allow_html=True)

            # Assessment chart
            if len(assessments) >= 2:
                fig = render_assessment_history_chart(assessments)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)


def page_doctor_search():
    """Search all patients."""
    render_header("Search Patients", "Find and view any patient's records")

    search_query = st.text_input("🔍 Search by name or email", placeholder="Type to search...")
    all_patients = get_all_patients()

    if search_query:
        results = [p for p in all_patients if
                   search_query.lower() in p['full_name'].lower() or
                   search_query.lower() in p['email'].lower()]
    else:
        results = all_patients

    st.markdown(f"**{len(results)} patient(s) found**")

    for p in results:
        risk = p.get('latest_risk', 'N/A')
        with st.expander(f"👤 {p['full_name']} ({p['email']}) — {risk} Risk"):
            assessments = get_patient_assessments(p['id'])
            st.write(f"Total Assessments: {p['total_assessments']}")
            if assessments:
                df = pd.DataFrame(assessments[:10])
                cols = ['assessed_at', 'risk_level', 'risk_score', 'heart_rate',
                        'respiratory_rate', 'oxygen_saturation', 'systolic_bp']
                st.dataframe(df[cols], use_container_width=True)


# ══════════════════════════════════════════════════════════════
# ADMIN PAGES
# ══════════════════════════════════════════════════════════════

def page_admin_dashboard():
    """Admin analytics dashboard."""
    render_header("Admin Dashboard", "System-wide analytics and monitoring")

    stats = get_system_stats()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card("Total Patients", stats['total_patients'], "👥", "")
    with col2:
        render_metric_card("Total Doctors", stats['total_doctors'], "👨‍⚕️", "")
    with col3:
        render_metric_card("Total Assessments", stats['total_assessments'], "📊", "")
    with col4:
        render_metric_card("Logins (24h)", stats['recent_logins'], "🔐", "")

    col1, col2, col3 = st.columns(3)
    with col1:
        render_metric_card("High Risk", stats['high_risk_count'], "🔴", "danger")
    with col2:
        render_metric_card("Medium Risk", stats['medium_risk_count'], "🟡", "warning")
    with col3:
        render_metric_card("Low Risk", stats['low_risk_count'], "🟢", "success")

    # Risk distribution chart
    import plotly.express as px
    risk_data = {
        'Risk Level': ['High', 'Medium', 'Low'],
        'Count': [stats['high_risk_count'], stats['medium_risk_count'], stats['low_risk_count']]
    }
    df = pd.DataFrame(risk_data)
    fig = px.bar(df, x='Risk Level', y='Count',
                 color='Risk Level',
                 color_discrete_map={'High': '#e74c3c', 'Medium': '#f39c12', 'Low': '#2ecc71'},
                 title='System-wide Risk Distribution')
    fig.update_layout(paper_bgcolor='white', plot_bgcolor='#f8fafc',
                      font={'family': 'DM Sans'}, height=300)
    st.plotly_chart(fig, use_container_width=True)


def page_all_patients():
    """Admin view of all patients."""
    render_header("All Patients", "Complete patient registry")

    patients = get_all_patients()
    doctors = get_all_doctors()
    doctor_map = {d['id']: d['full_name'] for d in doctors}

    st.markdown(f"**Total patients: {len(patients)}**")

    df = pd.DataFrame(patients)
    if not df.empty:
        df['assigned_doctor'] = df['assigned_doctor_id'].map(doctor_map).fillna('Unassigned')
        display_cols = ['full_name', 'email', 'latest_risk', 'total_assessments',
                        'assigned_doctor', 'status', 'created_at']
        available = [c for c in display_cols if c in df.columns]
        st.dataframe(df[available], use_container_width=True)

        # Assign doctors
        st.markdown("### Assign Doctor to Patient")
        col1, col2, col3 = st.columns(3)
        with col1:
            patient_sel = st.selectbox("Patient", options=[p['id'] for p in patients],
                                       format_func=lambda x: next(p['full_name'] for p in patients if p['id'] == x))
        with col2:
            doctor_sel = st.selectbox("Doctor", options=[d['id'] for d in doctors],
                                      format_func=lambda x: next(d['full_name'] for d in doctors if d['id'] == x))
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Assign"):
                assign_patient_to_doctor(patient_sel, doctor_sel)
                st.success("Patient assigned!")
                st.rerun()


def page_audit_logs():
    """Admin audit log viewer."""
    from database import get_connection
    render_header("Audit Logs", "System login and activity logs")

    conn = get_connection()
    logs = conn.execute("""
        SELECT ll.*, u.username, u.role FROM login_logs ll
        JOIN users u ON ll.user_id = u.id
        ORDER BY ll.logged_at DESC LIMIT 100
    """).fetchall()
    conn.close()

    df = pd.DataFrame([dict(r) for r in logs])
    if not df.empty:
        st.dataframe(df[['logged_at', 'username', 'role', 'action', 'ip_address']],
                     use_container_width=True)
    else:
        st.info("No logs yet.")


# ══════════════════════════════════════════════════════════════
# MAIN ROUTER
# ══════════════════════════════════════════════════════════════

def main():
    if not is_logged_in():
        page_login()
        return

    user = get_current_user()
    current_page = render_sidebar()

    if user['role'] == 'patient':
        if current_page == 'assess':
            page_assess()
        elif current_page == 'dashboard':
            page_patient_dashboard()
        elif current_page == 'history':
            page_patient_history()

    elif user['role'] == 'doctor':
        if current_page == 'doctor_home':
            page_doctor_home()
        elif current_page == 'patients':
            page_doctor_patients()
        elif current_page == 'search':
            page_doctor_search()

    elif user['role'] == 'admin':
        if current_page == 'admin':
            page_admin_dashboard()
        elif current_page == 'all_patients':
            page_all_patients()
        elif current_page == 'audit':
            page_audit_logs()


if __name__ == "__main__":
    main()
