from flask import Flask, request, render_template, redirect, jsonify, url_for, session
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
currentpatient = "none" 


# Configure Flask app with template and static folder paths
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management

# Database configuration
DB_CONFIG = {
    'host': '127.0.0.1', #change to 127.0.0.1
    'user': 'root',
    'password': 'm#P52s@ap$V', # change to
    'database': 'test' #change to 
}

# Function to get database connection
def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None
    
def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            logging.info("Database connection successful!")
    except Error as e:
        logging.error(f"Error: '{e}'")
    return connection

def with_db_connection(f):
    def decorated_function(*args, **kwargs):
        connection = create_connection()
        if connection:
            try:
                return f(connection, *args, **kwargs)
            finally:
                connection.close()
    decorated_function.__name__ = f.__name__  
    return decorated_function


@app.route('/')
def index():
    return render_template('home.html')

@app.route('/patientregister')
def patientregister():
    return render_template('patient.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/doctor_dashboard')
@with_db_connection
def doctor_dashboard(connection):
    logging.info("Accessing the doctor dashboard...")
    try:
        pending_appointments = AppointmentManager.get_pending_appointments(connection)
        approved_appointments = AppointmentManager.get_approved_appointments(connection)
        logging.info(f"Pending appointments: {pending_appointments}")
        logging.info(f"Approved appointments: {approved_appointments}")
        print("Entered Database and Fetched")
        return render_template('doctor.html', pending_appointments=pending_appointments,
                               approved_appointments=approved_appointments)
      
    except Exception as e:
        logging.error(f"Error in doctor_dashboard: {e}")
        return redirect(url_for('error_page'))


@app.route('/patientlogincheck', methods=['POST'])
def patientlogincheck():
    datanew = request.get_json()
    username = datanew.get("username")
    print(username)
    password = datanew.get("password")
    print(password)
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM rch_patients WHERE user = %s AND pass = %s", (username, password))
    patient = cursor.fetchone()
    conn.close()
    print(patient)
    if patient:
        print("success",patient['patient_id'])
        global currentpatient
        currentpatient = patient['patient_id']
        return jsonify({"status": "success"})
    elif not patient:
        print("fail")
        return jsonify({"status": "fail"})


@app.route("/adminloginpage")
def adminloginpage():
    return render_template("adminlogin.html")

@app.route('/adminlogincheck', methods=['POST'])
def adminlogincheck():
    datanew = request.get_json()
    username = datanew.get("username")
    print(username)
    password = datanew.get("password")
    print(password)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM admin WHERE user = %s AND pass = %s", (username, password))
    admin = cursor.fetchone()
    conn.close()
    print(admin)
    if admin:
        print("success")
        return jsonify({"status": "success"})
    elif not admin:
        print("fail")
        return jsonify({"status": "fail"})

@app.route("/doctorloginpage")
def doctorloginpage():
    return render_template("doctorlogin.html")

@app.route('/doctorlogincheck', methods=['POST'])
def doctorlogincheck():
    datanew = request.get_json()
    username = datanew.get("username")
    print(username)
    password = datanew.get("password")
    print(password)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM doctor WHERE user = %s AND pass = %s", (username, password))
    doctor = cursor.fetchone()
    conn.close()
    print(doctor)
    if doctor:
        print("success")
        return jsonify({"status": "success"})
    elif not doctor:
        print("fail")
        return jsonify({"status": "fail"})


@app.route('/adminhome')
def adminhome():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT patient_id, full_name, date_of_birth, contact_number, address, email, patient_status, registration_date FROM rch_patients")
    data = cursor.fetchall()
    conn.close()
    return render_template('admin.html', data=data)

