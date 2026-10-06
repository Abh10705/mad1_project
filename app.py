from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from database import db
from models import User

app = Flask(__name__)
app.config.from_object(Config)

# Initialize SQLAlchemy with Flask app
db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    if current_user.is_authenticated:
        return f"Hello, {current_user.name}! Role: {current_user.role}. <a href='/logout'>Logout</a>"
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            if user.role == 'examiner' and user.status == 'pending':
                flash('Your examiner registration is pending Admin approval.', 'warning')
                return redirect(url_for('login'))
            elif user.status == 'deactivated':
                flash('Your account has been deactivated. Contact Admin.', 'danger')
                return redirect(url_for('login'))

            login_user(user)
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(url_for('home'))

        flash('Invalid username or password.', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')

        if role not in ['student', 'examiner']:
            flash('Invalid role selected.', 'danger')
            return redirect(url_for('register'))

        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash('Username or Email already registered.', 'danger')
            return redirect(url_for('register'))

        status = 'pending' if role == 'examiner' else 'approved'

        new_user = User(
            name=name,
            username=username,
            email=email,
            role=role,
            status=status
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        if role == 'examiner':
            flash('Registration submitted! Please wait for Admin approval before logging in.', 'info')
        else:
            flash('Registration successful! You can now log in.', 'success')

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)