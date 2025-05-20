from flask_restx import Namespace, Resource, fields
from datetime import datetime, date, timedelta
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from app.models import Student, Lecturer, Course, Department, Program, NonAcademicStaff, ResearchProject
from app.models.association_tables import enrollments, course_lecturers, project_team_members
from app.utils.validation import validate_id
from app.utils.database import db

# Initialize Namespace
ns = Namespace('api', 
    description='University Record Management System Operations', 
    path='/api',
    ordered=True  # Maintain endpoint order in Swagger UI
)

# ======================
# Response Models
# ======================
student_model = ns.model('Student', {
    'student_id': fields.Integer(description='Unique student identifier'),
    'name': fields.String(required=True, description='Full name'),
    'email': fields.String(description='University email address'),
    'year': fields.Integer(description='Current year of study (1-4)'),
    'program': fields.String(description='Enrolled academic program'),
    'advisor': fields.String(description='Assigned faculty advisor'),
    'courses_enrolled': fields.List(fields.String, description='List of course codes')
})

lecturer_model = ns.model('Lecturer', {
    'lecturer_id': fields.Integer(description='Unique staff identifier'),
    'name': fields.String(required=True, description='Full name'),
    'email': fields.String(description='University email address'),
    'department': fields.String(description='Affiliated department'),
    'research_areas': fields.List(fields.String, description='Research interests')
})

course_model = ns.model('Course', {
    'course_id': fields.Integer(description='Unique course identifier'),
    'code': fields.String(required=True, pattern=r'[A-Z]{2,4}\d{3}', example='CS101', 
                          description='Course code (e.g. CS101)'),
    'name': fields.String(required=True, description='Course title'),
    'credits': fields.Integer(min=1, max=30, description='Academic credits'),
    'department_id': fields.Integer(description='Offering department ID')
})

advisor_model = ns.model('Advisor', {
    'name': fields.String(description='Advisor name'),
    'email': fields.String(description='Contact email'),
    'department': fields.String(description='Department name')
})

supervisor_model = ns.model('Supervisor', {
    'lecturer': fields.Nested(lecturer_model),
    'projects_count': fields.Integer(min=0, description='Number of supervised projects')
})

staff_model = ns.model('Staff', {
    'staff_id': fields.Integer(description='Unique staff identifier'),
    'name': fields.String(required=True, description='Full name'),
    'position': fields.String(description='Job title and employment type'),
    'department': fields.String(description='Affiliated department')
})

# ======================
# API Endpoints
# ======================

# Query 1: Students in course by lecturer
@ns.route('/students/enrolled/<course_code>/<lecturer_id>')
@ns.doc(params={
    'course_code': {'description': 'Course code (e.g. CS101)', 'example': 'CS101'},
    'lecturer_id': {'description': 'Numeric lecturer identifier', 'example': '1'}
})
class StudentsInCourse(Resource):
    @ns.response(200, 'Success', [student_model])
    @ns.response(404, 'Course/Lecturer not found')
    @ns.response(500, 'Database error')
    def get(self, course_code, lecturer_id):
        """Retrieve students enrolled in a specific course taught by a lecturer"""
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
            
            if not students:
                ns.abort(404, "No students found for this course/lecturer combination")
                
            return [s.to_dict() for s in students]
        except SQLAlchemyError as e:
            db.session.rollback()
            ns.abort(500, "Database error occurred")
        except Exception as e:
            ns.abort(500, str(e))

# Query 2: Final year students with >70% average
@ns.route('/students/final-year/high-achievers')
class FinalYearHighAchievers(Resource):
    @ns.response(200, 'Success', [student_model])
    @ns.response(404, 'No students found')
    @ns.response(500, 'Database error')
    def get(self):
        """List final year students with average grade above 70%"""
        try:
            students = db.session.query(Student).filter(
                Student.year_of_study == 4,
                Student.current_grades > 70
            ).all()
            
            if not students:
                ns.abort(404, "No high-achieving final year students found")
                
            return [s.to_dict() for s in students]
        except SQLAlchemyError as e:
            db.session.rollback()
            ns.abort(500, "Database error occurred")

# Query 3: Students without current semester courses
@ns.route('/students/unregistered')
class UnregisteredStudents(Resource):
    @ns.response(200, 'Success', [student_model])
    @ns.response(404, 'All students registered')
    @ns.response(500, 'Database error')
    def get(self):
        """Identify students not enrolled in any courses for current semester"""
        try:
            now = datetime.now()
            current_year = now.year
            start_date = date(current_year, 1, 1)
            end_date = date(current_year, 6, 30) if now.month <= 6 else date(current_year, 12, 31)
            
            subquery = db.session.query(enrollments.c.student_id).filter(
                enrollments.c.enrollment_date.between(start_date, end_date)
            )
            
            students = db.session.query(Student).filter(
                ~Student.student_id.in_(subquery)
            ).all()
            
            if not students:
                ns.abort(404, "All students are registered for current semester")
                
            return [s.to_dict() for s in students]
        except SQLAlchemyError as e:
            db.session.rollback()
            ns.abort(500, "Database error occurred")

