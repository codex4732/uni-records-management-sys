import pytest
from datetime import date
from app import create_app
from app.utils.database import db
from app.models import (
    Department, Lecturer, Course, Student,
    Program, NonAcademicStaff, ResearchProject
)


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
        research_areas="Artificial Intelligence, Cybersecurity"
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
        research_interests="Machine Learning;Neural Networks"
    )
    _db.session.add(lecturer)
    _db.session.commit()
    return lecturer


@pytest.fixture
def course(department, lecturer, _db):
    """Create a test course."""
    course = Course(
        code="CS101",
        name="Introduction to Programming",
        description="Fundamentals of programming using Python",
        level="Undergraduate",
        credits=15,
        department=department,
        lecturers=[lecturer]
    )
    _db.session.add(course)
    _db.session.commit()
    return course


@pytest.fixture
def program(department, _db):
    """Create a test program."""
    program = Program(
        name="Computer Science BSc",
        degree_awarded="Bachelor of Science",
        duration=3,
        department=department
    )
    _db.session.add(program)
    _db.session.commit()
    return program


@pytest.fixture
def student(program, lecturer, course, _db):
    """Create a test student."""
    student = Student(
        name="John Doe",
        email="john.doe@student.uni.ac.uk",
        date_of_birth=date(2000, 1, 15),
        year_of_study=2,
        current_grades=75.5,
        program=program,
        advisor=lecturer,
        courses=[course]
    )
    _db.session.add(student)
    _db.session.commit()
    return student


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
        funding_sources="UK Research Council",
        principal_investigator=lecturer,
        team_members=[lecturer],
        outcomes="New ML framework;3 publications"
    )
    _db.session.add(project)
    _db.session.commit()
    return project


# Test Department Model
def test_department_creation(department):
    """Test department creation and basic attributes."""
    assert department.name == "Computer Science"
    assert department.faculty == "Engineering"
    assert "Artificial Intelligence" in department.research_areas


def test_department_relationships(department, lecturer, course, program, staff):
    """Test department relationships with other models."""
    assert lecturer in department.lecturers
    assert course in department.courses
    assert program in department.programs
    assert staff in department.staff_members


def test_department_to_dict(department):
    """Test department to_dict method."""
    dept_dict = department.to_dict()
    assert dept_dict['name'] == "Computer Science"
    assert dept_dict['faculty'] == "Engineering"
    assert isinstance(dept_dict['courses'], list)
    assert isinstance(dept_dict['programs'], list)


# Test Lecturer Model
def test_lecturer_creation(lecturer):
    """Test lecturer creation and basic attributes."""
    assert lecturer.name == "Dr. Alice Smith"
    assert lecturer.email == "a.smith@uni.ac.uk"
    assert lecturer.employment_type == "Full-Time"


def test_lecturer_relationships(lecturer, course, student, research_project):
    """Test lecturer relationships with other models."""
    assert course in lecturer.courses
    assert student in lecturer.advisees
    assert research_project in lecturer.research_projects


def test_lecturer_to_dict(lecturer):
    """Test lecturer to_dict method."""
    lecturer_dict = lecturer.to_dict()
    assert lecturer_dict['name'] == "Dr. Alice Smith"
    assert lecturer_dict['email'] == "a.smith@uni.ac.uk"
    assert isinstance(lecturer_dict['research_areas'], list)


def test_lecturer_course_load(lecturer, course, _db):
    """Test lecturer course load update method."""
    lecturer.update_course_load()
    assert lecturer.course_load == 1


# Test Course Model
def test_course_creation(course):
    """Test course creation and basic attributes."""
    assert course.code == "CS101"
    assert course.name == "Introduction to Programming"
    assert course.credits == 15


def test_course_relationships(course, lecturer, student):
    """Test course relationships with other models."""
    assert lecturer in course.lecturers
    assert student in course.students


def test_course_to_dict(course):
    """Test course to_dict method."""
    course_dict = course.to_dict()
    assert course_dict['code'] == "CS101"
    assert course_dict['name'] == "Introduction to Programming"
    assert isinstance(course_dict['student_count'], int)
    assert isinstance(course_dict['lecturer_count'], int)


# Test Program Model
def test_program_creation(program):
    """Test program creation and basic attributes."""
    assert program.name == "Computer Science BSc"
    assert program.degree_awarded == "Bachelor of Science"
    assert program.duration == 3


def test_program_relationships(program, student):
    """Test program relationships with other models."""
    assert student in program.students


