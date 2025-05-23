from app.utils.database import db


class Course(db.Model):
    __tablename__ = 'courses'

    course_id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(250), nullable=False)
    level = db.Column(db.String(20), nullable=False)
    credits = db.Column(db.Integer, nullable=False)
    schedule = db.Column(db.String(250))

    # Relationships
    department_id = db.Column(db.Integer, db.ForeignKey('departments.department_id'))
    students = db.relationship('Student', secondary='enrollments', back_populates='courses')
    lecturers = db.relationship('Lecturer', secondary='course_lecturers', back_populates='courses')

    def to_dict(self):
        return {
            "course_id": self.course_id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "level": self.level,
            "credits": self.credits,
            "schedule": self.schedule,
            "department_id": self.department_id,
            "student_count": len(self.students),
            "lecturer_count": len(self.lecturers)
        }

    def __repr__(self):
        return f"<Course {self.code} - {self.name}>"
