"""
University Record Management System (URMS) API.

This module sets up the main Flask-RESTx API namespace and registers all endpoints
with their corresponding resource classes. It serves as the entry point for the
University Record Management System (URMS) API.
"""

from flask_restx import Namespace

from .api_models import create_models
from .api_resources import (
    StudentsList, StudentDetail, StudentAdvisor,
    LecturersList, LecturerDetail, LecturerAdvisees,
    CoursesList, CourseDetail,
    EnrollmentsList,
    DepartmentsList, DepartmentDetail,
    StaffList
)


# Initialize Namespace
ns = Namespace(
    'api',
    description='University Record Management System (URMS) Operations',
    path='/api',
    ordered=True
)

# Create and register all models
models = create_models(ns)


# =============
# API Endpoints Registration
# =============

# Students Endpoints
@ns.route('/students')
class StudentsListEndpoint(StudentsList):
    """Students list endpoint with filtering capabilities."""
    
    @ns.doc(params={
        'year': 'Filter by year of study (1-5)',
        'min_grade': 'Minimum grade filter (0-100)',
        'max_grade': 'Maximum grade filter (0-100)',
        'program_id': 'Filter by program ID',
        'department_id': 'Filter by department ID',
        'graduation_status': 'Filter by graduation status (true/false)',
        'unregistered': 'Show only unregistered students (true/false)',
        'limit': 'Maximum number of results',
        'offset': 'Number of results to skip'
    })
    @ns.response(200, 'Success', models['student_model'])
    @ns.response(400, 'Invalid parameters')
    @ns.response(404, 'No students found')
    @ns.response(500, 'Database error')
    @ns.marshal_with(models['student_model'])
    def get(self):
        """List students with optional filtering."""
        return super().get(ns, models)


@ns.route('/students/<int:student_id>')
@ns.doc(params={'student_id': 'Unique student identifier'})
class StudentDetailEndpoint(StudentDetail):
    """Individual student detail endpoint."""
    
    @ns.response(200, 'Success', models['student_detail_model'])
    @ns.response(404, 'Student not found')
    @ns.response(500, 'Database error')
    @ns.marshal_with(models['student_detail_model'])
    def get(self, student_id):
        """Get detailed information about a specific student."""
        return super().get(student_id, ns, models)


@ns.route('/students/<int:student_id>/advisor')
@ns.doc(params={'student_id': 'Unique student identifier'})
class StudentAdvisorEndpoint(StudentAdvisor):
    """Student advisor information endpoint."""
    
    @ns.response(200, 'Success', models['advisor_model'])
    @ns.response(404, 'Student or advisor not found')
    @ns.response(500, 'Database error')
    @ns.marshal_with(models['advisor_model'])
    def get(self, student_id):
        """Get advisor information for a specific student."""
        return super().get(student_id, ns, models)


# Lecturers Endpoints
@ns.route('/lecturers')
class LecturersListEndpoint(LecturersList):
    """Lecturers list endpoint with filtering capabilities."""
    
    @ns.doc(params={
        'department_id': 'Filter by department ID',
        'expertise_area': 'Filter by expertise area keyword',
        'research_area': 'Filter by research area keyword',
        'employment_type': 'Filter by employment type',
        'min_course_load': 'Minimum course load',
        'max_course_load': 'Maximum course load',
        'top_supervisors': 'Show top research supervisors (true/false)',
        'limit': 'Maximum number of results',
        'offset': 'Number of results to skip'
    })
    @ns.response(200, 'Success', models['lecturer_model'])
    @ns.response(400, 'Invalid parameters')
    @ns.response(404, 'No lecturers found')
    @ns.response(500, 'Database error')
    def get(self):
        """List lecturers with optional filtering."""
        return super().get(ns, models)


@ns.route('/lecturers/<int:lecturer_id>')
@ns.doc(params={'lecturer_id': 'Unique lecturer identifier'})
class LecturerDetailEndpoint(LecturerDetail):
    """Individual lecturer detail endpoint."""
    
    @ns.response(200, 'Success', models['lecturer_detail_model'])
    @ns.response(404, 'Lecturer not found')
    @ns.response(500, 'Database error')
    @ns.marshal_with(models['lecturer_detail_model'])
    def get(self, lecturer_id):
        """Get detailed information about a specific lecturer."""
        return super().get(lecturer_id, ns, models)


