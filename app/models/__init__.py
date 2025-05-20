import sys

if 'sphinx' not in sys.modules:
    # Import all models for SQLAlchemy discovery
    from .student import Student
    from .lecturer import Lecturer
    from .course import Course
    from .department import Department
    from .program import Program
    from .research_project import ResearchProject
    from .non_acad_staff import NonAcademicStaff
    from .association_tables import enrollments, course_lecturers, project_team_members
    from .base import BaseModel
