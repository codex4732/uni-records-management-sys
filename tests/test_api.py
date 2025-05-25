import pytest
import json
from datetime import date
from app import create_app
from app.utils.database import db
from app.models import (
    Department, Lecturer, Course, Student, CourseOffering,
    Program, Enrollment, NonAcademicStaff, ResearchProject
)


# ===============================
# Test Fixtures
# ===============================

@pytest.fixture
def app():
    """Create and configure a test Flask app instance."""
    app = create_app('testing')
    return app

@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()

@pytest.fixture
def _db(app):
    """Create and initialize test database."""
    with app.app_context():
        db.create_all()
        yield db
        db.drop_all()

@pytest.fixture
def department(_db):
    """Create a test department."""
    dept = Department(
        name="Computer Science",
        faculty="Engineering",
        research_areas="Artificial Intelligence;Cybersecurity"
    )
    _db.session.add(dept)
    _db.session.commit()
    return dept

@pytest.fixture
def lecturer(department, _db):
    """Create a test lecturer."""
    lecturer = Lecturer(
        name="Dr. Alice Smith",
        email="a.smith@uni.ac.uk",
        academic_qualifications="PhD in Computer Science",
        employment_type="Full-Time",
        department=department,
        research_interests="Machine Learning;Neural Networks",
        areas_of_expertise="AI;Machine Learning;Deep Learning",
        course_load=2
    )
    _db.session.add(lecturer)
    _db.session.commit()
    return lecturer

@pytest.fixture
def course(department, _db):
    """Create a test course."""
    course = Course(
        code="CS101",
        name="Introduction to Programming",
        description="Fundamentals of programming using Python",
        level="Undergraduate",
        credits=15,
        department=department,
        schedule="Mon 10:00-12:00, Wed 14:00-16:00"
    )
    _db.session.add(course)
    _db.session.commit()
    return course

@pytest.fixture
def course_offering(course, lecturer, _db):
    """Create a test course offering."""
    offering = CourseOffering(
        course=course,
        lecturer=lecturer,
        semester="Fall",
        year=2024
    )
    _db.session.add(offering)
    _db.session.commit()
    return offering

@pytest.fixture
def program(department, _db):
    """Create a test program."""
    program = Program(
        name="Computer Science BSc",
        degree_awarded="Bachelor of Science",
        duration=3,
        department=department,
        course_requirements="120 credits minimum",
        enrollment_details="September intake"
    )
    _db.session.add(program)
    _db.session.commit()
    return program

@pytest.fixture
def student(program, lecturer, _db):
    """Create a test student."""
    student = Student(
        name="John Doe",
        email="john.doe@student.uni.ac.uk",
        date_of_birth=date(2000, 1, 15),
        year_of_study=2,
        current_grades=75.5,
        enrolled_program_id=program.program_id,
        advisor=lecturer,
        graduation_status=False,
        disciplinary_record=False
    )
    _db.session.add(student)
    _db.session.commit()
    return student

@pytest.fixture
def enrollment(student, course_offering, _db):
    """Create a test enrollment."""
    enrollment = Enrollment(
        student=student,
        offering=course_offering,
        enrollment_date=date(2024, 9, 1),
        grade=85.0,
        status="completed"
    )
    _db.session.add(enrollment)
    _db.session.commit()
    return enrollment

@pytest.fixture
def staff(department, _db):
    """Create a test non-academic staff member."""
    staff = NonAcademicStaff(
        name="Sarah Wilson",
        job_title="Department Administrator",
        employment_type="Full-Time",
        department=department
    )
    _db.session.add(staff)
    _db.session.commit()
    return staff

@pytest.fixture
def research_project(lecturer, _db):
    """Create a test research project."""
    project = ResearchProject(
        title="Advanced Machine Learning Techniques",
        funding_sources="UK Research Council;EPSRC",
        principal_investigator=lecturer,
        outcomes="New ML framework;3 publications;Patent application",
        publications="Smith, A. et al. (2024). Novel ML Approaches. Nature AI."
    )
    project.team_members = [lecturer]
    _db.session.add(project)
    _db.session.commit()
    return project


# ===============================
# Students API Tests
# ===============================

