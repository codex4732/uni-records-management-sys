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
    department = db.relationship('Department', back_populates='courses')
    offerings = db.relationship('CourseOffering', back_populates='course')

    @property
    def enrollments(self):
        """Get all enrollments for this course through offerings"""
        if hasattr(self, '_precomputed_enrollments'):
            return self._precomputed_enrollments
        
        all_enrollments = []
        for offering in self.offerings:
            all_enrollments.extend(offering.enrollments)
        return all_enrollments

    @property
    def active_enrollments(self):
        """Get active enrollments for this course"""
        if hasattr(self, '_precomputed_active_enrollments'):
            return self._precomputed_active_enrollments
        
        return [enrollment for enrollment in self.enrollments 
                if enrollment.status == 'active']

    def to_dict(self, include_stats=True, detailed=False):
        result = {
            "course_id": self.course_id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "level": self.level,
            "credits": self.credits,
            "schedule": self.schedule,
            "department_id": self.department_id,
        }

        if detailed:
            # Get unique students enrolled in this course
            students = []
            seen_students = set()
            for offering in self.offerings:
                for enrollment in offering.enrollments:
                    if enrollment.student_id not in seen_students:
                        students.append({
                            "student_id": enrollment.student.student_id,
                            "name": enrollment.student.name,
                            "year": enrollment.student.year_of_study,
                            "status": enrollment.status
                        })
                        seen_students.add(enrollment.student_id)
            
            # Get unique lecturers teaching this course
            lecturers = []
            seen_lecturers = set()
            for offering in self.offerings:
                if offering.lecturer_id not in seen_lecturers:
                    lecturers.append({
                        "lecturer_id": offering.lecturer.lecturer_id,
                        "name": offering.lecturer.name,
                        "email": offering.lecturer.email,
                        "department": offering.lecturer.department.name if offering.lecturer.department else None
                    })
                    seen_lecturers.add(offering.lecturer_id)
            
            # Get semesters and years when course is offered
            offerings_info = []
            for offering in self.offerings:
                offerings_info.append({
                    "offering_id": offering.offering_id,
                    "semester": offering.semester,
                    "year": offering.year,
                    "lecturer": offering.lecturer.name
                })
            
            result.update({
                "students": students,
                "lecturers": lecturers,
                "offerings": offerings_info,
                "student_count": len(students),
                "lecturer_count": len(lecturers)
            })
        
        elif include_stats:
            if hasattr(self, '_precomputed_student_count'):
                result["student_count"] = self._precomputed_student_count
            else:
                # Fallback to property-based computation
                result["student_count"] = len(self.active_enrollments)

            if hasattr(self, '_precomputed_lecturer_count'):
                result["lecturer_count"] = self._precomputed_lecturer_count
            else:
                result["lecturer_count"] = len(set(o.lecturer_id for o in self.offerings))

        return result
    
    def __repr__(self):
        return f"<Course {self.code}: {self.name}>"
