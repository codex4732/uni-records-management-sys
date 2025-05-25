from app.utils.database import db


class CourseOffering(db.Model):
    __tablename__ = 'course_offerings'
    
    offering_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'), nullable=False)
    lecturer_id = db.Column(db.Integer, db.ForeignKey('lecturers.lecturer_id'), nullable=False)
    semester = db.Column(db.String(10))  # Fall, Spring, Summer
    year = db.Column(db.Integer)         # 2024, 2025, etc.

    # Correct Relationships
    course = db.relationship('Course', back_populates='offerings')
    lecturer = db.relationship('Lecturer', back_populates='offerings')
    enrollments = db.relationship('Enrollment', back_populates='offering')

    def to_dict(self):
        return {
            "offering_id": self.offering_id,
            "course_id": self.course_id,
            "lecturer_id": self.lecturer_id,
            "semester": self.semester,
            "year": self.year
        }

    def __repr__(self):
        return f"<CourseOffering {self.offering_id} - Course: {self.course_id}, Lecturer: {self.lecturer_id}>"
