from datetime import date

from app import create_app
from app.models import Department, Lecturer, Course, Student, Program, NonAcademicStaff, ResearchProject
from app.utils.database import db


app = create_app()

def create_test_data():
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()

        # ======================
        # Create Departments
        # ======================
        cs_dept = Department(
            name="Computer Science",
            faculty="Engineering",
            research_areas="Artificial Intelligence, Cybersecurity"
        )
        
        math_dept = Department(
            name="Mathematics",
            faculty="Science",
            research_areas="Pure Mathematics, Applied Mathematics"
        )

        # ======================
        # Create Lecturers
        # ======================
        lecturer1 = Lecturer(
            name="Dr. Alice Smith",
            email="a.smith@uni.ac.uk",
            department=cs_dept,
            research_interests="Machine Learning;Neural Networks",
            employment_type="Full-Time",
            academic_qualifications="PhD in Computer Science"
        )

        lecturer2 = Lecturer(
            name="Dr. Bob Johnson",
            email="b.johnson@uni.ac.uk",
            academic_qualifications="PhD in Mathematics",  # Added this line
            department=math_dept,
            research_interests="Number Theory;Cryptography",
            employment_type="Part-Time"
        )

        # ======================
        # Create Courses
        # ======================
        course1 = Course(
            code="CS101",
            name="Introduction to Programming",
            description="Fundamentals of programming using Python",
            level="Undergraduate",
            credits=15,
            department=cs_dept,
            lecturers=[lecturer1]
        )

        course2 = Course(
            code="CS102",
            name="Data Structures",
            description="Common data structures and algorithms",
            level="Undergraduate",
            credits=20,
            department=cs_dept,
            lecturers=[lecturer1]
        )

        course3 = Course(
            code="MATH101",
            name="Calculus I",
            description="Introduction to differential calculus",
            level="Foundation",
            credits=15,
            department=math_dept,
            lecturers=[lecturer2]
        )

        # ======================
        # Create Programs
        # ======================
        cs_program = Program(
            name="Computer Science BSc",
            degree_awarded="Bachelor of Science",
            duration=3,
            department=cs_dept
        )

        math_program = Program(
            name="Mathematics MSci",
            degree_awarded="Master of Science",
            duration=4,
            department=math_dept
        )

        # ======================
        # Create Students
        # ======================
        student1 = Student(
            name="John Doe",
            email="john.doe@student.uni.ac.uk",
            date_of_birth=date(2000, 1, 15),
            year_of_study=4,
            current_grades=85.5,
            program=cs_program,
            advisor=lecturer1,
            courses=[course1, course2]
        )

        student2 = Student(
            name="Jane Smith",
            email="jane.smith@student.uni.ac.uk",
            date_of_birth=date(2002, 5, 20),
            year_of_study=3,
            current_grades=65.0,
            program=math_program,
            advisor=lecturer2,
            courses=[course3]
        )

        # ======================
        # Create Staff
        # ======================
        staff1 = NonAcademicStaff(
            name="Sarah Wilson",
            job_title="Department Administrator",
            employment_type="Full-Time",
            department=cs_dept
        )

        staff2 = NonAcademicStaff(
            name="Michael Brown",
            job_title="Lab Technician",
            employment_type="Part-Time",
            department=math_dept
        )

        # ======================
        # Create Research Projects
        # ======================
        project1 = ResearchProject(
            title="Advanced Machine Learning Techniques",
            funding_sources="UK Research Council",
            principal_investigator=lecturer1,
            team_members=[lecturer1, lecturer2],
            outcomes="New ML framework;3 publications"
        )

        project2 = ResearchProject(
            title="Number Theory in Cryptography",
            funding_sources="EU Horizon 2020",
            principal_investigator=lecturer2,
            outcomes="New encryption algorithm"
        )

        # Add all objects to session
        db.session.add_all([
            cs_dept, math_dept,
            lecturer1, lecturer2,
            course1, course2, course3,
            cs_program, math_program,
            student1, student2,
            staff1, staff2,
            project1, project2
        ])
        
        db.session.commit()

        print("✅ Database seeded successfully!")

if __name__ == "__main__":
    create_test_data()
