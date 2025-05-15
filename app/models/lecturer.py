from app.utils.database import db

class Lecturer(db.Model):
    __tablename__ = 'lecturers'

    lecturer_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    academic_qualifications = db.Column(db.String(200), nullable=False)
    employment_type = db.Column(db.String(100), nullable=False)
    contract_details = db.Column(db.String(100))
    areas_of_expertise = db.Column(db.String(250))
    course_load = db.Column(db.Integer, nullable=False, default=0)
    research_interests = db.Column(db.String(250))
    publications = db.Column(db.Text)
    
    # Relationships
    department_id = db.Column(db.Integer, db.ForeignKey('departments.department_id'))
    courses = db.relationship('Course', secondary='course_lecturers', back_populates='lecturers')
    advisees = db.relationship('Student', back_populates='advisor')
    research_group = db.relationship('ResearchProject', back_populates='principal_investigator', uselist=False)
    projects = db.relationship('ResearchProject', secondary='project_team_members', back_populates='team_members')
    
    def __repr__(self):
        return f"<Lecturer {self.lecturer_id} - {self.name}>"
