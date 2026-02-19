"""
model.py - ML model loading and risk prediction
Handles loading the trained MLP model and making predictions
"""

import numpy as np
import pickle
import os
import streamlit as st


# ── NORMAL RANGES FOR VITAL SIGNS ────────────────────────────
VITAL_RANGES = {
    'respiratory_rate': {'min': 12, 'max': 20, 'unit': 'breaths/min', 'label': 'Respiratory Rate'},
    'oxygen_saturation': {'min': 95, 'max': 100, 'unit': '%', 'label': 'Oxygen Saturation'},
    'o2_scale': {'min': 0, 'max': 2, 'unit': '', 'label': 'O2 Scale'},
    'systolic_bp': {'min': 90, 'max': 140, 'unit': 'mmHg', 'label': 'Systolic BP'},
    'heart_rate': {'min': 60, 'max': 100, 'unit': 'bpm', 'label': 'Heart Rate'},
    'temperature': {'min': 36.1, 'max': 37.5, 'unit': '°C', 'label': 'Temperature'},
}

RISK_LABELS = {0: 'Low', 1: 'Medium', 2: 'High'}
RISK_COLORS = {'Low': '#2ecc71', 'Medium': '#f39c12', 'High': '#e74c3c'}

RECOMMENDATIONS = {
    'Low': [
        "✅ Your vitals are within normal range.",
        "🥗 Maintain a balanced diet and regular exercise.",
        "💧 Stay hydrated and get adequate sleep (7-9 hours).",
        "🏃 Engage in at least 30 minutes of physical activity daily.",
        "📅 Schedule routine check-ups every 6-12 months.",
        "🚭 Avoid smoking and limit alcohol consumption.",
    ],
    'Medium': [
        "⚠️ Some vitals are outside the normal range.",
        "👨‍⚕️ Consult a doctor within the next 24-48 hours.",
        "📊 Monitor your vitals daily and track any changes.",
        "💊 Take prescribed medications as directed.",
        "🧘 Reduce stress through relaxation techniques.",
        "🍎 Follow a heart-healthy diet and reduce sodium intake.",
        "📞 Contact your healthcare provider if symptoms worsen.",
    ],
    'High': [
        "🚨 URGENT: Seek immediate medical attention!",
        "🏥 Go to the nearest emergency room or call emergency services.",
        "📱 Call emergency services (911 or local emergency number) immediately.",
        "🚫 Do NOT drive yourself to the hospital.",
        "👥 Have someone stay with you at all times.",
        "💊 Do not take any new medications without doctor approval.",
        "📋 Bring a list of your current medications to the hospital.",
    ]
}


@st.cache_resource
def load_model_and_scaler():
    """Load the trained model and scaler. Returns None if files not found."""
    model = None
    scaler = None

    # Try loading Keras model
    try:
        from tensorflow.keras.models import load_model
        if os.path.exists('risk_model.h5'):
            model = load_model('risk_model.h5')
    except Exception as e:
        pass

    # Try loading scaler
    try:
        if os.path.exists('scaler.pkl'):
            with open('scaler.pkl', 'rb') as f:
                scaler = pickle.load(f)
    except Exception as e:
        pass

    return model, scaler


def predict_risk(vitals: dict):
    """
    Predict risk level from vitals.
    Falls back to rule-based if model not available.
    Returns: (risk_label, risk_score, probabilities)
    """
    model, scaler = load_model_and_scaler()

    if model is not None and scaler is not None:
        return _model_predict(vitals, model, scaler)
    else:
        return _rule_based_predict(vitals)


def _model_predict(vitals, model, scaler):
    """Use the trained MLP model for prediction."""
    try:
        import numpy as np

        numerical_input = np.array([[
            vitals['respiratory_rate'],
            vitals['oxygen_saturation'],
            vitals['o2_scale'],
            vitals['systolic_bp'],
            vitals['heart_rate'],
            vitals['temperature']
        ]])

        numerical_scaled = scaler.transform(numerical_input)
        consciousness_encoded = 1 if vitals['consciousness'] != 'A' else 0
        final_input = np.concatenate([
            numerical_scaled,
            [[consciousness_encoded, vitals['on_oxygen']]]
        ], axis=1)

        probs = model.predict(final_input, verbose=0)[0]
        pred_class = int(np.argmax(probs))
        risk_label = RISK_LABELS[pred_class]
        risk_score = float(np.max(probs)) * 100

        return risk_label, risk_score, {
            'Low': float(probs[0]) * 100,
            'Medium': float(probs[1]) * 100,
            'High': float(probs[2]) * 100,
        }
    except Exception:
        return _rule_based_predict(vitals)


def _rule_based_predict(vitals):
    """
    Rule-based fallback prediction using clinical thresholds.
    Used when the ML model is not available.
    """
    score = 0

    rr = vitals['respiratory_rate']
    if rr < 12 or rr > 25: score += 3
    elif rr > 20: score += 1

    spo2 = vitals['oxygen_saturation']
    if spo2 < 90: score += 4
    elif spo2 < 94: score += 2

    sbp = vitals['systolic_bp']
    if sbp < 90 or sbp > 180: score += 3
    elif sbp > 160 or sbp < 100: score += 1

    hr = vitals['heart_rate']
    if hr < 40 or hr > 130: score += 3
    elif hr > 100 or hr < 60: score += 1

    temp = vitals['temperature']
    if temp < 35 or temp > 39.5: score += 3
    elif temp > 38 or temp < 36: score += 1

    consciousness = vitals['consciousness']
    if consciousness == 'U': score += 5
    elif consciousness == 'P': score += 3
    elif consciousness == 'V': score += 1

    if vitals['on_oxygen'] == 1: score += 1

    if score >= 8:
        risk_label = 'High'
        probs = {'Low': 5.0, 'Medium': 15.0, 'High': 80.0}
    elif score >= 4:
        risk_label = 'Medium'
        probs = {'Low': 20.0, 'Medium': 65.0, 'High': 15.0}
    else:
        risk_label = 'Low'
        probs = {'Low': 80.0, 'Medium': 15.0, 'High': 5.0}

    risk_score = probs[risk_label]
    return risk_label, risk_score, probs


def check_abnormal_vitals(vitals: dict) -> dict:
    """Check which vitals are outside normal range."""
    abnormal = {}
    checks = {
        'respiratory_rate': (vitals['respiratory_rate'], 12, 20),
        'oxygen_saturation': (vitals['oxygen_saturation'], 95, 100),
        'systolic_bp': (vitals['systolic_bp'], 90, 140),
        'heart_rate': (vitals['heart_rate'], 60, 100),
        'temperature': (vitals['temperature'], 36.1, 37.5),
    }
    for key, (value, low, high) in checks.items():
        if value < low:
            abnormal[key] = {'value': value, 'status': 'low', 'normal': f"{low}-{high}"}
        elif value > high:
            abnormal[key] = {'value': value, 'status': 'high', 'normal': f"{low}-{high}"}
    return abnormal
