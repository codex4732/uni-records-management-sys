"""
API Response Models for University Record Management System (URMS).

This module contains all Flask-RESTx model definitions used for API response
serialization and documentation. Models are organized by entity type and
include both basic and detailed representations.
"""

from flask_restx import fields


def create_models(ns):
    """
    Create and register all API response models with the given namespace.
    
    Args:
        ns: Flask-RESTx Namespace instance
        
    Returns:
        dict: Dictionary containing all model definitions
    """
    
    # ======================
    # Student Models
    # ======================
    
    student_model = ns.model('Student', {
        'student_id': fields.Integer(description='Unique student identifier'),
        'name': fields.String(required=True, description='Full name'),
        'email': fields.String(description='University email address'),
        'year': fields.Integer(description='Current year of study (1-5)', min=1, max=5),
        'current_grade': fields.Float(description='Current average grade', min=0, max=100),
        'program': fields.String(description='Enrolled academic program'),
        'advisor': fields.String(description='Assigned faculty advisor'),
        'enrollment_count': fields.Integer(description='Total number of active enrollments'),
        'courses_enrolled': fields.List(fields.String, description='List of course codes'),
        'graduation_status': fields.Boolean(description='Graduation status'),
        'disciplinary_record': fields.Boolean(description='Disciplinary record status')
    })

    student_enrollment_detail_model = ns.model('StudentEnrollmentDetail', {
        'enrollment_id': fields.Integer(description='Enrollment ID'),
        'course_code': fields.String(description='Course code'),
        'course_name': fields.String(description='Course name'),
        'course_credits': fields.Integer(description='Course credit hours'),
        'course_level': fields.String(description='Course level'),
        'semester': fields.String(description='Semester'),
        'year': fields.Integer(description='Academic year'),
        'lecturer': fields.String(description='Lecturer name'),
        'enrollment_date': fields.String(description='Enrollment date'),
        'enrollment_grade': fields.Float(description='Grade received'),
        'status': fields.String(description='Enrollment status')
    })

    student_program_detail_model = ns.model('StudentProgramDetail', {
        'program_id': fields.Integer(description='Program ID'),
        'program_name': fields.String(description='Program name'),
        'degree_awarded': fields.String(description='Degree awarded'),
        'duration': fields.Integer(description='Program duration in years'),
        'department': fields.String(description='Department name')
    })

    student_advisor_detail_model = ns.model('StudentAdvisorDetail', {
        'advisor_id': fields.Integer(description='Advisor ID'),
        'advisor_name': fields.String(description='Advisor name'),
        'advisor_email': fields.String(description='Advisor email'),
        'advisor_department': fields.String(description='Advisor department')
    })

    student_detail_model = ns.model('StudentDetail', {
        'student_id': fields.Integer(description='Student ID'),
        'name': fields.String(description='Student name'),
        'email': fields.String(description='Email address'),
        'year': fields.Integer(description='Year of study'),
        'current_grade': fields.Float(description='Current grade'),
        'program_details': fields.Nested(student_program_detail_model, description='Detailed program information'),
        'advisor_details': fields.Nested(student_advisor_detail_model, description='Detailed advisor information'),
        'enrollment_count': fields.Integer(description='Total number of enrollments'),
        'total_enrolled_credits': fields.Integer(description='Total enrolled credit hours'),
        'completed_credits': fields.Integer(description='Total completed credit hours'),
        'calculated_gpa': fields.Float(description='Calculated GPA from completed courses'),
        'active_enrollment_count': fields.Integer(description='Number of active enrollments'),
        'active_enrollments': fields.List(fields.Nested(student_enrollment_detail_model), description='Active enrollments'),
        'completed_enrollment_count': fields.Integer(description='Number of completed enrollments'),
        'completed_enrollments': fields.List(fields.Nested(student_enrollment_detail_model), description='Completed enrollments'),
        'withdrawn_enrollment_count': fields.Integer(description='Number of withdrawn enrollments'),
        'withdrawn_enrollments': fields.List(fields.Nested(student_enrollment_detail_model), description='Withdrawn enrollments'),
        'failed_enrollment_count': fields.Integer(description='Number of failed enrollments'),
        'failed_enrollments': fields.List(fields.Nested(student_enrollment_detail_model), description='Failed enrollments'),
        'graduation_status': fields.Boolean(description='Graduation status'),
        'disciplinary_record': fields.Boolean(description='Disciplinary record')
    })

    # ======================
    # Lecturer Models
    # ======================
    
    lecturer_model = ns.model('Lecturer', {
        'lecturer_id': fields.Integer(description='Unique lecturer identifier'),
        'name': fields.String(required=True, description='Full name'),
        'email': fields.String(description='University email address'),
        'department': fields.String(description='Affiliated department'),
        'employment_type': fields.String(description='Employment type'),
        'course_load': fields.Integer(description='Number of courses taught', min=0),
        'areas_of_expertise': fields.List(fields.String, description='Areas of expertise'),
        'research_areas': fields.List(fields.String, description='Research interests'),
        'academic_qualifications': fields.String(description='Academic qualifications')
    })

    lecturer_research_project_model = ns.model('LecturerResearchProject', {
        'project_id': fields.Integer(description='Project ID'),
        'title': fields.String(description='Project title'),
        'role': fields.String(description='Role in project (Principal Investigator or Team Member)'),
        'funding_sources': fields.String(description='Funding sources'),
        'principal_investigator': fields.String(description='Principal investigator name (for team member projects)'),
        'outcomes': fields.List(fields.String, description='Project outcomes')
    })

    lecturer_course_taught_model = ns.model('LecturerCourseTaught', {
        'course_code': fields.String(description='Course code'),
        'course_name': fields.String(description='Course name'),
        'semester': fields.String(description='Semester'),
        'year': fields.Integer(description='Academic year'),
        'enrolled_students': fields.Integer(description='Number of enrolled students')
    })

    lecturer_advised_student_model = ns.model('LecturerAdvisedStudent', {
        'student_id': fields.Integer(description='Student ID'),
        'name': fields.String(description='Student name'),
        'year': fields.Integer(description='Year of study'),
        'program': fields.String(description='Program name')
    })

    lecturer_detail_model = ns.model('LecturerDetail', {
        'lecturer_id': fields.Integer(description='Lecturer ID'),
        'name': fields.String(description='Lecturer name'),
        'email': fields.String(description='Email address'),
        'department': fields.String(description='Department name'),
        'employment_type': fields.String(description='Employment type'),
        'contract_details': fields.String(description='Contract details'),
        'areas_of_expertise': fields.List(fields.String, description='Areas of expertise'),
        'research_areas': fields.List(fields.String, description='Research interests'),
        'academic_qualifications': fields.String(description='Academic qualifications'),
        'publications': fields.List(fields.String, description='Publications list'),
        'course_load': fields.Integer(description='Current course load'),
        'courses_taught': fields.List(fields.Nested(lecturer_course_taught_model), description='Courses currently taught'),
        'advisee_count': fields.Integer(description='Number of students advised'),
        'advised_students': fields.List(fields.Nested(lecturer_advised_student_model), description='Students being advised'),
        'principal_investigator_count': fields.Integer(description='Number of projects as principal investigator'),
        'team_member_count': fields.Integer(description='Number of projects as team member'),
        'total_research_projects': fields.Integer(description='Total number of research projects'),
        'research_projects': fields.List(fields.Nested(lecturer_research_project_model), description='All research projects')
    })

    # ======================
    # Course Models
    # ======================
    
    course_model = ns.model('Course', {
        'course_id': fields.Integer(description='Unique course identifier'),
        'code': fields.String(required=True, pattern=r'[A-Z]{2,4}\d{3}', example='CS101',
                             description='Course code (e.g. CS101)'),
        'name': fields.String(required=True, description='Course title'),
        'description': fields.String(description='Course description'),
        'level': fields.String(description='Course level'),
        'credits': fields.Integer(min=1, max=30, description='Academic credits'),
        'schedule': fields.String(description='Course schedule'),
        'department_id': fields.Integer(description='Offering department ID'),
        'student_count': fields.Integer(description='Number of enrolled students', min=0),
        'lecturer_count': fields.Integer(description='Number of assigned lecturers', min=0)
    })

    student_in_course_model = ns.model('StudentInCourse', {
        'student_id': fields.Integer(description='Student ID'),
        'name': fields.String(description='Student name'),
        'year': fields.Integer(description='Year of study'),
        'status': fields.String(description='Enrollment status')
    })

    lecturer_in_course_model = ns.model('LecturerInCourse', {
        'lecturer_id': fields.Integer(description='Lecturer ID'),
        'name': fields.String(description='Lecturer name'),
        'email': fields.String(description='Lecturer email'),
        'department': fields.String(description='Department name')
    })

    course_offering_model = ns.model('CourseOffering', {
        'offering_id': fields.Integer(description='Offering ID'),
        'semester': fields.String(description='Semester'),
        'year': fields.Integer(description='Academic year'),
        'lecturer': fields.String(description='Lecturer name')
    })

    course_detail_model = ns.model('CourseDetail', {
        'course_id': fields.Integer(description='Course ID'),
        'code': fields.String(description='Course code'),
        'name': fields.String(description='Course name'),
        'description': fields.String(description='Course description'),
        'level': fields.String(description='Course level'),
        'credits': fields.Integer(description='Credit hours'),
        'schedule': fields.String(description='Course schedule'),
        'department_id': fields.Integer(description='Department ID'),
        'offerings': fields.List(fields.Nested(course_offering_model), description='Course offerings by semester'),
        'student_count': fields.Integer(description='Total number of students'),
        'students': fields.List(fields.Nested(student_in_course_model), description='Students enrolled in this course'),
        'lecturer_count': fields.Integer(description='Total number of lecturers'),
        'lecturers': fields.List(fields.Nested(lecturer_in_course_model), description='Lecturers teaching this course'),
    })

    # ======================
    # Enrollment Models
    # ======================
    
    enrollment_student_model = ns.model('EnrollmentStudent', {
        'student_id': fields.Integer(description='Student ID'),
        'name': fields.String(description='Student name'),
        'year': fields.Integer(description='Year of study'),
        'program': fields.String(description='Program name'),
        'advisor': fields.String(description='Advisor name'),
        'enrollment_count': fields.Integer(description='Total number of enrollments')
    })

    enrollment_lecturer_model = ns.model('EnrollmentLecturer', {
        'lecturer_id': fields.Integer(description='Lecturer ID'),
        'name': fields.String(description='Lecturer name'),
        'email': fields.String(description='Lecturer email'),
        'department': fields.String(description='Department name'),
        'academic_qualifications': fields.String(description='Academic qualifications')
    })

    enrollment_simplified_model = ns.model('EnrollmentSimplified', {
        'enrollment_id': fields.Integer(description='Enrollment ID'),
        'student': fields.Nested(enrollment_student_model, description='Basic student information'),
        'course': fields.Nested(course_model, description='Full course details'),
        'lecturer': fields.Nested(enrollment_lecturer_model, description='Basic lecturer information'),
        'enrollment_date': fields.String(description='Enrollment date'),
        'grade': fields.Float(description='Grade received'),
        'status': fields.String(description='Enrollment status')
    })

    # ======================
    # Department Models
    # ======================
    
    advisor_model = ns.model('Advisor', {
        'name': fields.String(description='Advisor name'),
        'email': fields.String(description='Contact email'),
        'department': fields.String(description='Department name'),
        'areas_of_expertise': fields.List(fields.String, description='Areas of expertise'),
        'research_areas': fields.List(fields.String, description='Research interests'),
        'academic_qualifications': fields.String(description='Academic qualifications')
    })

    department_model = ns.model('Department', {
        'department_id': fields.Integer(description='Unique department identifier'),
        'name': fields.String(required=True, description='Department name'),
        'faculty': fields.String(description='Faculty name'),
        'research_areas': fields.String(description='Research focus areas'),
        'lecturer_count': fields.Integer(description='Number of lecturers', min=0),
        'course_count': fields.Integer(description='Number of courses offered', min=0),
        'program_count': fields.Integer(description='Number of programs offered', min=0)
    })

    lecturer_in_department_model = ns.model('LecturerInDepartment', {
        'lecturer_id': fields.Integer(description='Lecturer ID'),
        'name': fields.String(description='Lecturer name'),
        'email': fields.String(description='Lecturer email'),
        'employment_type': fields.String(description='Employment type'),
        'areas_of_expertise': fields.List(fields.String, description='Areas of expertise'),
        'course_load': fields.Integer(description='Current course load'),
        'research_interests': fields.List(fields.String, description='Research interests')
    })

    course_in_department_model = ns.model('CourseInDepartment', {
        'course_id': fields.Integer(description='Course ID'),
        'code': fields.String(description='Course code'),
        'name': fields.String(description='Course name'),
        'level': fields.String(description='Course level'),
        'credits': fields.Integer(description='Credit hours'),
        'description': fields.String(description='Course description')
    })

    program_in_department_model = ns.model('ProgramInDepartment', {
        'program_id': fields.Integer(description='Program ID'),
        'name': fields.String(description='Program name'),
        'degree_awarded': fields.String(description='Degree awarded'),
        'duration': fields.Integer(description='Duration in years'),
        'enrolled_students': fields.Integer(description='Number of enrolled students')
    })

    staff_in_department_model = ns.model('StaffInDepartment', {
        'staff_id': fields.Integer(description='Staff ID'),
        'name': fields.String(description='Staff name'),
        'job_title': fields.String(description='Job title'),
        'employment_type': fields.String(description='Employment type')
    })

    department_detail_model = ns.model('DepartmentDetail', {
        'department_id': fields.Integer(description='Department ID'),
        'name': fields.String(description='Department name'),
        'faculty': fields.String(description='Faculty name'),
        'research_areas': fields.String(description='Research areas'),
        'lecturer_count': fields.Integer(description='Total number of lecturers'),
        'lecturers': fields.List(fields.Nested(lecturer_in_department_model), description='Lecturers in this department'),
        'course_count': fields.Integer(description='Total number of courses'),
        'courses': fields.List(fields.Nested(course_in_department_model), description='Courses offered by this department'),
        'program_count': fields.Integer(description='Total number of programs'),
        'programs': fields.List(fields.Nested(program_in_department_model), description='Programs offered by this department'),
        'staff_count': fields.Integer(description='Total number of staff members'),
        'staff_members': fields.List(fields.Nested(staff_in_department_model), description='Non-academic staff in this department')
    })

    # ======================
    # Staff Models
    # ======================
    
    staff_model = ns.model('Staff', {
        'staff_id': fields.Integer(description='Unique staff identifier'),
        'name': fields.String(required=True, description='Full name'),
        'job_title': fields.String(description='Job title'),
        'employment_type': fields.String(description='Employment type'),
        'department': fields.String(description='Affiliated department')
    })

    return {
        'student_model': student_model,
        'student_enrollment_detail_model': student_enrollment_detail_model,
        'student_program_detail_model': student_program_detail_model,
        'student_advisor_detail_model': student_advisor_detail_model,
        'student_detail_model': student_detail_model,
        'lecturer_model': lecturer_model,
        'lecturer_research_project_model': lecturer_research_project_model,
        'lecturer_course_taught_model': lecturer_course_taught_model,
        'lecturer_advised_student_model': lecturer_advised_student_model,
        'lecturer_detail_model': lecturer_detail_model,
        'course_model': course_model,
        'student_in_course_model': student_in_course_model,
        'lecturer_in_course_model': lecturer_in_course_model,
        'course_offering_model': course_offering_model,
        'course_detail_model': course_detail_model,
        'enrollment_student_model': enrollment_student_model,
        'enrollment_lecturer_model': enrollment_lecturer_model,
        'enrollment_simplified_model': enrollment_simplified_model,
        'advisor_model': advisor_model,
        'department_model': department_model,
        'lecturer_in_department_model': lecturer_in_department_model,
        'course_in_department_model': course_in_department_model,
        'program_in_department_model': program_in_department_model,
        'staff_in_department_model': staff_in_department_model,
        'department_detail_model': department_detail_model,
        'staff_model': staff_model
    }
