"""
seed_demo_data.py - Create demo accounts for testing
Run this once: python seed_demo_data.py
"""

from database import initialize_database, create_user, save_assessment, add_doctor_note, assign_patient_to_doctor
from auth import hash_password

def seed():
    initialize_database()

    users = [
        ("patient1", "pass123", "John Kamau", "john@demo.com", "patient"),
        ("patient2", "pass123", "Grace Wanjiku", "grace@demo.com", "patient"),
        ("doctor1",  "pass123", "Dr. Amina Osei", "amina@demo.com", "doctor"),
        ("admin",    "admin123", "System Admin", "admin@demo.com", "admin"),
    ]

    ids = {}
    for username, password, name, email, role in users:
        success, msg = create_user(username, hash_password(password), name, email, role)
        if success:
            from database import get_user_by_username
            u = get_user_by_username(username)
            ids[username] = u['id']
            print(f"✅ Created {role}: {username}")
        else:
            print(f"⚠️  {username}: {msg}")
            from database import get_user_by_username
            u = get_user_by_username(username)
            if u:
                ids[username] = u['id']

    # Sample assessments for patient1
    if 'patient1' in ids:
        samples = [
            ({'respiratory_rate':16,'oxygen_saturation':98,'o2_scale':1,'systolic_bp':120,'heart_rate':80,'temperature':37.0,'consciousness':'A','on_oxygen':0}, 'Low', 85.0),
            ({'respiratory_rate':22,'oxygen_saturation':93,'o2_scale':2,'systolic_bp':145,'heart_rate':105,'temperature':38.2,'consciousness':'V','on_oxygen':0}, 'Medium', 70.0),
            ({'respiratory_rate':28,'oxygen_saturation':88,'o2_scale':3,'systolic_bp':90,'heart_rate':130,'temperature':39.5,'consciousness':'P','on_oxygen':1}, 'High', 92.0),
        ]
        for vitals, risk, score in samples:
            save_assessment(ids['patient1'], vitals, risk, score, "Demo assessment")
        print("✅ Sample assessments created for patient1")

    # Assign patient to doctor
    if 'patient1' in ids and 'doctor1' in ids:
        assign_patient_to_doctor(ids['patient1'], ids['doctor1'])
        add_doctor_note(ids['doctor1'], ids['patient1'], "Patient showing improvement. Continue monitoring BP.", False)
        add_doctor_note(ids['doctor1'], ids['patient1'], "URGENT: SpO2 dropped below 90%. Immediate follow-up required.", True)
        print("✅ Doctor notes and assignment created")

    print("\n✅ Demo data seeded successfully!")
    print("\nLogin credentials:")
    print("  Patient : patient1 / pass123")
    print("  Doctor  : doctor1  / pass123")
    print("  Admin   : admin    / admin123")

if __name__ == "__main__":
    seed()
