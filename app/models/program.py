from app.utils.database import db


class Program(db.Model):
    __tablename__ = 'programs'

    program_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    degree_awarded = db.Column(db.String(100))
    duration = db.Column(db.Integer, nullable=False)  # in years
    course_requirements = db.Column(db.String(250))
    enrollment_details = db.Column(db.String(250))

    # Relationships
    department_id = db.Column(db.Integer, db.ForeignKey('departments.department_id'))
    department = db.relationship('Department', back_populates='programs')
    students = db.relationship('Student', back_populates='program')

    def to_dict(self):
        return {
            "program_id": self.program_id,
            "name": self.name,
            "degree": self.degree_awarded,
            "duration_years": self.duration,
            "department_id": self.department_id,
            "enrolled_students": len(self.students)
        }

    def __repr__(self):
        return f"<Program {self.program_id}: {self.name}>"