@app.route('/update_patient', methods=['POST'])
def update_patient():
    data = request.json
    patient_id = data['patient_id']
    full_name = data['full_name']
    date_of_birth = data['date_of_birth']
    contact_number = data['contact_number']
    address = data['address']
    email = data['email']
    patient_status = data['patient_status']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE rch_patients 
        SET full_name=%s, date_of_birth=%s, contact_number=%s, address=%s, email=%s, patient_status=%s 
        WHERE patient_id=%s
        """,
        (full_name, date_of_birth, contact_number, address, email, patient_status, patient_id)
    )
    conn.commit()
    conn.close()
    
    return jsonify({"success": True})

@app.route("/patientlogin")
def patientlogin():
    return render_template("patientlogin.html")


# Route to handle form submission
@app.route('/submit_patient', methods=['POST'])
def submit_patient():
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = connection.cursor()
    
    try:
        # Retrieve form data
        form_data = {
            'full_name': request.form['full_name'].strip(),
            'user': request.form['user'].strip(),
            'pass': request.form['pass'],
            'date_of_birth': request.form['date_of_birth'],
            'contact_number': request.form['contact_number'].strip(),
            'address': request.form['address'].strip(),
            'email': request.form['email'].strip().lower(),
            'patient_status': request.form['patient_status']

        }

        # SQL Query to insert data
        sql = """
            INSERT INTO rch_patients 
            (full_name, user, pass, date_of_birth, contact_number, address, email, patient_status) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = tuple(form_data.values())
        print(values)
        print(values[1])
        cursor.execute(sql, values)
        connection.commit()
        
        patient_id = cursor.lastrowid
        session['patient_id'] = patient_id  # Store patient ID in session
        
        # Redirect to the dashboard after successful submission
        return redirect(url_for('patientlogin'))

    except Error as e:
        print(e)
        return jsonify({"error": "Database error occured"}), 500
    finally:
        cursor.close()
        connection.close()


# Route to render the patient dashboard
@app.route('/dashboard')
def dashboard():
    connection = get_db_connection()
    if not connection:
        return "Database connection failed", 500
    
    cursor = connection.cursor(dictionary=True)
    try:
        # Retrieve patient data
        global currentpatient
        cursor.execute("SELECT * FROM rch_patients WHERE patient_id = %s", (currentpatient,))
        patient_data = cursor.fetchone()

        # Retrieve appointment status
        cursor.execute("SELECT * FROM appointments WHERE patient_id = %s", (currentpatient,))
        appointment = cursor.fetchone()

        return render_template('dashboard.html', patient=patient_data, appointment=appointment, datetime=datetime)

    finally:
        cursor.close()
        connection.close()


# Route to handle appointment request
@app.route('/request_appointment', methods=['POST'])
def request_appointment():
    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = connection.cursor()
    try:
        # Insert appointment request with status "Pending"
        cursor.execute("INSERT INTO appointments (patient_id, appointment_status, requested_date) VALUES (%s, 'pending', NOW())", (currentpatient,))
        connection.commit()
        
        return jsonify({"message": "Appointment request submitted successfully"})
    except Error as e:
        return jsonify({"error": "Database error occurred"}), 500
    finally:
        cursor.close()
        connection.close()





