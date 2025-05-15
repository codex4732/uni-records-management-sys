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
    students = db.relationship('Student', backref='program')

    def __repr__(self):
        return f"<Program {self.program_id} - {self.name}>"
