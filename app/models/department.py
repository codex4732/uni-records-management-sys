from app.utils.database import db

class Department(db.Model):
    __tablename__ = 'departments'

    department_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    faculty = db.Column(db.String(150), nullable=False)
    research_areas = db.Column(db.String(250))

    # Relationships
    courses = db.relationship('Course', backref='department')
    programs = db.relationship('Program', backref='department')
    lecturers = db.relationship('Lecturer', backref='department')
    staff_members = db.relationship('NonAcademicStaff', backref='department')

    def __repr__(self):
        return f"<Department {self.department_id} - {self.name}>"