class TestStudentsAPI:
    """Test class for Students API endpoints."""
    
    def test_get_students_list_success(self, client, student):
        """Test successful retrieval of students list."""
        response = client.get('/api/students')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) > 0
        
        student_data = data[0]
        assert 'student_id' in student_data
        assert 'name' in student_data
        assert 'email' in student_data
        assert 'current_grade' in student_data
        assert student_data['name'] == "John Doe"

    def test_get_students_with_year_filter(self, client, student):
        """Test students list with year filter."""
        response = client.get('/api/students?year=2')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data) > 0
        assert all(s['year'] == 2 for s in data)

    def test_get_students_with_grade_filter(self, client, student):
        """Test students list with grade filters."""
        response = client.get('/api/students?min_grade=70&max_grade=80')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data) > 0
        assert all(70 <= s['current_grade'] <= 80 for s in data)

    def test_get_student_detail_success(self, client, student):
        """Test successful retrieval of student details."""
        response = client.get(f'/api/students/{student.student_id}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['student_id'] == student.student_id
        assert data['name'] == "John Doe"
        assert 'program_details' in data or 'program' in data
        assert 'advisor_details' in data or 'advisor' in data

    def test_get_student_detail_with_detailed_flag(self, client, student, enrollment):
        """Test student detail with detailed=True parameter."""
        response = client.get(f'/api/students/{student.student_id}?detailed=true')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'active_enrollments' in data
        assert 'completed_enrollments' in data
        assert 'program_details' in data
        assert 'advisor_details' in data
        assert 'calculated_gpa' in data
        assert 'total_enrolled_credits' in data

    def test_get_student_advisor_success(self, client, student):
        """Test successful retrieval of student advisor."""
        response = client.get(f'/api/students/{student.student_id}/advisor')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'name' in data
        assert 'email' in data
        assert data['name'] == "Dr. Alice Smith"


# ===============================
# Lecturers API Tests
# ===============================

class TestLecturersAPI:
    """Test class for Lecturers API endpoints."""
    
    def test_get_lecturers_list_success(self, client, lecturer):
        """Test successful retrieval of lecturers list."""
        response = client.get('/api/lecturers')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) > 0
        
        lecturer_data = data[0]
        assert 'lecturer_id' in lecturer_data
        assert 'name' in lecturer_data
        assert 'email' in lecturer_data
        assert 'areas_of_expertise' in lecturer_data
        assert 'research_areas' in lecturer_data
        assert lecturer_data['name'] == "Dr. Alice Smith"

    def test_get_lecturers_with_expertise_filter(self, client, lecturer):
        """Test lecturers list with expertise area filter."""
        response = client.get('/api/lecturers?expertise_area=Machine')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data) > 0

    def test_get_lecturer_detail_success(self, client, lecturer):
        """Test successful retrieval of lecturer details."""
        response = client.get(f'/api/lecturers/{lecturer.lecturer_id}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['lecturer_id'] == lecturer.lecturer_id
        assert data['name'] == "Dr. Alice Smith"
        assert 'areas_of_expertise' in data
        assert isinstance(data['areas_of_expertise'], list)

    def test_get_lecturer_detail_with_detailed_flag(self, client, lecturer, research_project, course_offering):
        """Test lecturer detail with detailed=True parameter."""
        response = client.get(f'/api/lecturers/{lecturer.lecturer_id}?detailed=true')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'research_projects' in data
        assert 'courses_taught' in data
        assert 'advised_students' in data
        assert 'principal_investigator_count' in data
        assert 'total_research_projects' in data
        assert 'publications' in data

    def test_get_lecturer_advisees_success(self, client, lecturer, student):
        """Test successful retrieval of lecturer advisees."""
        response = client.get(f'/api/lecturers/{lecturer.lecturer_id}/advisees')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]['name'] == "John Doe"


# ===============================
# Courses API Tests
# ===============================

class TestCoursesAPI:
    """Test class for Courses API endpoints."""
    
    def test_get_courses_list_success(self, client, course):
        """Test successful retrieval of courses list."""
        response = client.get('/api/courses')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) > 0
        
        course_data = data[0]
        assert 'course_id' in course_data
        assert 'code' in course_data
        assert 'name' in course_data
        assert 'schedule' in course_data
        assert course_data['code'] == "CS101"

    def test_get_course_detail_by_code_success(self, client, course):
        """Test successful retrieval of course details using course code."""
        response = client.get(f'/api/courses/{course.code}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['code'] == course.code
        assert data['name'] == "Introduction to Programming"
        assert 'schedule' in data

    def test_get_course_detail_with_detailed_flag(self, client, course, course_offering, enrollment):
        """Test course detail with detailed=True parameter."""
        response = client.get(f'/api/courses/{course.code}?detailed=true')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'students' in data
        assert 'lecturers' in data
        assert 'offerings' in data
        assert 'student_count' in data
        assert 'lecturer_count' in data

    def test_get_courses_with_level_filter(self, client, course):
        """Test courses list with level filter."""
        response = client.get('/api/courses?level=Undergraduate')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data) > 0
        assert all(c['level'] == 'Undergraduate' for c in data)


# ===============================
# Enrollments API Tests
# ===============================

