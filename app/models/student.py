from sqlalchemy import CheckConstraint
from app.utils.database import db


class Student(db.Model):
    __tablename__ = 'students'

    student_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    year_of_study = db.Column(db.Integer,
                              CheckConstraint('year_of_study >= 1 AND year_of_study <= 5'),
                              nullable=False)
    current_grades = db.Column(db.Float, nullable=False)
    graduation_status = db.Column(db.Boolean, default=False)
    disciplinary_record = db.Column(db.Boolean, default=False)

    # Relationships
    enrolled_program_id = db.Column(db.Integer, db.ForeignKey('programs.program_id'))
    program = db.relationship('Program', back_populates='students')
    enrollments = db.relationship('Enrollment', back_populates='student')
    advisor_id = db.Column(db.Integer, db.ForeignKey('lecturers.lecturer_id'))
    advisor = db.relationship('Lecturer', back_populates='advisees')

    @property
    def active_courses(self):
        """Get list of active course codes for this student"""
        return [e.course.code for e in self.enrollments if e.status == 'active' and e.course]
    
    @property
    def active_enrollment_count(self):
        """Count of active enrollments"""
        return len([e for e in self.enrollments if e.status == 'active'])

    def to_dict(self, include_courses=True, include_enrollments=True, detailed=False):
        result = {
            "student_id": self.student_id,
            "name": self.name,
            "email": self.email,
            "year": self.year_of_study,
            "current_grade": self.current_grades,
            "program": self.program.name if self.program else None,
            "advisor": self.advisor.name if self.advisor else None,
            'graduation_status': self.graduation_status,
            'disciplinary_record': self.disciplinary_record
        }
        
        if include_courses and hasattr(self, '_courses_enrolled'):
            result['courses_enrolled'] = self._courses_enrolled
        elif include_courses:
            # Only execute if not preloaded
            result['courses_enrolled'] = [
                e.offering.course.code for e in self.enrollments 
                if e.status == 'active'
            ]
        
        if include_enrollments and hasattr(self, '_enrollment_count'):
            result['enrollment_count'] = self._enrollment_count
        elif include_enrollments:
            result['enrollment_count'] = len([e for e in self.enrollments if e.status == 'active'])
        
        # Add detailed info if requested
        if detailed:
            # Get detailed enrollment breakdown
            enrollment_details = []
            for enrollment in self.enrollments:
                enrollment_details.append({
                    "enrollment_id": enrollment.enrollment_id,
                    "course_code": enrollment.offering.course.code,
                    "course_name": enrollment.offering.course.name,
                    "course_credits": enrollment.offering.course.credits,
                    "course_level": enrollment.offering.course.level,
                    "semester": enrollment.offering.semester,
                    "year": enrollment.offering.year,
                    "lecturer": enrollment.offering.lecturer.name if enrollment.offering.lecturer else None,
                    "enrollment_date": enrollment.enrollment_date.strftime('%Y-%m-%d') if enrollment.enrollment_date else None,
                    "enrollment_grade": enrollment.grade,
                    "status": enrollment.status
                })
            
            # Group enrollments by status for summary
            active_enrollments = [e for e in enrollment_details if e["status"] == "active"]
            completed_enrollments = [e for e in enrollment_details if e["status"] == "completed"]
            failed_enrollments = [e for e in enrollment_details if e["status"] == "failed"]
            withdrawn_enrollments = [e for e in enrollment_details if e["status"] == "withdrawn"]
            
            # Calculate academic statistics
            completed_credits = sum(e["course_credits"] for e in completed_enrollments if e["enrollment_grade"] is not None)
            total_enrolled_credits = sum(e["course_credits"] for e in enrollment_details)
            
            # Get grades for GPA calculation
            graded_enrollments = [e for e in enrollment_details if e["enrollment_grade"] is not None]
            gpa = sum(e["enrollment_grade"] for e in graded_enrollments) / len(graded_enrollments) if graded_enrollments else None
            
            result.update({
                "total_enrolled_credits": total_enrolled_credits,
                "completed_credits": completed_credits,
                "calculated_gpa": round(gpa, 2) if gpa else None,
                "active_enrollment_count": len(active_enrollments),
                "active_enrollments": active_enrollments,
                "completed_enrollment_count": len(completed_enrollments),
                "completed_enrollments": completed_enrollments,
                "withdrawn_enrollment_count": len(withdrawn_enrollments),
                "withdrawn_enrollments": withdrawn_enrollments,
                "failed_enrollment_count": len(failed_enrollments),
                "failed_enrollments": failed_enrollments,             
                "program_details": {
                    "program_id": self.program.program_id if self.program else None,
                    "program_name": self.program.name if self.program else None,
                    "degree_awarded": self.program.degree_awarded if self.program else None,
                    "duration": self.program.duration if self.program else None,
                    "department": self.program.department.name if self.program and self.program.department else None
                },
                "advisor_details": {
                    "advisor_id": self.advisor.lecturer_id if self.advisor else None,
                    "advisor_name": self.advisor.name if self.advisor else None,
                    "advisor_email": self.advisor.email if self.advisor else None,
                    "advisor_department": self.advisor.department.name if self.advisor and self.advisor.department else None
                }
            })

        return result
    
    def __repr__(self):
        return f"<Student {self.student_id}: {self.name}>"
