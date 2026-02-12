from flask import Flask, render_template, request, redirect, url_for, flash, session
from controller.database import db
from controller.config import Config
from controller.model import User, Role, UserRole
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config.from_object(Config)

# Ensure secret key exists (for flash & session)
if not app.config.get("SECRET_KEY"):
    app.config["SECRET_KEY"] = "supersecretkey"

db.init_app(app)


# ---------------- DATABASE SETUP ----------------
with app.app_context():
    db.create_all()

    # Create roles safely (no duplicate ID issue)
    role_names = ["admin", "staff", "student"]

    for name in role_names:
        if not Role.query.filter_by(name=name).first():
            db.session.add(Role(name=name))
    db.session.commit()

    # Create default admin safely
    admin_email = "admin@gmail.com"
    existing_admin = User.query.filter_by(email=admin_email).first()

    if not existing_admin:
        admin_user = User(
            user_name="admin",
            email=admin_email,
            password=generate_password_hash("admin123"),
            phone="1234567890",
            city="AdminCity",
            flag=True
        )
        db.session.add(admin_user)
        db.session.commit()

        admin_role = Role.query.filter_by(name="admin").first()
        db.session.add(UserRole(user_id=admin_user.user_id, role_id=admin_role.role_id))
        db.session.commit()


# ---------------- HOME ----------------
@app.route('/')
def home():
    return redirect(url_for('login'))


# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password_raw = request.form.get('password')
        phone = request.form.get('phone')
        city = request.form.get('city')

        if not username or not email or not password_raw:
            flash("Please fill all required fields")
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash("Email already registered")
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password_raw)

        new_user = User(
            user_name=username,
            email=email,
            password=hashed_password,
            phone=phone,
            city=city
        )
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful. Please login.")
        return redirect(url_for('login'))

    return render_template('register.html')


# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user'] = user.user_name
            return redirect(url_for('welcome'))
        else:
            flash("Invalid email or password")

    return render_template('login.html')


# ---------------- WELCOME ----------------
@app.route('/welcome')
def welcome():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('welcome.html', username=session['user'])


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(debug=True)