@ns.route('/lecturers/<int:lecturer_id>/advisees')
@ns.doc(params={'lecturer_id': 'Unique lecturer identifier'})
class LecturerAdviseesEndpoint(LecturerAdvisees):
    """Lecturer advisees endpoint."""
    
    @ns.response(200, 'Success', models['student_model'])
    @ns.response(404, 'Lecturer not found or no advisees')
    @ns.response(500, 'Database error')
    @ns.marshal_with(models['student_model'])
    def get(self, lecturer_id):
        """Get list of students advised by a specific lecturer."""
        return super().get(lecturer_id, ns, models)


# Courses Endpoints
@ns.route('/courses')
class CoursesListEndpoint(CoursesList):
    """Courses list endpoint with filtering capabilities."""
    
    @ns.doc(params={
        'department_id': 'Filter by department ID',
        'level': 'Filter by course level',
        'min_credits': 'Minimum credits',
        'max_credits': 'Maximum credits',
        'lecturer_id': 'Filter by lecturer ID',
        'student_id': 'Filter by student enrollment (status=active only)',
        'limit': 'Maximum number of results',
        'offset': 'Number of results to skip'
    })
    @ns.response(200, 'Success', models['course_model'])
    @ns.response(400, 'Invalid parameters')
    @ns.response(404, 'No courses found')
    @ns.response(500, 'Database error')
    def get(self):
        """List courses with optional filtering."""
        return super().get(ns, models)


@ns.route('/courses/<string:course_code>')
@ns.doc(params={'course_code': 'Course code (e.g. CS101)'})
class CourseDetailEndpoint(CourseDetail):
    """Individual course detail endpoint."""
    
    @ns.response(200, 'Success', models['course_detail_model'])
    @ns.response(404, 'Course not found')
    @ns.response(500, 'Database error')
    @ns.marshal_with(models['course_detail_model'])
    def get(self, course_code):
        """Get detailed information about a specific course."""
        return super().get(course_code, ns, models)


# Enrollments Endpoints
@ns.route('/enrollments')
class EnrollmentsListEndpoint(EnrollmentsList):
    """Enrollments list endpoint with filtering capabilities."""
    
    @ns.doc(params={
        'course_code': 'Filter by course code',
        'student_id': 'Filter by student ID',
        'lecturer_id': 'Filter by lecturer ID',
        'semester': 'Filter by semester',
        'year': 'Filter by year',
        'status': 'Filter by enrollment status',
        'from_date': 'Filter enrollments from date (YYYY-MM-DD)',
        'to_date': 'Filter enrollments to date (YYYY-MM-DD)',
        'has_grade': 'Filter by grade presence (true/false)',
        'limit': 'Maximum number of results',
        'offset': 'Number of results to skip'
    })
    @ns.response(200, 'Success', models['enrollment_simplified_model'])
    @ns.response(400, 'Invalid parameters')
    @ns.response(404, 'No enrollments found')
    @ns.response(500, 'Database error')
    @ns.marshal_list_with(models['enrollment_simplified_model'])
    def get(self):
        """List enrollments with optional filtering."""
        return super().get(ns, models)


# Departments Endpoints
@ns.route('/departments')
class DepartmentsListEndpoint(DepartmentsList):
    """Departments list endpoint."""
    
    @ns.response(200, 'Success', models['department_model'])
    @ns.response(404, 'No departments found')
    @ns.response(500, 'Database error')
    def get(self):
        """List all departments."""
        return super().get(ns, models)


@ns.route('/departments/<int:department_id>')
@ns.doc(params={'department_id': 'Unique department identifier'})
class DepartmentDetailEndpoint(DepartmentDetail):
    """Individual department detail endpoint."""
    
    @ns.response(200, 'Success', models['department_detail_model'])
    @ns.response(404, 'Department not found')
    @ns.response(500, 'Database error')
    @ns.marshal_with(models['department_detail_model'])
    def get(self, department_id):
        """Get detailed information about a specific department."""
        return super().get(department_id, ns, models)


# Staff Endpoints
@ns.route('/staff')
class StaffListEndpoint(StaffList):
    """Non-academic staff list endpoint with filtering capabilities."""
    
    @ns.doc(params={
        'department_id': 'Filter by department ID',
        'job_title': 'Filter by job title',
        'employment_type': 'Filter by employment type',
        'limit': 'Maximum number of results',
        'offset': 'Number of results to skip'
    })
    @ns.response(200, 'Success', models['staff_model'])
    @ns.response(400, 'Invalid parameters')
    @ns.response(404, 'No staff found')
    @ns.response(500, 'Database error')
    def get(self):
        """List non-academic staff with optional filtering."""
        return super().get(ns, models)
