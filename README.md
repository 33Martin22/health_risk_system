# 🏥 AI-Powered Health Risk Assessment System

A production-ready Streamlit web application for health risk classification with role-based access, patient dashboards, doctor portal, and PDF report generation.

---

## 📁 File Structure

```
health_risk_app/
├── app.py              # Main Streamlit application & page router
├── auth.py             # Authentication, password hashing, session management
├── database.py         # SQLite database setup and all DB operations
├── model.py            # ML model loading and risk prediction logic
├── utils.py            # UI helpers, charts, and visualizations
├── reports.py          # PDF report generation
├── seed_demo_data.py   # Script to create demo accounts
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

---

## ⚙️ Setup Instructions

### Step 1 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 2 — (Optional) Add your trained model
If you have the trained MLP model from your earlier work, copy these two files into the project folder:
```
health_risk_app/
├── risk_model.h5    ← your Keras model
├── scaler.pkl       ← your fitted MinMaxScaler
```
If these files are not present, the app will automatically use a **rule-based fallback** that still works correctly.

### Step 3 — Seed demo data (first time only)
```bash
python seed_demo_data.py
```
This creates demo accounts and sample data.

### Step 4 — Run the app
```bash
streamlit run app.py
```

### Step 5 — Open in browser
The app will open automatically at: **http://localhost:8501**

---

## 🔐 Demo Login Credentials

| Role    | Username  | Password  |
|---------|-----------|-----------|
| Patient | patient1  | pass123   |
| Doctor  | doctor1   | pass123   |
| Admin   | admin     | admin123  |

---

## 👤 Patient Features
- Enter vital signs and get instant AI risk classification
- View risk gauge and probability distribution
- See highlighted abnormal vitals
- Receive personalized recommendations
- Download PDF medical reports
- View dashboard with risk trends and charts
- Full assessment history

## 👨‍⚕️ Doctor Features
- View and manage assigned patients
- Search all patients
- Add treatment notes (including critical flags)
- View patient vitals history and charts
- Receive simulated alerts for high-risk patients

## 🔑 Admin Features
- System-wide analytics dashboard
- View all patients and assign doctors
- Full audit log of logins

---

## ☁️ Deploy to Streamlit Cloud (Free)

1. Push the `health_risk_app/` folder to a GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Set `app.py` as the main file
5. Click Deploy — dependencies install automatically
