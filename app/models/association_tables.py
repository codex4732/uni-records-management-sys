# Association tables
from sqlalchemy import func
from app.utils.database import db

enrollments = db.Table('enrollments',
    db.Column('student_id', db.Integer, db.ForeignKey('students.student_id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('courses.course_id'), primary_key=True),
    db.Column('enrollment_date', db.Date, server_default=func.now()),
    db.Column('grade', db.Float)
)

course_lecturers = db.Table('course_lecturers',
    db.Column('course_id', db.Integer, db.ForeignKey('courses.course_id'), primary_key=True),
    db.Column('lecturer_id', db.Integer, db.ForeignKey('lecturers.lecturer_id'), primary_key=True)
)

project_team_members = db.Table('project_team_members',
    db.Column('lecturer_id', db.Integer, db.ForeignKey('lecturers.lecturer_id'), primary_key=True),
    db.Column('project_id', db.Integer, db.ForeignKey('research_projects.project_id'), primary_key=True)
)