# Query 4: Faculty advisor contact for student
@ns.route('/students/<student_id>/advisor')
@ns.doc(params={'student_id': 'Numeric student identifier'})
class StudentAdvisor(Resource):
    @ns.marshal_with(advisor_model)
    @ns.response(200, 'Success')
    @ns.response(404, 'Student/Advisor not found')
    @ns.response(500, 'Database error')
    def get(self, student_id):
        """Retrieve contact information for a student's faculty advisor"""
        validate_id(student_id)
        try:
            student = db.session.get(Student, student_id)
            if not student or not student.advisor:
                ns.abort(404, "Advisor not found for this student")
                
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
@ns.doc(params={'research_area': 'Research area keyword'})
class LecturersByExpertise(Resource):
    @ns.response(200, 'Success', [lecturer_model])
    @ns.response(404, 'No lecturers found')
    @ns.response(500, 'Database error')
    def get(self, research_area):
        """Search for lecturers with expertise in a specific research area"""
        try:
            lecturers = db.session.query(Lecturer).filter(
                Lecturer.research_interests.ilike(f"%{research_area}%")
            ).all()
            
            if not lecturers:
                ns.abort(404, f"No lecturers found with expertise in '{research_area}'")
                
            return [l.to_dict() for l in lecturers]
        except SQLAlchemyError as e:
            db.session.rollback()
            ns.abort(500, "Database error occurred")

# Query 6: Courses by department
@ns.route('/courses/department/<department_id>')
@ns.doc(params={'department_id': 'Numeric department identifier'})
class DepartmentCourses(Resource):
    @ns.response(200, 'Success', [course_model])
    @ns.response(404, 'Department not found')
    @ns.response(500, 'Database error')
    def get(self, department_id):
        """List all courses offered by a specific department"""
        validate_id(department_id)
        try:
            courses = db.session.query(Course).join(
                Course.lecturers
            ).filter(
                Lecturer.department_id == department_id
            ).distinct().all()
            
            if not courses:
                ns.abort(404, "No courses found for this department")
                
            return [c.to_dict() for c in courses]
        except SQLAlchemyError as e:
            db.session.rollback()
            ns.abort(500, "Database error occurred")

# Query 7: Lecturers with most supervised projects
@ns.route('/lecturers/top-supervisors')
class TopSupervisors(Resource):
    @ns.response(200, 'Success', [supervisor_model])
    @ns.response(404, 'No research projects found')
    @ns.response(500, 'Database error')
    def get(self):
        """Identify lecturers who have supervised the most research projects"""
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
            
            if not lecturers:
                ns.abort(404, "No research projects found")
                
            return [{
                "lecturer": l[0].to_dict(),
                "projects_count": l[1]
            } for l in lecturers]
        except SQLAlchemyError as e:
            db.session.rollback()
            ns.abort(500, "Database error occurred")

# Query 8: Students advised by lecturer
@ns.route('/lecturer/<lecturer_id>/advisees')
@ns.doc(params={'lecturer_id': 'Numeric lecturer identifier'})
class LecturerAdvisees(Resource):
    @ns.response(200, 'Success', [student_model])
    @ns.response(404, 'No advisees found')
    @ns.response(500, 'Database error')
    def get(self, lecturer_id):
        """Retrieve list of students advised by a specific lecturer"""
        validate_id(lecturer_id)
        try:
            students = db.session.query(Student).filter(
                Student.advisor_id == lecturer_id
            ).all()
            
            if not students:
                ns.abort(404, "This lecturer has no advisees")
                
            return [s.to_dict() for s in students]
        except SQLAlchemyError as e:
            db.session.rollback()
            ns.abort(500, "Database error occurred")

# Query 9: Staff by department
@ns.route('/staff/department/<department_id>')
@ns.doc(params={'department_id': 'Numeric department identifier'})
class DepartmentStaff(Resource):
    @ns.response(200, 'Success', [staff_model])
    @ns.response(404, 'No staff found')
    @ns.response(500, 'Database error')
    def get(self, department_id):
        """Find all non-academic staff members in a specific department"""
        validate_id(department_id)
        try:
            staff = db.session.query(NonAcademicStaff).filter(
                NonAcademicStaff.department_id == department_id
            ).all()
            
            if not staff:
                ns.abort(404, "No staff found in this department")
                
            return [s.to_dict() for s in staff]
        except SQLAlchemyError as e:
            db.session.rollback()
            ns.abort(500, "Database error occurred")
