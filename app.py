from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from database import db
from models import User, Course, Examination, Booking

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    # Updated to SQLAlchemy 2.0 style to avoid legacy warnings
    return db.session.get(User, int(user_id))

@app.route('/')
def home():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif current_user.role == 'examiner':
        return f"Welcome Examiner {current_user.name}! (Dashboard coming next)"
    elif current_user.role == 'student':
        return f"Welcome Student {current_user.name}! (Dashboard coming next)"

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

# --- ADMIN ROUTES ---

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('home'))

    total_courses = Course.query.count()
    total_exams = Examination.query.count()
    total_examiners = User.query.filter_by(role='examiner', status='approved').count()
    total_students = User.query.filter_by(role='student').count()
    total_bookings = Booking.query.count()

    pending_examiners = User.query.filter_by(role='examiner', status='pending').all()

    return render_template(
        'admin_dashboard.html',
        total_courses=total_courses,
        total_exams=total_exams,
        total_examiners=total_examiners,
        total_students=total_students,
        total_bookings=total_bookings,
        pending_examiners=pending_examiners
    )

@app.route('/admin/courses')
@login_required
def manage_courses():
    if current_user.role != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('home'))
    return "Course Management Section (Coming in next step)"

@app.route('/admin/approve-examiner/<int:user_id>')
@login_required
def approve_examiner(user_id):
    if current_user.role != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('home'))

    examiner = db.session.get(User, user_id)
    if examiner and examiner.role == 'examiner':
        examiner.status = 'approved'
        db.session.commit()
        flash(f'Examiner {examiner.name} approved successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/deactivate-examiner/<int:user_id>')
@login_required
def deactivate_examiner(user_id):
    if current_user.role != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('home'))

    examiner = db.session.get(User, user_id)
    if examiner and examiner.role == 'examiner':
        examiner.status = 'deactivated'
        db.session.commit()
        flash(f'Examiner {examiner.name} account deactivated.', 'warning')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)