"""
utils.py - Utility functions and UI helpers
Shared helper functions for visualizations, formatting, and UI components
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime
from model import RISK_COLORS, VITAL_RANGES


def apply_theme():
    """Apply the hospital-style CSS theme."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Serif+Display&display=swap');

    :root {
        --primary: #1a4a7a;
        --primary-light: #2563a8;
        --accent: #00b4d8;
        --success: #2ecc71;
        --warning: #f39c12;
        --danger: #e74c3c;
        --bg: #f0f4f8;
        --card-bg: #ffffff;
        --text: #1e293b;
        --text-muted: #64748b;
        --border: #e2e8f0;
        --sidebar-bg: #1a4a7a;
    }

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
        color: var(--text);
    }

    .stApp { background-color: var(--bg); }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a4a7a 0%, #0f2d4f 100%);
    }
    section[data-testid="stSidebar"] * { color: white !important; }
    section[data-testid="stSidebar"] .stSelectbox label { color: rgba(255,255,255,0.7) !important; }

    /* Cards */
    .metric-card {
        background: white;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        border-left: 4px solid var(--primary);
        margin-bottom: 16px;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .metric-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.1); }
    .metric-card.success { border-left-color: var(--success); }
    .metric-card.warning { border-left-color: var(--warning); }
    .metric-card.danger  { border-left-color: var(--danger); }

    /* Risk badge */
    .risk-badge {
        display: inline-block;
        padding: 8px 20px;
        border-radius: 50px;
        font-weight: 700;
        font-size: 1rem;
        letter-spacing: 0.5px;
    }
    .risk-low    { background: #d1fae5; color: #065f46; }
    .risk-medium { background: #fef3c7; color: #92400e; }
    .risk-high   { background: #fee2e2; color: #991b1b; }

    /* Section headers */
    .section-title {
        font-family: 'DM Serif Display', serif;
        font-size: 1.6rem;
        color: var(--primary);
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 2px solid var(--border);
    }

    /* Alert boxes */
    .alert-high {
        background: #fee2e2;
        border: 1px solid #fca5a5;
        border-radius: 12px;
        padding: 16px;
        margin: 12px 0;
        color: #991b1b;
        font-weight: 500;
    }
    .alert-medium {
        background: #fef3c7;
        border: 1px solid #fcd34d;
        border-radius: 12px;
        padding: 16px;
        margin: 12px 0;
        color: #92400e;
        font-weight: 500;
    }
    .alert-low {
        background: #d1fae5;
        border: 1px solid #6ee7b7;
        border-radius: 12px;
        padding: 16px;
        margin: 12px 0;
        color: #065f46;
        font-weight: 500;
    }

    /* Abnormal vital highlight */
    .vital-abnormal {
        background: #fff7ed;
        border: 1px solid #fed7aa;
        border-radius: 8px;
        padding: 8px 12px;
        margin: 4px 0;
        color: #c2410c;
        font-size: 0.9rem;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #1a4a7a, #2563a8);
        color: white !important;
        border: none;
        border-radius: 10px;
        padding: 10px 24px;
        font-weight: 600;
        font-family: 'DM Sans', sans-serif;
        transition: all 0.2s;
        width: 100%;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #2563a8, #1a4a7a);
        transform: translateY(-1px);
        box-shadow: 0 4px 14px rgba(26,74,122,0.4);
    }

    /* Input fields */
    .stNumberInput input, .stTextInput input, .stSelectbox select {
        border-radius: 8px !important;
        border: 1.5px solid var(--border) !important;
    }
    .stNumberInput input:focus, .stTextInput input:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(26,74,122,0.1) !important;
    }

    /* Hide default Streamlit branding */
    #MainMenu, footer { visibility: hidden; }
    header { visibility: hidden; }

    /* Page padding */
    .main .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 1200px; }
    </style>
    """, unsafe_allow_html=True)


def render_header(title, subtitle=""):
    """Render a styled page header."""
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1a4a7a, #2563a8); 
                padding: 28px 32px; border-radius: 16px; margin-bottom: 28px;
                box-shadow: 0 4px 20px rgba(26,74,122,0.25);">
        <h1 style="color:white; margin:0; font-family:'DM Serif Display',serif; font-size:1.9rem;">
            🏥 {title}
        </h1>
        {f'<p style="color:rgba(255,255,255,0.8); margin:8px 0 0; font-size:0.95rem;">{subtitle}</p>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)


def render_metric_card(label, value, icon="", color_class=""):
    """Render a styled metric card."""
    st.markdown(f"""
    <div class="metric-card {color_class}">
        <div style="font-size:0.85rem; color:#64748b; font-weight:500; margin-bottom:6px;">
            {icon} {label}
        </div>
        <div style="font-size:1.8rem; font-weight:700; color:#1e293b;">{value}</div>
    </div>
    """, unsafe_allow_html=True)


def render_risk_badge(risk_level):
    """Render a colored risk badge."""
    cls = f"risk-{risk_level.lower()}"
    icons = {'Low': '🟢', 'Medium': '🟡', 'High': '🔴'}
    icon = icons.get(risk_level, '')
    st.markdown(f"""
    <div style="text-align:center; padding: 20px 0;">
        <span class="risk-badge {cls}">{icon} {risk_level} Risk</span>
    </div>
    """, unsafe_allow_html=True)


def render_risk_gauge(risk_score, risk_level):
    """Render a Plotly gauge chart for risk score."""
    color = RISK_COLORS.get(risk_level, '#gray')
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=risk_score,
        number={'suffix': "%", 'font': {'size': 32, 'color': color}},
        title={'text': f"Risk Confidence", 'font': {'size': 14, 'color': '#64748b'}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#64748b"},
            'bar': {'color': color, 'thickness': 0.3},
            'bgcolor': "white",
            'borderwidth': 0,
            'steps': [
                {'range': [0, 33], 'color': '#d1fae5'},
                {'range': [33, 66], 'color': '#fef3c7'},
                {'range': [66, 100], 'color': '#fee2e2'}
            ],
            'threshold': {
                'line': {'color': color, 'width': 4},
                'thickness': 0.75,
                'value': risk_score
            }
        }
    ))
    fig.update_layout(
        height=220, margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='white', font={'family': 'DM Sans'}
    )
    return fig


def render_probability_bars(probabilities):
    """Render a horizontal bar chart of risk probabilities."""
    labels = list(probabilities.keys())
    values = list(probabilities.values())
    colors = [RISK_COLORS[l] for l in labels]

    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation='h',
        marker_color=colors,
        text=[f"{v:.1f}%" for v in values],
        textposition='outside'
    ))
    fig.update_layout(
        title="Probability Distribution",
        xaxis_title="Probability (%)",
        xaxis=dict(range=[0, 110]),
        height=200,
        margin=dict(l=10, r=40, t=40, b=20),
        paper_bgcolor='white',
        plot_bgcolor='white',
        font={'family': 'DM Sans'}
    )
    return fig


def render_assessment_history_chart(assessments):
    """Render a line chart of risk level trends over time."""
    if not assessments:
        return None

    df = pd.DataFrame(assessments)
    df['assessed_at'] = pd.to_datetime(df['assessed_at'])
    df = df.sort_values('assessed_at')

    risk_map = {'Low': 1, 'Medium': 2, 'High': 3}
    df['risk_num'] = df['risk_level'].map(risk_map)

    fig = go.Figure()
    colors_map = {'Low': '#2ecc71', 'Medium': '#f39c12', 'High': '#e74c3c'}

    for risk, color in colors_map.items():
        mask = df['risk_level'] == risk
        if mask.any():
            fig.add_trace(go.Scatter(
                x=df[mask]['assessed_at'],
                y=df[mask]['risk_num'],
                mode='markers',
                name=risk,
                marker=dict(color=color, size=12, symbol='circle'),
            ))

    fig.add_trace(go.Scatter(
        x=df['assessed_at'], y=df['risk_num'],
        mode='lines', line=dict(color='#94a3b8', width=1.5, dash='dot'),
        showlegend=False
    ))

    fig.update_layout(
        title="Risk Level Trend Over Time",
        yaxis=dict(tickvals=[1, 2, 3], ticktext=['Low', 'Medium', 'High'], range=[0.5, 3.5]),
        xaxis_title="Date",
        height=280,
        margin=dict(l=10, r=10, t=40, b=20),
        paper_bgcolor='white', plot_bgcolor='#f8fafc',
        font={'family': 'DM Sans'},
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    return fig


def render_risk_distribution_pie(assessments):
    """Render a pie chart of risk distribution."""
    if not assessments:
        return None

    df = pd.DataFrame(assessments)
    counts = df['risk_level'].value_counts().reset_index()
    counts.columns = ['risk_level', 'count']

    fig = px.pie(
        counts, values='count', names='risk_level',
        color='risk_level',
        color_discrete_map=RISK_COLORS,
        title='Risk Distribution',
        hole=0.4
    )
    fig.update_layout(
        height=280, margin=dict(l=10, r=10, t=40, b=20),
        paper_bgcolor='white', font={'family': 'DM Sans'},
        legend=dict(orientation='h', yanchor='bottom', y=-0.2)
    )
    return fig


def render_vitals_chart(assessments):
    """Render a multi-line chart of vitals over time."""
    if len(assessments) < 2:
        return None

    df = pd.DataFrame(assessments)
    df['assessed_at'] = pd.to_datetime(df['assessed_at'])
    df = df.sort_values('assessed_at')

    fig = go.Figure()
    vitals_to_plot = [
        ('heart_rate', 'Heart Rate (bpm)', '#e74c3c'),
        ('respiratory_rate', 'Resp. Rate', '#3498db'),
        ('oxygen_saturation', 'SpO2 (%)', '#2ecc71'),
        ('systolic_bp', 'Systolic BP', '#9b59b6'),
    ]

    for col, label, color in vitals_to_plot:
        if col in df.columns:
            fig.add_trace(go.Scatter(
                x=df['assessed_at'], y=df[col],
                mode='lines+markers', name=label,
                line=dict(color=color, width=2),
                marker=dict(size=6)
            ))

    fig.update_layout(
        title="Vitals Over Time",
        xaxis_title="Date", yaxis_title="Value",
        height=300, margin=dict(l=10, r=10, t=40, b=20),
        paper_bgcolor='white', plot_bgcolor='#f8fafc',
        font={'family': 'DM Sans'},
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    return fig


def highlight_abnormal_vitals(abnormal_vitals):
    """Display abnormal vitals as highlighted warning boxes."""
    if not abnormal_vitals:
        st.markdown("""
        <div style="background:#d1fae5;border-radius:8px;padding:12px 16px;color:#065f46;font-weight:500;">
            ✅ All vitals are within normal range
        </div>""", unsafe_allow_html=True)
        return

    st.markdown("**⚠️ Abnormal Vitals Detected:**")
    for key, info in abnormal_vitals.items():
        label = VITAL_RANGES.get(key, {}).get('label', key)
        unit = VITAL_RANGES.get(key, {}).get('unit', '')
        direction = "↑ HIGH" if info['status'] == 'high' else "↓ LOW"
        st.markdown(f"""
        <div class="vital-abnormal">
            ⚠️ <strong>{label}</strong>: {info['value']} {unit} — 
            <span style="font-weight:700;">{direction}</span> 
            (Normal: {info['normal']} {unit})
        </div>
        """, unsafe_allow_html=True)


def simulated_email_alert(patient_name, risk_level, doctor_name=""):
    """Simulate sending an email alert for high risk patients."""
    if risk_level == 'High':
        st.markdown(f"""
        <div style="background:#fff7ed;border:1px solid #fed7aa;border-radius:12px;
                    padding:16px;margin:12px 0;">
            <strong>📧 Alert Notification Sent (Simulated)</strong><br>
            <span style="color:#92400e; font-size:0.9rem;">
            To: Emergency Medical Team {f'& Dr. {doctor_name}' if doctor_name else ''}<br>
            Subject: ⚠️ HIGH RISK PATIENT ALERT — {patient_name}<br>
            Patient {patient_name} has been classified as HIGH RISK. Immediate attention required.
            </span>
        </div>
        """, unsafe_allow_html=True)


def format_datetime(dt_str):
    """Format a datetime string for display."""
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%b %d, %Y at %I:%M %p")
    except Exception:
        return dt_str
