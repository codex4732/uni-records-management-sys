from app.utils.database import db


class Lecturer(db.Model):
    __tablename__ = 'lecturers'

    lecturer_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    academic_qualifications = db.Column(db.String(200), nullable=False)
    employment_type = db.Column(db.String(100), nullable=False)
    contract_details = db.Column(db.String(100))
    areas_of_expertise = db.Column(db.String(250))
    course_load = db.Column(db.Integer, nullable=False, default=0)
    research_interests = db.Column(db.String(250))
    publications = db.Column(db.Text)

    # Relationships
    department_id = db.Column(db.Integer, db.ForeignKey('departments.department_id'))
    department = db.relationship('Department', back_populates='lecturers')
    offerings = db.relationship('CourseOffering', back_populates='lecturer')
    advisees = db.relationship('Student', back_populates='advisor')
    research_projects = db.relationship('ResearchProject', back_populates='principal_investigator')
    research_group = db.relationship('ResearchProject', secondary='project_team_members', back_populates='team_members')

    @property
    def enrollments(self):
        """Get all enrollments for courses taught by this lecturer"""
        from app.models.enrollment import Enrollment
        return db.session.query(Enrollment).join(
            'offering'
        ).filter_by(lecturer_id=self.lecturer_id).all()
    
    @property
    def current_course_load(self):
        """Current number of course offerings"""
        return len(self.offerings)

    def to_dict(self, include_stats=True, detailed=False):
        result = {
            "lecturer_id": self.lecturer_id,
            "name": self.name,
            "email": self.email,
            "department": self.department.name if self.department else None,
            "employment_type": self.employment_type,
            "course_load": self.current_course_load,
            "areas_of_expertise": self.areas_of_expertise.split(';') if self.areas_of_expertise else [],
            "research_areas": self.research_interests.split(';') if self.research_interests else [],
            "academic_qualifications": self.academic_qualifications
        }

        if detailed:
            # Get research projects where lecturer is principal investigator
            principal_projects = []
            for project in self.research_projects:
                principal_projects.append({
                    "project_id": project.project_id,
                    "title": project.title,
                    "role": "Principal Investigator",
                    "funding_sources": project.funding_sources,
                    "principal_investigator": project.principal_investigator.name if project.principal_investigator else None,
                    "outcomes": project.outcome_list
                })
            
            # Get research projects where lecturer is a team member
            team_member_projects = []
            for project in self.research_group:
                # Avoid duplicates if they're both PI and team member
                if project.principal_investigator_id != self.lecturer_id:
                    team_member_projects.append({
                        "project_id": project.project_id,
                        "title": project.title,
                        "role": "Team Member",
                        "funding_sources": project.funding_sources,
                        "principal_investigator": project.principal_investigator.name if project.principal_investigator else None,
                        "outcomes": project.outcome_list
                    })
            
            # Combine all research projects
            all_projects = principal_projects + team_member_projects
            
            # Get course offerings taught by this lecturer
            courses_taught = []
            for offering in self.offerings:
                courses_taught.append({
                    "course_code": offering.course.code,
                    "course_name": offering.course.name,
                    "semester": offering.semester,
                    "year": offering.year,
                    "enrolled_students": len(offering.enrollments)
                })
            
            # Get students advised by this lecturer
            advised_students = []
            for student in self.advisees:
                advised_students.append({
                    "student_id": student.student_id,
                    "name": student.name,
                    "year": student.year_of_study,
                    "program": student.program.name if student.program else None
                })
            
            result.update({
                "contract_details": self.contract_details,
                "publications": self.publications.split(';') if self.publications else [],
                "research_projects": all_projects,
                "principal_investigator_count": len(principal_projects),
                "team_member_count": len(team_member_projects),
                "total_research_projects": len(all_projects),
                "courses_taught": courses_taught,
                "advised_students": advised_students,
                "advisee_count": len(advised_students)
            })
        
        if include_stats:
            if hasattr(self, '_precomputed_course_load'):
                result["course_load"] = self._precomputed_course_load
            else:
                result["course_load"] = self.current_course_load
        
        return result

    def update_course_load(self):
        """Update course_load based on number of course offerings"""
        self.course_load = len(self.offerings)

    def __repr__(self):
        return f"<Lecturer {self.lecturer_id}: {self.name}>"
