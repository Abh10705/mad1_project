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
    elif current_user.role == 'student':
        return redirect(url_for('student_dashboard'))
    elif current_user.role == 'examiner':
        return redirect(url_for('examiner_dashboard'))

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

@app.route('/admin/courses', methods=['GET', 'POST'])
@login_required
def manage_courses():
    if current_user.role != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        code = request.form.get('code')
        name = request.form.get('name')
        description = request.form.get('description')

        existing = Course.query.filter_by(code=code).first()
        if existing:
            flash(f'Course code {code} already exists!', 'danger')
        else:
            new_course = Course(code=code, name=name, description=description)
            db.session.add(new_course)
            db.session.commit()
            flash(f'Course {code} - {name} created successfully!', 'success')
        return redirect(url_for('manage_courses'))

    courses = Course.query.all()
    return render_template('courses.html', courses=courses)

@app.route('/admin/courses/delete/<int:course_id>')
@login_required
def delete_course(course_id):
    if current_user.role != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('home'))

    course = db.session.get(Course, course_id)
    if course:
        db.session.delete(course)
        db.session.commit()
        flash('Course deleted successfully.', 'info')
    return redirect(url_for('manage_courses'))

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

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('home'))

    search_query = request.args.get('q', '')
    if search_query:
        examinations = Examination.query.join(Course).filter(
            (Examination.name.ilike(f'%{search_query}%')) | 
            (Course.name.ilike(f'%{search_query}%')) |
            (Course.code.ilike(f'%{search_query}%'))
        ).all()
    else:
        examinations = Examination.query.all()

    return render_template('student_dashboard.html', examinations=examinations, search_query=search_query)

from datetime import datetime

@app.route('/admin/examinations', methods=['GET', 'POST'])
@login_required
def manage_examinations():
    if current_user.role != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        course_id = request.form.get('course_id')
        name = request.form.get('name')
        exam_type = request.form.get('exam_type')
        duration = int(request.form.get('duration'))
        max_marks = float(request.form.get('max_marks'))

        # Parse datetime-local input fields
        slot_creation_start = datetime.strptime(request.form.get('slot_creation_start'), '%Y-%m-%dT%H:%M')
        slot_creation_end = datetime.strptime(request.form.get('slot_creation_end'), '%Y-%m-%dT%H:%M')
        booking_start = datetime.strptime(request.form.get('booking_start'), '%Y-%m-%dT%H:%M')
        booking_end = datetime.strptime(request.form.get('booking_end'), '%Y-%m-%dT%H:%M')

        new_exam = Examination(
            course_id=course_id,
            name=name,
            exam_type=exam_type,
            duration=duration,
            max_marks=max_marks,
            slot_creation_start=slot_creation_start,
            slot_creation_end=slot_creation_end,
            booking_start=booking_start,
            booking_end=booking_end,
            status='Slot Creation'
        )
        db.session.add(new_exam)
        db.session.commit()
        flash(f'Examination "{name}" created successfully!', 'success')
        return redirect(url_for('manage_examinations'))

    examinations = Examination.query.all()
    courses = Course.query.filter_by(status='active').all()
    return render_template('examinations.html', examinations=examinations, courses=courses)

@app.route('/admin/examinations/delete/<int:exam_id>')
@login_required
def delete_examination(exam_id):
    if current_user.role != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('home'))

    exam = db.session.get(Examination, exam_id)
    if exam:
        db.session.delete(exam)
        db.session.commit()
        flash('Examination deleted successfully.', 'info')
    return redirect(url_for('manage_examinations'))

from models import User, Course, Examination, Slot, Booking

@app.route('/examiner/dashboard', methods=['GET', 'POST'])
@login_required
def examiner_dashboard():
    if current_user.role != 'examiner':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        examination_id = request.form.get('examination_id')
        date_str = request.form.get('date')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        max_capacity = int(request.form.get('max_capacity'))

        exam = db.session.get(Examination, examination_id)
        if not exam:
            flash('Invalid examination selected.', 'danger')
        else:
            new_slot = Slot(
                examination_id=examination_id,
                examiner_id=current_user.id,
                date=date_str,
                start_time=start_time,
                end_time=end_time,
                max_capacity=max_capacity,
                available_seats=max_capacity,
                status='Available'
            )
            db.session.add(new_slot)
            db.session.commit()
            flash('Examination slot created successfully!', 'success')
        return redirect(url_for('examiner_dashboard'))

    slots = Slot.query.filter_by(examiner_id=current_user.id).all()
    examinations = Examination.query.all()
    return render_template('examiner_dashboard.html', slots=slots, examinations=examinations)

@app.route('/examiner/slot/delete/<int:slot_id>')
@login_required
def delete_slot(slot_id):
    if current_user.role != 'examiner':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('home'))

    slot = db.session.get(Slot, slot_id)
    if slot and slot.examiner_id == current_user.id:
        db.session.delete(slot)
        db.session.commit()
        flash('Slot removed successfully.', 'info')
    else:
        flash('Unauthorized action or slot not found.', 'danger')
    return redirect(url_for('examiner_dashboard'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)