from app.utils.database import db

class NonAcademicStaff(db.Model):
    __tablename__ = 'non_academic_staff'

    staff_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    job_title = db.Column(db.String(100))
    employment_type = db.Column(db.String(100), nullable=False)

    # Relationships
    department_id = db.Column(db.Integer, db.ForeignKey('departments.department_id'))

    def to_dict(self):
        return {
            "staff_id": self.staff_id,
            "name": self.name,
            "position": f"{self.job_title} ({self.employment_type})",
            "department": self.department.name if self.department else None
        }

    def __repr__(self):
        return f"<NonAcademicStaff {self.staff_id} - {self.name}>"