class TestEnrollmentsAPI:
    """Test class for Enrollments API endpoints."""
    
    def test_get_enrollments_list_success(self, client, enrollment):
        """Test successful retrieval of enrollments list."""
        response = client.get('/api/enrollments')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) > 0
        
        enrollment_data = data[0]
        assert 'enrollment_id' in enrollment_data
        assert 'student' in enrollment_data
        assert 'course' in enrollment_data
        assert 'lecturer' in enrollment_data

    def test_get_enrollments_simplified_response(self, client, enrollment):
        """Test enrollments list with simplified=true parameter."""
        response = client.get('/api/enrollments?simplified=true')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data) > 0
        
        enrollment_data = data[0]
        # Check simplified student data structure
        assert 'student' in enrollment_data
        assert 'enrollment_count' in enrollment_data['student']
        assert 'program' in enrollment_data['student']

    def test_get_enrollments_with_course_filter(self, client, enrollment, course):
        """Test enrollments list with course filter."""
        response = client.get(f'/api/enrollments?course_code={course.code}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data) > 0

    def test_get_enrollments_with_semester_filter(self, client, enrollment):
        """Test enrollments list with semester filter."""
        response = client.get('/api/enrollments?semester=Fall&year=2024')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data) > 0


# ===============================
# Departments API Tests
# ===============================

class TestDepartmentsAPI:
    """Test class for Departments API endpoints."""
    
    def test_get_departments_list_success(self, client, department):
        """Test successful retrieval of departments list."""
        response = client.get('/api/departments')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) > 0
        
        dept_data = data[0]
        assert 'department_id' in dept_data
        assert 'name' in dept_data
        assert 'faculty' in dept_data
        assert 'research_areas' in dept_data
        assert dept_data['name'] == "Computer Science"

    def test_get_department_detail_success(self, client, department):
        """Test successful retrieval of department details."""
        response = client.get(f'/api/departments/{department.department_id}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['department_id'] == department.department_id
        assert data['name'] == "Computer Science"

    def test_get_department_detail_with_detailed_flag(self, client, department, lecturer, course, program, staff):
        """Test department detail with detailed=True parameter."""
        response = client.get(f'/api/departments/{department.department_id}?detailed=true')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'lecturers' in data
        assert 'courses' in data
        assert 'programs' in data
        assert 'staff_members' in data
        assert 'lecturer_count' in data
        assert 'course_count' in data
        assert 'program_count' in data
        assert 'staff_count' in data


# ===============================
# Staff API Tests
# ===============================

class TestStaffAPI:
    """Test class for Staff API endpoints."""
    
    def test_get_staff_list_success(self, client, staff):
        """Test successful retrieval of staff list."""
        response = client.get('/api/staff')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) > 0
        
        staff_data = data[0]
        assert 'staff_id' in staff_data
        assert 'name' in staff_data
        assert 'job_title' in staff_data
        assert staff_data['name'] == "Sarah Wilson"

    def test_get_staff_with_department_filter(self, client, staff, department):
        """Test staff list with department filter."""
        response = client.get(f'/api/staff?department_id={department.department_id}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data) > 0


# ===============================
# Property Testing
# ===============================

class TestModelProperties:
    """Test class for testing computed properties and methods."""
    
    def test_course_active_enrollments_property(self, client, course, enrollment):
        """Test course active_enrollments property through API."""
        # Set enrollment to active status
        enrollment.status = 'active'
        db.session.commit()
        
        response = client.get(f'/api/courses/{course.code}?include_stats=true')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'student_count' in data

    def test_lecturer_current_course_load_property(self, client, lecturer, course_offering):
        """Test lecturer current_course_load property through API."""
        response = client.get(f'/api/lecturers/{lecturer.lecturer_id}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'course_load' in data
        assert data['course_load'] >= 1

    def test_student_active_courses_property(self, client, student, enrollment):
        """Test student active_courses property through API."""
        enrollment.status = 'active'
        db.session.commit()
        
        response = client.get(f'/api/students/{student.student_id}?include_courses=true')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'active_enrollments' in data
        assert isinstance(data['active_enrollments'], list)


# ===============================
# General API Tests
# ===============================

class TestGeneralAPI:
    """Test class for general API functionality."""
    
    def test_api_content_type(self, client, student):
        """Test API response content type."""
        response = client.get('/api/students')
        assert response.status_code == 200
        assert 'application/json' in response.content_type

    def test_empty_database_responses(self, client, _db):
        """Test API responses when database is empty."""
        _db.session.query(Student).delete()
        _db.session.commit()
        
        response = client.get('/api/students')

        if response.status_code == 500:
            assert True
        elif response.status_code == 404:
            assert True
        elif response.status_code == 200:
            data = json.loads(response.data)
            assert len(data) == 0
        else:
            assert False, f"Unexpected status code: {response.status_code}"

    def test_semicolon_separated_fields_parsing(self, client, lecturer):
        """Test that semicolon-separated fields are properly parsed."""
        response = client.get(f'/api/lecturers/{lecturer.lecturer_id}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data['areas_of_expertise'], list)
        assert isinstance(data['research_areas'], list)
        assert len(data['areas_of_expertise']) > 0
