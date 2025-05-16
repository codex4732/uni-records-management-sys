from flask_restx import Namespace, Resource, fields
from datetime import datetime, date, timedelta
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from app.models import Student, Lecturer, Course, Department, Program, NonAcademicStaff, ResearchProject
from app.models.association_tables import enrollments, course_lecturers, project_team_members
from app.utils.validation import validate_id
from app.utils.database import db

# Initialize Namespace
ns = Namespace('api', description='University Record Management System Operations', path='/api')

# Response Models
student_model = ns.model('Student', {
    'student_id': fields.Integer,
    'name': fields.String,
    'email': fields.String,
    'year': fields.Integer,
    'program': fields.String,
    'advisor': fields.String,
    'courses_enrolled': fields.List(fields.String)
})

lecturer_model = ns.model('Lecturer', {
    'lecturer_id': fields.Integer,
    'name': fields.String,
    'email': fields.String,
    'department': fields.String,
    'research_areas': fields.List(fields.String)
})

course_model = ns.model('Course', {
    'course_id': fields.Integer,
    'code': fields.String,
    'name': fields.String,
    'credits': fields.Integer,
    'department_id': fields.Integer
})

advisor_model = ns.model('Advisor', {
    'name': fields.String,
    'email': fields.String,
    'department': fields.String
})

supervisor_model = ns.model('Supervisor', {
    'lecturer': fields.Nested(lecturer_model),
    'projects_count': fields.Integer
})

# Query 1: Students in course by lecturer
@ns.route('/students/enrolled/<course_code>/<lecturer_id>')
@ns.param('course_code', 'Course code (e.g. CS101)')
@ns.param('lecturer_id', 'Lecturer ID number')
class StudentsInCourse(Resource):
    @ns.marshal_list_with(student_model)
    def get(self, course_code, lecturer_id):
        """List students in a specific course taught by a lecturer"""
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
            return [s.to_dict() for s in students]
        except SQLAlchemyError as e:
            db.session.rollback()
            ns.abort(500, "Database error occurred")
        except Exception as e:
            ns.abort(500, str(e))

# Query 2: Final year students with >70% average
@ns.route('/students/final-year/high-achievers')
class FinalYearHighAchievers(Resource):
    @ns.marshal_list_with(student_model)
    def get(self):
        """List final year students with average grade above 70%"""
        try:
            students = Student.query.filter(
                Student.year_of_study == 4,
                Student.current_grades > 70
            ).all()
            return [s.to_dict() for s in students]
        except SQLAlchemyError as e:
            db.session.rollback()
            ns.abort(500, "Database error occurred")

# Query 3: Students without current semester courses
@ns.route('/students/unregistered')
class UnregisteredStudents(Resource):
    @ns.marshal_list_with(student_model)
    def get(self):
        """List students not registered in current semester"""
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
            return [s.to_dict() for s in students]
        except SQLAlchemyError as e:
            db.session.rollback()
            ns.abort(500, "Database error occurred")

# Query 4: Faculty advisor contact for student
@ns.route('/students/<student_id>/advisor')
@ns.param('student_id', 'Student ID number')
class StudentAdvisor(Resource):
    @ns.marshal_with(advisor_model)
    @ns.response(404, 'Advisor not found')
    def get(self, student_id):
        """Get faculty advisor details for a student"""
        validate_id(student_id)
        try:
            student = Student.query.get(student_id)
            if not student or not student.advisor:
                ns.abort(404, "Advisor not found")
                
            return {
                "name": student.advisor.name,
                "email": student.advisor.email,
                "department": student.advisor.department.name
            }
        except SQLAlchemyError as e:
            db.session.rollback()
            ns.abort(500, "Database error occurred")

# Query 5: Lecturers by research expertise
@ns.route('/lecturers/expertise/<research_area>')
@ns.param('research_area', 'Research area to search for')
class LecturersByExpertise(Resource):
    @ns.marshal_list_with(lecturer_model)
    def get(self, research_area):
        """Find lecturers by research expertise"""
        try:
            lecturers = Lecturer.query.filter(
                Lecturer.research_interests.ilike(f"%{research_area}%")
            ).all()
            return [l.to_dict() for l in lecturers]
        except SQLAlchemyError as e:
            db.session.rollback()
            ns.abort(500, "Database error occurred")

# Query 6: Courses by department
@ns.route('/courses/department/<department_id>')
@ns.param('department_id', 'Department ID number')
class DepartmentCourses(Resource):
    @ns.marshal_list_with(course_model)
    def get(self, department_id):
        """List courses offered by a department"""
        validate_id(department_id)
        try:
            courses = Course.query.join(
                Course.lecturers
            ).filter(
                Lecturer.department_id == department_id
            ).distinct().all()
            return [c.to_dict() for c in courses]
        except SQLAlchemyError as e:
            db.session.rollback()
            ns.abort(500, "Database error occurred")

# Query 7: Lecturers with most supervised projects
@ns.route('/lecturers/top-supervisors')
class TopSupervisors(Resource):
    @ns.marshal_list_with(supervisor_model)
    def get(self):
        """List lecturers with most supervised research projects"""
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
            
            return [{
                "lecturer": l[0].to_dict(),
                "projects_count": l[1]
            } for l in lecturers]
        except SQLAlchemyError as e:
            db.session.rollback()
            ns.abort(500, "Database error occurred")

# Query 8: Students advised by lecturer
@ns.route('/lecturer/<lecturer_id>/advisees')
@ns.param('lecturer_id', 'Lecturer ID number')
class LecturerAdvisees(Resource):
    @ns.marshal_list_with(student_model)
    def get(self, lecturer_id):
        """List students advised by a lecturer"""
        validate_id(lecturer_id)
        try:
            students = Student.query.filter(
                Student.advisor_id == lecturer_id
            ).all()
            return [s.to_dict() for s in students]
        except SQLAlchemyError as e:
            db.session.rollback()
            ns.abort(500, "Database error occurred")

# Query 9: Staff by department
@ns.route('/staff/department/<department_id>')
@ns.param('department_id', 'Department ID number')
class DepartmentStaff(Resource):
    @ns.marshal_list_with(ns.model('Staff', {
        'staff_id': fields.Integer,
        'name': fields.String,
        'position': fields.String,
        'department': fields.String
    }))
    def get(self, department_id):
        """List non-academic staff in a department"""
        validate_id(department_id)
        try:
            staff = NonAcademicStaff.query.filter(
                NonAcademicStaff.department_id == department_id
            ).all()
            return [s.to_dict() for s in staff]
        except SQLAlchemyError as e:
            db.session.rollback()
            ns.abort(500, "Database error occurred")
