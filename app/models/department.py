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

    def to_dict(self):
        return {
            "department_id": self.department_id,
            "name": self.name,
            "faculty": self.faculty,
            "research_areas": self.research_areas,
            "courses": [c.to_dict() for c in self.courses],
            "programs": [p.name for p in self.programs]
        }

    def __repr__(self):
        return f"<Department {self.department_id} - {self.name}>"
