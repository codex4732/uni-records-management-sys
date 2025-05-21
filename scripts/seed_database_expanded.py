"""University Records Management System Database Seeder.

This script populates a database with test data for the University Records Management System.
It creates sample data for departments, lecturers, courses, programs, students, staff,
and research projects with realistic relationships and constraints.

The script uses predefined mappings and external data files to generate consistent
and interconnected test data across all entities in the system.
"""

from datetime import date, timedelta
import random
import pandas as pd
import os
import json
import sys
from typing import Dict, List, Tuple, Optional

from app import create_app
from app.models import (
    Department, Lecturer, Course, Student,
    Program, NonAcademicStaff, ResearchProject
)
from app.utils.database import db

# Initialize Flask application context
app = create_app()


def load_faculty_data() -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """Load and transform faculty structure data from JSON file.

    Returns:
        tuple: Contains two dictionaries:
            - faculty_departments: Maps faculties to their departments
            - dept_subjects: Maps departments to their subjects

    Raises:
        FileNotFoundError: If faculty data file is not found
        JSONDecodeError: If faculty data file contains invalid JSON
    """
    try:
        with open(os.path.join('data', 'faculty_department_subject.json')) as f:
            data = json.load(f)
            # Create both mappings in a single pass for efficiency
            faculty_departments: Dict[str, List[str]] = {}
            dept_subjects: Dict[str, List[str]] = {}

            for faculty, departments in data.items():
                faculty_departments[faculty] = list(departments.keys())
                dept_subjects.update(departments)

            return faculty_departments, dept_subjects
    except FileNotFoundError:
        print("❌ Faculty data file not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print("❌ Invalid JSON format in faculty data file")
        sys.exit(1)


# Load faculty structure data
FACULTY_DEPARTMENTS, department_subjects = load_faculty_data()

# Define mapping between faculties and their possible degree types
FACULTY_DEGREE_MAPPING = {
    "Faculty of Arts and Humanities": ["Arts"],
    "Faculty of Social Sciences": ["Arts", "Science"],
    "Faculty of Mathematics and Science": ["Science"],
    "Faculty of Engineering": ["Science", "Engineering"],
    "Faculty of Medicine and Health Sciences": ["Science"],
    "Faculty of Business and Economics": ["Arts", "Science", "Business"],
    "Faculty of Law": ["Arts"],
    "Faculty of Computer Science": ["Science"]
}


def maybe_null(nullable_chance: float = 0.7) -> bool:
    """Determine if a nullable field should be filled based on probability.
    
    Args:
        nullable_chance: Probability (0-1) that the field should be filled (default: 0.7)

    Returns:
        bool: True if field should be filled, False if it should be null
    """
    return random.random() < nullable_chance


def load_people_data() -> pd.DataFrame:
    """Load and validate person data from Excel file.

    The function performs several validation steps:
    1. Verifies file existence
    2. Checks for required columns
    3. Validates data completeness
    4. Verifies email format
    5. Ensures minimum record count

    Returns:
        pd.DataFrame: DataFrame containing validated people records

    Raises:
        FileNotFoundError: If Excel file cannot be found
        ValueError: If required columns are missing or data is invalid
        pd.errors.EmptyDataError: If Excel file is empty
        Exception: For other Excel loading errors
    """
    required_columns = ['First Name', 'Last Name', 'Email']
    excel_path = os.path.join('data', '20250516220523_7885.xlsx')

    try:
        # Check if file exists
        if not os.path.exists(excel_path):
            raise FileNotFoundError(f"Excel file not found at {excel_path}")

        # Load Excel file
        df = pd.read_excel(excel_path)

        # Check if file is empty
        if df.empty:
            raise pd.errors.EmptyDataError("Excel file is empty")

        # Validate required columns
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")

        # Remove rows with missing required values
        df = df.dropna(subset=required_columns)

        # Validate data
        if len(df) < 100:  # Minimum required records
            raise ValueError(f"Insufficient records in Excel file. Found {len(df)}, need at least 100")

        # Basic email format validation
        invalid_emails = df[~df['Email'].str.contains('@', na=False)]
        if not invalid_emails.empty:
            print(f"⚠️ Warning: Found {len(invalid_emails)} invalid email addresses")
            # Remove invalid email rows
            df = df[df['Email'].str.contains('@', na=False)]

        print(f"✅ Loaded {len(df)} valid records from Excel file")
        return df

    except pd.errors.EmptyDataError:
        print("❌ Excel file is empty")
        sys.exit(1)
    except pd.errors.ParserError:
        print("❌ Invalid Excel file format")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error loading Excel file: {str(e)}")
        sys.exit(1)


def get_department_subjects(dept_name: str) -> List[str]:
    """Get list of subjects taught in a department.

    Args:
        dept_name: Name of the department

    Returns:
        list: Subject names associated with the department, empty if not found
    """
    return department_subjects.get(dept_name, [])


def create_test_data() -> None:
    """Create and populate database with test data.

    This function orchestrates the creation of test data in the following order:
    1. Clears existing database tables
    2. Loads and validates external data sources
    3. Creates departments and faculty structure
    4. Generates lecturers with appropriate qualifications
    5. Creates courses with valid prerequisites
    6. Establishes degree programs
    7. Enrolls students in programs and courses
    8. Assigns non-academic staff
    9. Creates research projects with teams

    The data is created with realistic relationships and constraints.
    All database operations are performed within a transaction.

    Raises:
        ValueError: If insufficient records in source data
        Exception: For other database or data creation errors
    """
    with app.app_context():
        try:
            # Clear existing database
            db.drop_all()
            db.create_all()

            # Load and validate source data with minimum requirements
            min_required = {
                'students': 100,
                'lecturers': 20,
                'staff': 10
            }

            people_df = load_people_data()

            # Ensure minimum required records
            total_required = sum(min_required.values())
            if len(people_df) < total_required:
                raise ValueError(
                    f"Insufficient records in Excel file. "
                    f"Need at least {total_required}, found {len(people_df)}"
                )

            # Split data ensuring minimum requirements
            student_data = people_df.iloc[:800]
            lecturer_data = people_df.iloc[800:925]
            staff_data = people_df.iloc[925:]

            if len(student_data) < min_required['students']:
                raise ValueError(f"Insufficient student records. Need {min_required['students']}")
            if len(lecturer_data) < min_required['lecturers']:
                raise ValueError(f"Insufficient lecturer records. Need {min_required['lecturers']}")
            if len(staff_data) < min_required['staff']:
                raise ValueError(f"Insufficient staff records. Need {min_required['staff']}")

            # ======================
            # Create Departments
            # ======================
            departments = []
            faculty_dept_map = {}

            for faculty, dept_list in FACULTY_DEPARTMENTS.items():
                # Select 3-5 departments per faculty
                selected_depts = random.sample(
                    dept_list,
                    min(random.randint(3, 5), len(dept_list))
                )

                faculty_depts = []
                for dept_name in selected_depts:
                    # Create department
                    research_areas = None
                    if maybe_null():
                        research_areas = ", ".join([
                            random.choice([
                                "Artificial Intelligence", "Machine Learning",
                                "Ethics", "Education", "Interdisciplinary Studies",
                                "Policy", "Human-Computer Interaction",
                                "Psychology", "Philosophy", "Digital Transformation",
                                "Quantitative Methods", "Qualitative Research",
                                "Applied Research", "Sustainable Development"
                            ]) for _ in range(random.randint(1, 3))
                        ])

                    dept = Department(
                        name=dept_name,
                        faculty=faculty,
                        research_areas=research_areas
                    )
                    departments.append(dept)
                    faculty_depts.append(dept)
                    db.session.add(dept)

                faculty_dept_map[faculty] = faculty_depts

            # ======================
            # Create Lecturers
            # ======================
            lecturers = []
            qualifications = [
                "PhD", "x2 PhD", "MPhil", "MRes",
                "Masters", "x2 Masters", "DPhil"
            ]

            def create_lecturer(row, department):
                """Helper function to create a lecturer with given data."""
                research_interests = None
                if maybe_null():
                    interests = [
                        "Artificial Intelligence", "Machine Learning",
                        "Ethics", "Education", "Interdisciplinary Studies",
                        "Policy", "Human-Computer Interaction",
                        "Psychology", "Philosophy", "Digital Transformation",
                        "Quantitative Methods", "Qualitative Research",
                        "Applied Research", "Sustainable Development"
                    ]
                    research_interests = ";".join(random.sample(interests, random.randint(1, 3)))

                # Contract details (nullable)
                contract_details = None
                if maybe_null():
                    contract_details = random.choice([
                        "Tenure-track", "Tenured", "Visiting Professor",
                        "Fixed-term contract", "Research fellowship"
                    ])

                return Lecturer(
                    name=f"{row['First Name']} {row['Last Name']}",
                    email=row['Email'],
                    department=department,
                    academic_qualifications=random.choice(qualifications),
                    employment_type=random.choice(["Full-Time", "Part-Time", "Contract"]),
                    contract_details=contract_details,
                    areas_of_expertise=None if not maybe_null() else random.choice(
                        get_department_subjects(department.name)),
                    research_interests=research_interests,
                    publications=None if not maybe_null() else random.choice([
                        "Journal publications; Conference papers",
                        "Journal publications", "Books; Book chapters",
                        "Patents; Technical reports"
                    ]),
                )

            def distribute_lecturers(lecturer_data, departments):
                """Distribute lecturers across departments ensuring minimum requirements."""
                attempts = 0
                max_attempts = 100  # Prevent infinite loops

                while attempts < max_attempts:
                    department_counts = {dept: 0 for dept in departments}
                    lecturers = []

                    # Try to distribute lecturers
                    for idx, row in lecturer_data.iterrows():
                        # Prioritize departments with fewer lecturers
                        understaffed_depts = [
                            d for d in departments
                            if department_counts[d] < 2
                        ]

                        if understaffed_depts:
                            # Assign to understaffed department
                            department = random.choice(understaffed_depts)
                        else:
                            # All departments have minimum staff, assign randomly
                            department = random.choice(departments)

                        lecturer = create_lecturer(row, department)
                        lecturers.append(lecturer)
                        department_counts[department] += 1

                    # Check if distribution meets requirements
                    if all(count >= 2 for count in department_counts.values()):
                        return lecturers

                    attempts += 1

                raise ValueError("Failed to distribute lecturers after maximum attempts")

            # Use the new distribution function
            try:
                lecturers = distribute_lecturers(lecturer_data, departments)
                for lecturer in lecturers:
                    db.session.add(lecturer)
            except ValueError as e:
                print(f"❌ Error: {str(e)}")
                sys.exit(1)

            # ======================
            # Create Courses
            # ======================
            courses = []
            course_codes = set()

            # Generate courses for each department
            for dept in departments:
                # Create 1-5 courses per department
                for _ in range(random.randint(1, 5)):
                    # Generate unique course code
                    prefix = ''.join(w[0] for w in dept.name.split() if w not in ["of", "and", "the"]).upper()
                    while True:
                        code = f"{prefix}{random.randint(100, 499)}"
                        if code not in course_codes:
                            course_codes.add(code)
                            break

                    # Select 1-2 lecturers from same department
                    dept_lecturers = [lecturer for lecturer in lecturers if lecturer.department == dept]
                    if not dept_lecturers:
                        # Skip creating a course if no lecturers in the department are available
                        continue

                    course_lecturers = random.sample(
                        dept_lecturers,
                        min(random.randint(1, 2), len(dept_lecturers))
                    )

                    course_names = [
                        "Introduction to", "Advanced", "Principles of",
                        "Topics in", "Seminar in", "Fundamentals of",
                        "Theories of", "Research Methods in"
                    ]

                    # Get subjects for this department from JSON mapping
                    dept_subjects = get_department_subjects(dept.name)

                    # If no subjects found, skip this course
                    if not dept_subjects:
                        continue

                    subject = random.choice(dept_subjects)

                    course = Course(
                        code=code,
                        name=f"{random.choice(course_names)} {subject}",
                        description=f"This course covers essential concepts in {subject}",
                        level=random.choice(["Foundation", "Undergraduate", "Graduate", "Doctoral"]),
                        credits=random.choice([5, 10, 15, 20, 30]),
                        schedule=None if not maybe_null() else f"{random.choice(['Mon', 'Tue', 'Wed', 'Thu', 'Fri'])} "
                                                               f"{random.randint(9, 17)}:"
                                                               f"{random.choice(['00', '20', '30', '40'])}",
                        department=dept,
                        lecturers=course_lecturers
                    )
                    courses.append(course)
                    db.session.add(course)

            # Update course load for lecturers
            for lecturer in lecturers:
                lecturer.update_course_load()

            # ======================
            # Create Programs
            # ======================
            programs = []

            # Create programs for each department
            for dept in departments:
                # Create 1-3 programs per department
                for _ in range(random.randint(1, 3)):
                    degree_types = ["Bachelor of", "Master of", "PhD in", 'Researcher in']
                    degree_name = FACULTY_DEGREE_MAPPING.get(dept.faculty, ["General Studies"])
                    dept_name = dept.name.replace("Department of ", "")

                    degree_type = random.choice(degree_types)

                    # Set duration based on degree type
                    if degree_type == "Bachelor of":
                        duration = random.randint(3, 4)
                    elif degree_type == "Master of":
                        duration = random.randint(1, 2)
                    elif degree_type == "PhD in":
                        duration = random.randint(3, 5)
                    else:  # Researcher in
                        duration = random.randint(1, 3)

                    program = Program(
                        name=f"{degree_type} {dept_name}",
                        degree_awarded=f"{degree_type} {random.choice(degree_name)}",
                        duration=duration,
                        department=dept,
                        course_requirements=None if not maybe_null()
                        else f"{random.choice(['Core courses', 'Core courses plus electives'])}",
                        enrollment_details=None if not maybe_null()
                        else f"Open enrollment in {random.choice(['Fall', 'Spring', 'Fall/Spring', 'Winter'])}"
                    )
                    programs.append(program)
                    db.session.add(program)

            # ======================
            # Create Students
            # ======================
            students = []

            for idx, row in student_data.iterrows():
                # Select a random program
                program = random.choice(programs)

                # Select advisor from same department as program
                dept_lecturers = [lecturer for lecturer in lecturers if lecturer.department == program.department]
                advisor = random.choice(dept_lecturers) if dept_lecturers else random.choice(lecturers)

                # Select 1-5 courses from same department
                dept_courses = [c for c in courses if c.department == program.department]

                # Handle course assignment
                if not dept_courses or random.random() < 0.12:
                    student_courses = []  # Always use empty list instead of None
                else:
                    student_courses = random.sample(
                        dept_courses,
                        min(random.randint(1, 5), len(dept_courses))
                    )

                # Generate birth date (18-50 years old)
                today = date.today()
                age = random.randint(18, 50)
                birth_year = today.year - age
                birth_month = random.randint(1, 12)
                birth_day = random.randint(1, 28)
                birth_date = date(birth_year, birth_month, birth_day)

                student = Student(
                    name=f"{row['First Name']} {row['Last Name']}",
                    email=row['Email'],
                    date_of_birth=birth_date,
                    year_of_study=random.randint(1, 4),
                    current_grades=round(random.uniform(35.0, 85.0), 1),
                    graduation_status=None if not maybe_null() else random.choice([True, False]),
                    disciplinary_record=None if not maybe_null() else random.choice([True, False]),
                    program=program,
                    advisor=advisor,
                    courses=student_courses
                )
                students.append(student)
                db.session.add(student)

            # ======================
            # Create Staff
            # ======================
            staff = []

            job_titles = [
                "Administrator", "Secretary", "Lab Technician",
                "IT Support", "Librarian", "Maintenance",
                "Security Officer", "Careers Advisor"
            ]

            for idx, row in staff_data.iterrows():
                # Select random department
                department = random.choice(departments)

                staff_member = NonAcademicStaff(
                    name=f"{row['First Name']} {row['Last Name']}",
                    job_title=random.choice(job_titles),
                    employment_type=random.choice(["Full-Time", "Part-Time", "Contract"]),
                    department=department
                )
                staff.append(staff_member)
                db.session.add(staff_member)

            # ======================
            # Create Research Projects
            # ======================
            projects = []

            # Create 30-50 research projects
            for _ in range(random.randint(30, 50)):
                # Select principal investigator
                pi = random.choice(lecturers)

                # Select team members (1-7 lecturers)
                team_size = random.randint(1, 7)
                team = random.sample(lecturers, min(team_size, len(lecturers)))

                # Ensure PI is in team
                if pi not in team:
                    team.append(pi)

                # Generate outcomes (nullable)
                outcomes = None
                if maybe_null():
                    possible_outcomes = [
                        "New international framework", "3 publications",
                        "Patent application", "Improved algorithm",
                        "United Nations advisory", "Educational software",
                        "Conference presentation", "Industry partnership"
                    ]
                    outcomes = ";".join(random.sample(possible_outcomes, random.randint(1, 3)))

                project_titles = [
                    "Advanced Research in", "Study of", "Investigation into",
                    "Development of", "Analysis of", "Applications of", "Review of",
                    "Exploration of", "Impact of", "Trends in", "Future of"
                ]

                subjects = [
                    "Machine Learning", "Artificial Intelligence", "Interdisciplinary Studies",
                    "Global Digital Infrastructure", "World Sustainability", "Marcusian Studies",
                    "Global Security", "Climate Change", "Academic Evolution", "European Union",
                    "[redacted] - CLASSIFIED RESEARCH", "Educational Technology", "Smart University Initiative (SUI)"
                ]

                project = ResearchProject(
                    title=f"{random.choice(project_titles)} {random.choice(subjects)}",
                    funding_sources=None if not maybe_null() else random.choice([
                        "European Universities Initiative (EUI)", "ERC Synergy Grants", "Alumni Fund",
                        "University Grant", "Industry Partnership", "National Science Foundation (NSF)",
                        "UK Research and Innovation (UKRI)", "Horizon Europe", "Gates Foundation"
                    ]),
                    principal_investigator=pi,
                    team_members=team,
                    publications=None if not maybe_null() else random.choice(["Journal publications; Conference papers",
                                                                              "Journal publications",
                                                                              "Patents; Technical reports"]),
                    outcomes=outcomes
                )
                projects.append(project)
                db.session.add(project)

            # Commit all changes
            db.session.commit()

            print(f"✅ Database seeded successfully with:")
            print(f"- {len(departments)} departments")
            print(f"- {len(lecturers)} lecturers")
            print(f"- {len(courses)} courses")
            print(f"- {len(programs)} programs")
            print(f"- {len(students)} students")
            print(f"- {len(staff)} non-academic staff")
            print(f"- {len(projects)} research projects")

        except Exception as e:
            print(f"❌ Error creating test data: {str(e)}")
            sys.exit(1)


if __name__ == "__main__":
    create_test_data()