def test_program_to_dict(program):
    """Test program to_dict method."""
    program_dict = program.to_dict()
    assert program_dict['name'] == "Computer Science BSc"
    assert program_dict['degree'] == "Bachelor of Science"
    assert isinstance(program_dict['enrolled_students'], int)


# Test Student Model
def test_student_creation(student):
    """Test student creation and basic attributes."""
    assert student.name == "John Doe"
    assert student.email == "john.doe@student.uni.ac.uk"
    assert student.year_of_study == 2


def test_student_relationships(student, program, lecturer, course):
    """Test student relationships with other models."""
    assert student.program == program
    assert student.advisor == lecturer
    assert course in student.courses


def test_student_to_dict(student):
    """Test student to_dict method."""
    student_dict = student.to_dict()
    assert student_dict['name'] == "John Doe"
    assert student_dict['email'] == "john.doe@student.uni.ac.uk"
    assert isinstance(student_dict['courses_enrolled'], list)


def test_student_grade_constraint(_db):
    """Test student year_of_study constraint."""
    with pytest.raises(Exception):  # SQLAlchemy will raise an exception for constraint violation
        invalid_student = Student(
            name="Invalid Student",
            email="invalid@student.uni.ac.uk",
            date_of_birth=date(2000, 1, 15),
            year_of_study=11,  # Invalid year (> 10)
            current_grades=75.5
        )
        _db.session.add(invalid_student)
        _db.session.commit()


# Test NonAcademicStaff Model
def test_staff_creation(staff):
    """Test non-academic staff creation and basic attributes."""
    assert staff.name == "Sarah Wilson"
    assert staff.job_title == "Department Administrator"
    assert staff.employment_type == "Full-Time"


def test_staff_relationships(staff, department):
    """Test non-academic staff relationships with other models."""
    assert staff.department == department


def test_staff_to_dict(staff):
    """Test non-academic staff to_dict method."""
    staff_dict = staff.to_dict()
    assert staff_dict['name'] == "Sarah Wilson"
    assert "Department Administrator" in staff_dict['position']
    assert staff_dict['department'] is not None


# Test ResearchProject Model
def test_research_project_creation(research_project):
    """Test research project creation and basic attributes."""
    assert research_project.title == "Advanced Machine Learning Techniques"
    assert research_project.funding_sources == "UK Research Council"
    assert "New ML framework" in research_project.outcomes


def test_research_project_relationships(research_project, lecturer):
    """Test research project relationships with other models."""
    assert research_project.principal_investigator == lecturer
    assert lecturer in research_project.team_members


def test_research_project_to_dict(research_project):
    """Test research project to_dict method."""
    project_dict = research_project.to_dict()
    assert project_dict['title'] == "Advanced Machine Learning Techniques"
    assert isinstance(project_dict['team_size'], int)
    assert isinstance(project_dict['outcomes'], list)


# Test Model Constraints and Validations
def test_unique_constraints(_db, department):
    """Test unique constraints on models."""
    # Test department name uniqueness
    with pytest.raises(Exception):
        duplicate_dept = Department(
            name="Computer Science",  # Duplicate name
            faculty="Science",
            research_areas="Data Science"
        )
        _db.session.add(duplicate_dept)
        _db.session.commit()


def test_email_uniqueness(_db, lecturer):
    """Test email uniqueness constraint."""
    with pytest.raises(Exception):
        duplicate_lecturer = Lecturer(
            name="Another Lecturer",
            email="a.smith@uni.ac.uk",  # Duplicate email
            academic_qualifications="PhD",
            employment_type="Part-Time"
        )
        _db.session.add(duplicate_lecturer)
        _db.session.commit()


def test_course_code_uniqueness(_db, course):
    """Test course code uniqueness constraint."""
    with pytest.raises(Exception):
        duplicate_course = Course(
            code="CS101",  # Duplicate code
            name="Another Programming Course",
            description="Another course",
            level="Undergraduate",
            credits=15
        )
        _db.session.add(duplicate_course)
        _db.session.commit()


# Test Cascade Deletions
def test_department_cascade_delete(_db, department, lecturer, course, program, staff):
    """Test that deleting a department cascades properly."""
    dept_id = department.department_id
    _db.session.delete(department)
    _db.session.commit()

    assert _db.session.get(Department, dept_id) is None
    # Verify related records are updated or deleted as per relationship configuration
    assert _db.session.get(Lecturer, lecturer.lecturer_id) is not None  # Should still exist but with null department_id
    assert _db.session.get(Course, course.course_id) is not None  # Should still exist but with null department_id
    assert _db.session.get(Program, program.program_id) is not None  # Should still exist but with null department_id
