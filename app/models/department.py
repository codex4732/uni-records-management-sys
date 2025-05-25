from app.utils.database import db


class Department(db.Model):
    __tablename__ = 'departments'

    department_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    faculty = db.Column(db.String(150), nullable=False)
    research_areas = db.Column(db.String(250))

    # Relationships
    courses = db.relationship('Course', back_populates='department')
    programs = db.relationship('Program', back_populates='department')
    lecturers = db.relationship('Lecturer', back_populates='department')
    staff_members = db.relationship('NonAcademicStaff', back_populates='department')

    def to_dict(self, include_stats=True, detailed=False):
        result = {
            "department_id": self.department_id,
            "name": self.name,
            "faculty": self.faculty,
            "research_areas": self.research_areas,
        }

        if detailed:
            # Get full lecturer details
            lecturers = []
            for lecturer in self.lecturers:
                lecturers.append({
                    "lecturer_id": lecturer.lecturer_id,
                    "name": lecturer.name,
                    "email": lecturer.email,
                    "employment_type": lecturer.employment_type,
                    "areas_of_expertise": lecturer.areas_of_expertise.split(';') if lecturer.areas_of_expertise else [],
                    "course_load": lecturer.current_course_load,
                    "research_interests": lecturer.research_interests.split(';') if lecturer.research_interests else []
                })
            
            # Get full course details
            courses = []
            for course in self.courses:
                courses.append({
                    "course_id": course.course_id,
                    "code": course.code,
                    "name": course.name,
                    "level": course.level,
                    "credits": course.credits,
                    "description": course.description
                })
            
            # Get full program details
            programs = []
            for program in self.programs:
                programs.append({
                    "program_id": program.program_id,
                    "name": program.name,
                    "degree_awarded": program.degree_awarded,
                    "duration": program.duration,
                    "enrolled_students": len(program.students)
                })
            
            # Get non-academic staff details
            staff_members = []
            for staff in self.staff_members:
                staff_members.append({
                    "staff_id": staff.staff_id,
                    "name": staff.name,
                    "job_title": staff.job_title,
                    "employment_type": staff.employment_type
                })
            
            result.update({
                "lecturers": lecturers,
                "courses": courses,
                "programs": programs,
                "staff_members": staff_members,
                "lecturer_count": len(lecturers),
                "course_count": len(courses),
                "program_count": len(programs),
                "staff_count": len(staff_members)
            })
        
        elif include_stats:
            # Original stats logic for non-detailed view
            result.update({
                "lecturer_count": len(self.lecturers),
                "course_count": len(self.courses),
                "program_count": len(self.programs)
            })

        return result

    def __repr__(self):
        return f"<Department {self.department_id}: {self.name}>"