class AppointmentManager:

    @staticmethod
    def get_pending_appointments(connection) -> list:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                a.appointment_id,
                p.patient_id,
                p.full_name,
                p.contact_number,
                p.email,
                a.appointment_status,
                DATE_FORMAT(a.requested_date, '%Y-%m-%d') as requested_date,
                TIME_FORMAT(a.appointment_time, '%H:%i') as appointment_time
            FROM appointments a
            JOIN rch_patients p ON a.patient_id = p.patient_id 
            WHERE a.appointment_status = 'pending'
            ORDER BY a.requested_date ASC, a.appointment_time ASC"""
        )
        appointments = cursor.fetchall()
        print(appointments)
        cursor.close()
        return appointments

    @staticmethod
    def get_approved_appointments(connection) -> list:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                a.appointment_id,
                p.full_name,
                p.contact_number,
                p.email,
                DATE_FORMAT(a.appointment_date, '%Y-%m-%d') as appointment_date,
                TIME_FORMAT(a.appointment_time, '%H:%i') as appointment_time
            FROM appointments a
            JOIN rch_patients p ON a.patient_id = p.patient_id
            WHERE a.appointment_status = 'approved'
            ORDER BY a.appointment_date DESC, a.appointment_time ASC"""
        )
        approved_appointments = cursor.fetchall()
        print(approved_appointments)
        cursor.close()
        return approved_appointments

    @app.route('/approve_appointment', methods=['POST'])
    @with_db_connection
    def approve_appointment(connection):
        appointment_id = request.form.get('appointment_id')
        appointment_time = request.form.get('appointment_time')
        appointment_date = request.form.get('appointment_date')
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE appointments 
            SET 
                appointment_status = 'approved',
                updated_at = NOW() ,
                appointment_time = %s,
                appointment_date = %s
            WHERE appointment_id = %s AND appointment_status = 'pending'"""
        , (appointment_time,appointment_date,appointment_id))
        connection.commit()
        cursor.close()
        return redirect(url_for('doctor_dashboard'))

    @app.route('/reject_appointment/<int:appointment_id>', methods=['POST'])
    @with_db_connection
    def reject_appointment(connection, appointment_id):
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE appointments 
            SET 
                appointment_status = 'rejected',
                updated_at = NOW()
            WHERE appointment_id = %s AND appointment_status = 'pending'
        """, (appointment_id,))
        connection.commit()
        cursor.close()
        return redirect(url_for('doctor_dashboard'))
    #logout
    @app.route('/logout')
    def logout():
        return redirect(url_for('home'))  # Redirect to login page after logout
    
    #vaccine
@app.route('/pregnancy_meds')
@with_db_connection
def pregnancy_meds(connection):
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM pregnancy_medicines")
        medicines = cursor.fetchall()
        cursor.close()
        return render_template('pregnancy_meds.html', medicines=medicines)
    except Error as e:
        logging.error(f"Error in pregnancy_meds: {e}")
        return redirect(url_for('error_page'))

@app.route('/update_med_stock', methods=['POST'])
@with_db_connection
def update_med_stock(connection):
    if request.method == 'POST':
        try:
            med_id = request.form['med_id']
            new_stock = request.form['stock']
            cursor = connection.cursor()
            cursor.execute("UPDATE pregnancy_medicines SET stock = %s WHERE id = %s", 
                         (new_stock, med_id))
            connection.commit()
            cursor.close()
            return jsonify({'success': True})
        except Error as e:
            logging.error(f"Error in update_med_stock: {e}")
            return jsonify({'success': False})
    return jsonify({'success': False})

# Add this to create the table if it doesn't exist
def create_pregnancy_medicines_table(connection):
    try:
        cursor = connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pregnancy_medicines (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                stock INT DEFAULT 0,
                description VARCHAR(500)
            )
        ''')
        
        # Check if table is empty and insert initial data
        cursor.execute("SELECT COUNT(*) FROM pregnancy_medicines")
        count = cursor.fetchone()[0]
        
        if count == 0:
            cursor.execute('''
                INSERT INTO pregnancy_medicines (name, stock, description) VALUES
                ('Acetaminophen', 100, 'Pain reliever and fever reducer'),
                ('Vitamin B6', 150, 'For morning sickness'),
                ('Iron Supplements', 200, 'For anemia prevention'),
                ('Calcium Carbonate', 120, 'Antacid for heartburn'),
                ('Prenatal Vitamins', 180, 'Essential vitamins and minerals'),
                ('Magnesium', 90, 'For leg cramps'),
                ('Vitamin D3', 160, 'Bone health supplement'),
                ('Folic Acid', 250, 'Neural tube defect prevention'),
                ('Docusate Sodium', 80, 'Stool softener'),
                ('Vitamin B12', 140, 'Energy and neural health')
            ''')
            connection.commit()
        cursor.close()
        logging.info("Pregnancy medicines table created/verified successfully")
    except Error as e:
        logging.error(f"Error creating pregnancy medicines table: {e}")

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

@app.route('/error_page')
def error_page():
    return "An error occurred. Please try again later.", 500

if __name__ == '__main__':
    app.run(debug=True)
