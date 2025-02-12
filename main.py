from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import UserMixin, login_user, logout_user, LoginManager, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from bson.objectid import ObjectId
import json
from pymongo import MongoClient

# Load configuration from JSON file
with open('config.json', 'r') as c:
    params = json.load(c)["params"]

app = Flask(__name__)
app.secret_key = 'siddhi'

# Configure MongoDB connection
client = MongoClient("mongodb+srv://bahugunasiddhi:bahugunasiddhi@sid.fguws.mongodb.net/livecare")
db = client['hospital_management']

# Set up login manager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# SMTP MAIL SERVER SETTINGS
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail-user'],
    MAIL_PASSWORD=params['gmail-password']
)
mail = Mail(app)

# Flask-Login user loader
@login_manager.user_loader
def load_user(user_id):
    user = db.users.find_one({"_id": ObjectId(user_id)})
    if user:
        return User(id=str(user['_id']), username=user['username'], email=user['email'], password=user['password'])
    return None

# Database models
class User(UserMixin):
    def __init__(self, id, username, email, password):
        self.id = id
        self.username = username
        self.email = email
        self.password = password

# Routes
@app.route('/doctors', methods=['GET', 'POST'])
def doctors():
    return render_template('doctor.html')

@app.route('/patients', methods=['GET', 'POST'])
@login_required
def patients():
    if request.method == "POST":
        data = {
            "email": request.form.get('email'),
            "name": request.form.get('name'),
            "appointment_date": request.form.get('appointment_date'),
            "appointment_time": request.form.get('appointment_time'),
            "gender": request.form.get('gender'),
            "doctor": request.form.get('doctor'),
            "slot": request.form.get('slot'),
            "phone_number": request.form.get('phone_number'),
            "additional_notes": request.form.get('additional_notes')
        }
        db.patients.insert_one(data)
        flash("Patient data submitted successfully.", "success")
        return redirect(url_for('patients'))

    return render_template('patient.html')

@app.route('/bookings')
@login_required
def bookings():
    email = current_user.email
    query = list(db.patients.find({"email": email}))
    for item in query:
        item["_id"] = str(item["_id"])
    return render_template('booking.html', query=query)

@app.route('/edit/<string:pid>', methods=['GET', 'POST'])
@login_required
def edit(pid):
    try:
        if not ObjectId.is_valid(pid):
            flash("Invalid Patient ID", "danger")
            return redirect(url_for('bookings'))

        patient = db.patients.find_one({"_id": ObjectId(pid)})
        if not patient:
            flash("Patient not found.", "danger")
            return redirect(url_for('bookings'))

        if request.method == 'POST':
            data = {
                "email": request.form.get('email').strip(),
                "name": request.form.get('name').strip(),
                "appointment_date": request.form.get('appointment_date'),
                "appointment_time": request.form.get('appointment_time'),
                "gender": request.form.get('gender'),
                "doctor": request.form.get('doctor'),
                "slot": request.form.get('slot'),
                "phone_number": request.form.get('phone_number'),
                "additional_notes": request.form.get('additional_notes', '').strip()
            }

            db.patients.update_one({"_id": ObjectId(pid)}, {"$set": data})
            flash("Patient information updated successfully.", "success")
            return redirect(url_for('bookings'))

        patient["_id"] = str(patient["_id"])  # Convert ObjectId to string for template
        return render_template('edit.html', patient=patient)

    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for('bookings'))

    
@app.route('/hospital')
def hospital():
    return render_template('hospital.html')    

@app.route('/delete/<string:pid>', methods=['GET', 'POST'])
@login_required
def delete(pid):
    print(f"Attempting to delete patient with ID: {pid}")  

    try:
        result = db.patients.delete_one({"_id": ObjectId(pid)})
        if result.deleted_count:
            flash("Slot Deleted Successfully", "danger")
        else:
            flash("Patient not found.", "warning")
    except Exception as e:
        print(f"Error deleting patient: {e}")

    return redirect(url_for('bookings'))


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == "POST":
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        user = db.users.find_one({"email": email})

        if user:
            flash("Email Already Exists", "warning")
            return render_template('signup.html')

        encpassword = generate_password_hash(password)
        db.users.insert_one({"username": username, "email": email, "password": encpassword})
        flash("Signup Success Please Login", "success")
        return render_template('login.html')

    return render_template('signup.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        user = db.users.find_one({"email": email})

        if user and check_password_hash(user['password'], password):
            login_user(User(id=str(user['_id']), username=user['username'], email=user['email'], password=user['password']))
            flash("Login Success", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid Credentials", "danger")
            return render_template('login.html')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

@app.route('/test')
def test():
    try:
        users = list(db.users.find())
        return f'Connected. Found {len(users)} users.'
    except Exception as e:
        return f'Not Connected: {str(e)}'

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
