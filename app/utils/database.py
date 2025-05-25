from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils import database_exists, create_database


db = SQLAlchemy()

def init_db(app):
    """Initialize database and tables programmatically"""
    with app.app_context():
        # Get database URI from config
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']

        # Create database if it doesn't exist
        try:
            if not database_exists(db_uri):
                create_database(db_uri)
                print(f"✅ Created database: {db_uri.split('/')[-1]}")
        except Exception as e:
            app.logger.error(f"Database initialization failed: {e}")
            raise

        # Create tables (ensure models are imported first)
        from app.models.student import Student
        from app.models.lecturer import Lecturer
        from app.models.course import Course
        from app.models.enrollment import Enrollment
        from app.models.course_offering import CourseOffering
        from app.models.department import Department
        from app.models.program import Program
        from app.models.research_project import ResearchProject
        from app.models.non_acad_staff import NonAcademicStaff
        from app.models.association_tables import project_team_members
        from app.models.base import BaseModel

        db.create_all()
        print("✅ Database tables READY")
