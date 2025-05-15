import enum
from sqlalchemy import CheckConstraint, Enum
from app.utils.database import db

class GradeStatus(enum.Enum):
    PASS = "pass"
    FAIL = "fail"

class Student(db.Model):
    __tablename__ = 'students'

    student_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    year_of_study = db.Column(db.Integer,
                              CheckConstraint('year_of_study >= 1 AND year_of_study <= 10'),
                              nullable=False)
    current_grades = db.Column(Enum(GradeStatus), nullable=False)
    graduation_status = db.Column(db.Boolean, default=False)
    disciplinary_record = db.Column(db.Boolean, default=False)
    
    # Relationships
    enrolled_program_id = db.Column(db.Integer, db.ForeignKey('programs.program_id'))
    courses = db.relationship('Course', secondary='enrollments', back_populates='students')
    advisor_id = db.Column(db.Integer, db.ForeignKey('lecturers.lecturer_id'))
    advisor = db.relationship('Lecturer', back_populates='advisees')
    
    def __repr__(self):
        return f"<Student {self.student_id} - {self.name}>"
