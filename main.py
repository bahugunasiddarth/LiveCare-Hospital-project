from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import UserMixin, login_user, logout_user, LoginManager, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from flask_mail import Mail, Message
import json

with open ('config.json','r') as c:
    params = json.load(c)["params"]

    

app = Flask(__name__)
app.secret_key = 'siddhi'
    
# Configure the remote MySQL connection
db_config = { 
    'user': 'if0_38135213',
    'password': '8fFGQSvBj6Nw',
    'host': 'sql107.infinityfree.com',
    'database': 'if0_38135213_new_hms',
    'port': 3306,
    'raise_on_warnings': True
}

def get_db_connection():
    conn = mysql.connector.connect(**db_config)
    return conn

# Set up login manager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

#SMTP MAIL SERVER SETTINGS
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='',
    MAIL_USER_SSL=True,
    MAIL_USERNAME=params['gmail-user'],
    MAIL_PASSWORD=params['gmail-password']
)
mail=Mail(app)

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user:
        return User(id=user['id'], username=user['username'], email=user['email'], password=user['password'])
    return None

# Database models
class User(UserMixin):
    def __init__(self, id, username, email, password):
        self.id = id
        self.username = username
        self.email = email
        self.password = password

class Patients(UserMixin):
    def __init__(self, pid, email, name, appointment_date,appointment_time,gender,doctor,slot,phone_number, additional_notes ):
        self.pid = pid
        self.email = email
        self.name = name
        self.appointment_date = appointment_date
        self.appointment_time = appointment_time
        self.gender = gender
        self.doctor = doctor
        self.slot = slot
        self.phone_number = phone_number
        self.additional_notes = additional_notes 
        
class Doctors(UserMixin):
    def __init__(self, did, email, name,dept ):
        self.did = did
        self.email = email
        self.name = name
        self.dept = dept
              



@app.route('/doctors' , methods=['GET', 'POST'])
def doctors():

    return render_template('doctor.html')


@app.route('/patients', methods=['GET', 'POST'])
@login_required
def patients():
    if request.method == "POST":
        email = request.form.get('email')
        name = request.form.get('name')
        appointment_date = request.form.get('appointment_date')
        appointment_time = request.form.get('appointment_time')
        gender = request.form.get('gender')
        doctor = request.form.get('doctor')
        slot = request.form.get('slot')
        phone_number = request.form.get('phone_number')
        additional_notes= request.form.get('additional_notes')
        

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO patients (email, name, appointment_date, appointment_time, gender, doctor, slot, phone_number, additional_notes) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                           (email, name, appointment_date, appointment_time, gender, doctor, slot, phone_number, additional_notes ))
            conn.commit()
        conn.close()

        #0subject="HOSPITAL MANAGEMENT SYSTEM"
        #mail.send_message(subject, sender=params['gmail-user'], recipients=[email],body=f"YOUR bOOKING IS CONFIRMED THANKS FOR CHOOSING US \nYour Entered Details are :\nName: {name}\nSlot: {slot}")


        flash("Patient data submitted successfully.", "success")
        return redirect(url_for('patients'))

    return render_template('patient.html')


@app.route('/bookings')
@login_required
def bookings():
    em=current_user.email
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM patients WHERE email = %s", (em,))
    query = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('booking.html', query=query)

    

@app.route('/edit/<string:pid>', methods=['POST', 'GET'])
@login_required
def edit(pid):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'GET':
        cursor.execute("SELECT * FROM patients WHERE pid = %s", (pid,))
        patient = cursor.fetchone()
        cursor.close()
        conn.close()

        if patient:
            return render_template('edit.html', patient=patient)
        flash("Patient not found.", "danger")
        return redirect(url_for('bookings'))

    if request.method == 'POST':
        form_data = (
            request.form.get('email'),
            request.form.get('name'),
            request.form.get('appointment_date'),
            request.form.get('appointment_time'),
            request.form.get('gender'),
            request.form.get('doctor'),
            request.form.get('slot'),
            request.form.get('phone_number'),
            request.form.get('additional_notes'),
            pid
        )

        cursor.execute("""
            UPDATE patients
            SET email = %s, name = %s, appointment_date = %s, appointment_time = %s, gender = %s,
                doctor = %s, slot = %s, phone_number = %s, additional_notes = %s
            WHERE pid = %s
        """, form_data)
        conn.commit()
        cursor.close()
        conn.close()

        flash("Patient information updated successfully.", "success")
        return redirect(url_for('bookings'))


@app.route('/hospital')
def hospital():
    return render_template('hospital.html')


@app.route('/delete/<string:pid>', methods=['GET', 'POST'])
@login_required
def delete(pid):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM patients WHERE pid = %s", (pid,))
    conn.commit()
    cursor.close()
    conn.close()

    flash("Slot Deleted Successfully", "danger")
    return redirect(url_for('bookings'))


# Routes
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == "POST":
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user:
            flash("Email Already Exists", "warning")
            cursor.close()
            conn.close()
            return render_template('signup.html')

        encpassword = generate_password_hash(password)
        cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (username, email, encpassword))
        conn.commit()

        cursor.close()
        conn.close()

        flash("Signup Success Please Login", "success")
        return render_template('login.html')

    return render_template('signup.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            login_user(User(id=user['id'], username=user['username'], email=user['email'], password=user['password']))
            flash("Login Success", "success")
            cursor.close()
            conn.close()
            return redirect(url_for('index'))
        else:
            flash("Invalid Credentials", "danger")
            cursor.close()
            conn.close()
            return render_template('login.html')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))


@app.route('/search', methods=['POST', 'GET'])
@login_required
def search():

    return render_template('index.html')


@app.route('/test')
def test():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        return f'Connected. Found {len(users)} users.'
    except Exception as e:
        return f'Not Connected: {str(e)}'


if __name__ == '__main__':
    app.run()
