from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils import database_exists, create_database

db = SQLAlchemy()

def init_db(app):
    """Initialize database and tables programmatically"""
    with app.app_context():
        # Get database URI from config
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        
        # Create database if it doesn't exist
        if not database_exists(db_uri):
            create_database(db_uri)
            print(f"✅ Created database: {db_uri.split('/')[-1]}")
        
        # Create tables (ensure models are imported first)
        from app.models.student import Student
        """from app.models.lecturer import Lecturer
        from app.models.non_acad_staff import Non_academic_staff
        from app.models.course import Course
        from app.models.department import Department
        from app.models.program import Program
        from app.models.research_project import Research_project
        from app.models.stud_course_enroll import Student_course_enrollment"""
        
        db.create_all()
        print("✅ Database tables created")
