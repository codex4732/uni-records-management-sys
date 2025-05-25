import sys

if 'sphinx' not in sys.modules:
    # Import all models for SQLAlchemy discovery
    from .student import Student
    from .lecturer import Lecturer
    from .course import Course
    from .enrollment import Enrollment
    from .course_offering import CourseOffering
    from .department import Department
    from .program import Program
    from .research_project import ResearchProject
    from .non_acad_staff import NonAcademicStaff
    from .association_tables import project_team_members
    from .base import BaseModel
