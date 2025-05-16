from datetime import datetime, date, timedelta
from flask import Blueprint, jsonify, request
from sqlalchemy import func, and_, or_, not_
from sqlalchemy.exc import SQLAlchemyError

from app.models import Student, Lecturer, Course, Department, Program, NonAcademicStaff, ResearchProject
from app.models.association_tables import enrollments, course_lecturers, project_team_members
from app.utils.validation import validate_id

from app.utils.database import db

api_bp = Blueprint('api', __name__)

# Response Standardization
def api_response(data=None, status=200, error=None):
    return jsonify({
        'status': status,
        'data': data,
        'error': error
    }), status


# Query 1: Students in course by lecturer

@api_bp.route('/students/enrolled/<course_code>/<lecturer_id>')
def students_in_course_by_lecturer(course_code, lecturer_id):
    validate_id(lecturer_id)
    try:
        students = db.session.query(Student).join(
            Student.courses
        ).join(
            Course.lecturers
        ).filter(
            Course.code == course_code,
            Lecturer.lecturer_id == lecturer_id
        ).all()
        
        return api_response([s.to_dict() for s in students])
    except SQLAlchemyError as e:
        db.session.rollback()
        return api_response(error="Database error", status=500)
    except Exception as e:
        return api_response(error=str(e), status=500)

# Query 2: Final year students with >70% average

@api_bp.route('/students/final-year/high-achievers')
def final_year_high_achievers():
    try:
        students = Student.query.filter(
            Student.year_of_study == 4,
            Student.current_grades > 70
        ).all()
        
        return api_response([s.to_dict() for s in students])
    except SQLAlchemyError as e:
        db.session.rollback()
        return api_response(error="Database error", status=500)
    except Exception as e:
        return api_response(error=str(e), status=500)

# Query 3: Students without current semester courses

@api_bp.route('/students/unregistered')
def unregistered_students():
    try:
        now = datetime.now()
        current_year = now.year
        start_date = date(current_year, 1, 1)
        end_date = date(current_year, 6, 30) if now.month <= 6 else date(current_year, 12, 31)
        subquery = db.session.query(enrollments.c.student_id).filter(
            enrollments.c.enrollment_date.between(start_date, end_date)
        )
        
        students = Student.query.filter(
            ~Student.student_id.in_(subquery)
        ).all()
        
        return api_response([s.to_dict() for s in students])
    except SQLAlchemyError as e:
        db.session.rollback()
        return api_response(error="Database error", status=500)
    except Exception as e:
        return api_response(error=str(e), status=500)

# Query 4: Faculty advisor contact for student

@api_bp.route('/students/<student_id>/advisor')
def get_advisor_contact(student_id):
    validate_id(student_id)
    try:
        student = Student.query.get(student_id)
        if not student or not student.advisor:
            return jsonify({"error": "Advisor not found"}), 404
            
        return api_response({
            "name": student.advisor.name,
            "email": student.advisor.email,
            "department": student.advisor.department.name
        })
    except SQLAlchemyError as e:
        db.session.rollback()
        return api_response(error="Database error", status=500)
    except Exception as e:
        return api_response(error=str(e), status=500)

# Query 5: Lecturers by research expertise

@api_bp.route('/lecturers/expertise/<research_area>')
def lecturers_by_expertise(research_area):
    try:
        lecturers = Lecturer.query.filter(
            Lecturer.research_interests.ilike(f"%{research_area}%")
        ).all()
        
        return api_response([l.to_dict() for l in lecturers])
    except SQLAlchemyError as e:
        db.session.rollback()
        return api_response(error="Database error", status=500)
    except Exception as e:
        return api_response(error=str(e), status=500)
    
# Query 6: Courses by department

@api_bp.route('/courses/department/<department_id>')
def courses_by_department(department_id):
    validate_id(department_id)
    try:
        courses = Course.query.join(
            Course.lecturers
        ).filter(
            Lecturer.department_id == department_id
        ).distinct().all()
        
        return api_response([c.to_dict() for c in courses])
    except SQLAlchemyError as e:
        db.session.rollback()
        return api_response(error="Database error", status=500)
    except Exception as e:
        return api_response(error=str(e), status=500)
    
# Query 7: Lecturers with most supervised projects

@api_bp.route('/lecturers/top-supervisors')
def top_project_supervisors():
    try:
        lecturers = db.session.query(
            Lecturer,
            func.count(ResearchProject.project_id).label('project_count')
        ).join(
            ResearchProject,
            Lecturer.lecturer_id == ResearchProject.principal_investigator_id
        ).group_by(Lecturer.lecturer_id).order_by(
            func.count(ResearchProject.project_id).desc()
        ).limit(10).all()
        
        return api_response([{
            "lecturer": l[0].to_dict(),
            "projects_count": l[1]
        } for l in lecturers])
    except SQLAlchemyError as e:
        db.session.rollback()
        return api_response(error="Database error", status=500)
    except Exception as e:
        return api_response(error=str(e), status=500)

# Query 8: Students advised by lecturer

@api_bp.route('/lecturer/<lecturer_id>/advisees')
def lecturer_advisees(lecturer_id):
    validate_id(lecturer_id)
    try:
        students = Student.query.filter(
            Student.advisor_id == lecturer_id
        ).all()
        
        return api_response([s.to_dict() for s in students])
    except SQLAlchemyError as e:
        db.session.rollback()
        return api_response(error="Database error", status=500)
    except Exception as e:
        return api_response(error=str(e), status=500)
    
# Query 9: Staff by department

@api_bp.route('/staff/department/<department_id>')
def staff_by_department(department_id):
    validate_id(department_id)
    try:
        staff = NonAcademicStaff.query.filter(
            NonAcademicStaff.department_id == department_id
        ).all()
        
        return api_response([s.to_dict() for s in staff])
    except SQLAlchemyError as e:
        db.session.rollback()
        return api_response(error="Database error", status=500)
    except Exception as e:
        return api_response(error=str(e), status=500)
