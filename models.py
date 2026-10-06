from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'examiner', 'student'
    status = db.Column(db.String(20), nullable=False, default='approved')  # 'pending', 'approved', 'deactivated'

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        # Admin and Students are active by default but Examiners are active only if approved
        return self.status == 'approved'

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    # Relationships
    slots_created = db.relationship('Slot', backref='examiner', lazy=True)
    bookings = db.relationship('Booking', backref='student', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='active')  # 'active', 'inactive'

    # Relationship to examinations
    examinations = db.relationship('Examination', backref='course', lazy=True, cascade="all, delete-orphan")


class Examination(db.Model):
    __tablename__ = 'examinations'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    exam_type = db.Column(db.String(50), nullable=False)  # 'Viva', 'Practical', 'Project Demo', 'Assessment'
    duration = db.Column(db.Integer, nullable=False)  # in minutes
    max_marks = db.Column(db.Float, nullable=False)
    
    # Timelines
    slot_creation_start = db.Column(db.DateTime, nullable=False)
    slot_creation_end = db.Column(db.DateTime, nullable=False)
    booking_start = db.Column(db.DateTime, nullable=False)
    booking_end = db.Column(db.DateTime, nullable=False)
    
    status = db.Column(db.String(30), default='Draft')  # 'Draft', 'Slot Creation', 'Booking Open', 'Closed', 'Completed'

    # Relationships
    rubrics = db.relationship('Rubric', backref='examination', lazy=True, cascade="all, delete-orphan")
    slots = db.relationship('Slot', backref='examination', lazy=True, cascade="all, delete-orphan")


class Rubric(db.Model):
    __tablename__ = 'rubrics'

    id = db.Column(db.Integer, primary_key=True)
    examination_id = db.Column(db.Integer, db.ForeignKey('examinations.id'), nullable=False)
    criterion_name = db.Column(db.String(100), nullable=False)
    max_marks = db.Column(db.Float, nullable=False)
    weightage = db.Column(db.Float, default=1.0)
    description = db.Column(db.Text, nullable=True)


class Slot(db.Model):
    __tablename__ = 'slots'

    id = db.Column(db.Integer, primary_key=True)
    examination_id = db.Column(db.Integer, db.ForeignKey('examinations.id'), nullable=False)
    examiner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    max_capacity = db.Column(db.Integer, nullable=False)
    available_seats = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='Available')  # 'Available', 'Full', 'Cancelled', 'Completed'

    # Relationships
    bookings = db.relationship('Booking', backref='slot', lazy=True)


class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey('slots.id'), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Booked')  # 'Booked', 'Cancelled', 'Completed'

    # Relationship to evaluation
    evaluations = db.relationship('Evaluation', backref='booking', lazy=True)


class Evaluation(db.Model):
    __tablename__ = 'evaluations'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    rubric_id = db.Column(db.Integer, db.ForeignKey('rubrics.id'), nullable=False)
    marks_obtained = db.Column(db.Float, nullable=False)
    remarks = db.Column(db.Text, nullable=True)