from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime
from contextlib import contextmanager
import requests
import json

app = Flask(__name__)

# API Ninjas Configuration
API_NINJAS_KEY = '1ATeuVhr5HhLrfEIZTdceQ==f1btBbgfSAbSTZA1'
NINJA_API_BASE_URL = 'https://api.api-ninjas.com/v1'

# API Headers
NINJA_HEADERS = {
    'X-Api-Key': API_NINJAS_KEY
}

# Database setup
def init_db():
    with sqlite3.connect('medical_appointments.db') as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id TEXT PRIMARY KEY,
                department TEXT,
                doctor TEXT,
                date TEXT,
                time TEXT,
                patient_name TEXT,
                patient_email TEXT,
                patient_phone TEXT,
                status TEXT,
                symptoms TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

@contextmanager
def get_db():
    conn = sqlite3.connect('medical_appointments.db')
    try:
        yield conn
    finally:
        conn.close()

# Initialize database
init_db()

@app.route('/')
@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

# New route for symptom checking
@app.route('/api/check-symptoms', methods=['POST'])
def check_symptoms():
    try:
        data = request.json
        symptoms = data.get('symptoms', '')
        
        # Call API Ninjas endpoint
        response = requests.get(
            f'{NINJA_API_BASE_URL}/symptoms',
            headers=NINJA_HEADERS,
            params={'query': symptoms}
        )
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'data': response.json()
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to fetch symptoms data'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@app.route('/api/get-departments')
def get_departments():
    departments = [
        'Cardiology',
        'Orthopedics',
        'Pediatrics',
        'General Medicine',
        'Dermatology',
        'Neurology',
        'Gynecology',
        'Dentistry'
    ]
    return jsonify(departments)

@app.route('/api/get-doctors/<department>')
def get_doctors(department):
    doctors_db = {
        'Cardiology': ['Dr. Smith (Cardiologist)', 'Dr. Johnson (Heart Specialist)'],
        'Orthopedics': ['Dr. Williams (Bone Specialist)', 'Dr. Brown (Joint Specialist)'],
        'Pediatrics': ['Dr. Davis (Child Specialist)', 'Dr. Miller (Pediatrician)'],
        'General Medicine': ['Dr. Wilson (General Physician)', 'Dr. Moore (Family Doctor)'],
        'Dermatology': ['Dr. Taylor (Skin Specialist)', 'Dr. Anderson (Dermatologist)'],
        'Neurology': ['Dr. Thomas (Neurologist)', 'Dr. White (Brain Specialist)'],
        'Gynecology': ['Dr. Martinez (Gynecologist)', 'Dr. Garcia (Women\'s Health)'],
        'Dentistry': ['Dr. Clark (Dentist)', 'Dr. Lewis (Dental Surgeon)']
    }
    return jsonify(doctors_db.get(department, []))

@app.route('/api/get-time-slots', methods=['POST'])
def get_time_slots():
    data = request.json
    date = data.get('date')
    
    morning_slots = [f"{hour}:00 AM" for hour in range(9, 12)]
    afternoon_slots = [f"{hour}:00 PM" for hour in range(1, 6)]
    
    all_slots = morning_slots + afternoon_slots
    return jsonify(all_slots)

@app.route('/api/book-appointment', methods=['POST'])
def book_appointment():
    try:
        data = request.json
        appointment_id = f"APT{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # First, check symptoms using API Ninjas
        if 'symptoms' in data:
            response = requests.get(
                f'{NINJA_API_BASE_URL}/symptoms',
                headers=NINJA_HEADERS,
                params={'query': data['symptoms']}
            )
            symptoms_data = response.json() if response.status_code == 200 else None
        else:
            symptoms_data = None

        with get_db() as conn:
            conn.execute('''
                INSERT INTO appointments (
                    id, department, doctor, date, time,
                    patient_name, patient_email, patient_phone, 
                    status, symptoms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                appointment_id,
                data['department'],
                data['doctor'],
                data['date'],
                data['time'],
                data['name'],
                data['email'],
                data['phone'],
                'confirmed',
                json.dumps(symptoms_data) if symptoms_data else None
            ))
            conn.commit()
        
        return jsonify({
            'success': True,
            'appointment_id': appointment_id,
            'message': 'Appointment booked successfully!',
            'symptoms_analysis': symptoms_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error booking appointment: {str(e)}'
        })

if __name__ == '__main__':
    app.run(debug=True, port=5502)