from sqlalchemy import func
from app.utils.database import db


class Enrollment(db.Model):
    __tablename__ = 'enrollments'

    enrollment_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id'), nullable=False)
    offering_id = db.Column(db.Integer, db.ForeignKey('course_offerings.offering_id'), nullable=False)
    enrollment_date = db.Column(db.Date, server_default=func.now())
    grade = db.Column(db.Float)
    status = db.Column(db.String(20), default='active')  # active, completed, failed, withdrawn

    # Relationships
    student = db.relationship('Student', back_populates='enrollments')
    offering = db.relationship('CourseOffering', back_populates='enrollments')

    @property
    def lecturer_id(self):
        """Simulate direct lecturer_id"""
        return self.offering.lecturer_id if self.offering else None
    
    @property
    def lecturer(self):
        """Simulate direct lecturer relationship"""
        return self.offering.lecturer if self.offering else None
    
    @property
    def course_id(self):
        """Simulate direct course_id"""
        return self.offering.course_id if self.offering else None
    
    @property
    def course(self):
        """Simulate direct course relationship"""
        return self.offering.course if self.offering else None
    
    @property
    def semester(self):
        """Access semester through offering"""
        return self.offering.semester if self.offering else None
    
    @property
    def year(self):
        """Access year through offering"""
        return self.offering.year if self.offering else None

    def to_dict(self, simplified=False):
        if simplified:
            # Simplified student details
            student_data = {
                "student_id": self.student.student_id,
                "name": self.student.name,
                "year": self.student.year_of_study,
                "program": self.student.program.name if self.student.program else None,
                "advisor": self.student.advisor.name if self.student.advisor else None,
                "enrollment_count": len(self.student.enrollments)
            }
            
            # Full course details
            course_data = self.offering.course.to_dict(include_stats=True)
            
            # Simplified lecturer details
            lecturer_data = {
                "lecturer_id": self.offering.lecturer.lecturer_id,
                "name": self.offering.lecturer.name,
                "email": self.offering.lecturer.email,
                "department": self.offering.lecturer.department.name if self.offering.lecturer.department else None,
                "academic_qualifications": self.offering.lecturer.academic_qualifications
            }
            
            return {
                "enrollment_id": self.enrollment_id,
                "student": student_data,
                "course": course_data,
                "lecturer": lecturer_data,
                "enrollment_date": self.enrollment_date.strftime('%Y-%m-%d') if self.enrollment_date else None,
                "grade": self.grade,
                "status": self.status
            }
        else:
            # Full detailed implementation
            return {
                "enrollment_id": self.enrollment_id,
                "student": self.student.to_dict(),
                "course": self.offering.course.to_dict(),
                "lecturer": self.offering.lecturer.to_dict(),
                "enrollment_date": self.enrollment_date.strftime('%Y-%m-%d') if self.enrollment_date else None,
                "grade": self.grade,
                "status": self.status
            }

    def __repr__(self):
        return f"<Enrollment {self.enrollment_id}: Student {self.student_id} -> {self.course.code if self.course else 'N/A'}>"
