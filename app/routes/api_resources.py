"""
API Resource Classes for University Record Management System.

This module contains all Flask-RESTx Resource classes that define the API endpoints
and their corresponding HTTP methods. Each resource handles specific entity operations
and includes comprehensive error handling and validation.
"""

from flask import request
from flask_restx import Resource
from datetime import datetime, date
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError

from app.models import (
    Student, Lecturer, Course, Department, Program, Enrollment, 
    CourseOffering, NonAcademicStaff, ResearchProject
)
from app.utils.database import db


class StudentsList(Resource):
    """Resource for handling multiple students operations."""
    
    def get(self, ns, models):
        """List students with optional filtering."""
        # Parse query parameters
        year = request.args.get('year', type=int)
        min_grade = request.args.get('min_grade', type=float)
        max_grade = request.args.get('max_grade', type=float)
        program_id = request.args.get('program_id', type=int)
        department_id = request.args.get('department_id', type=int)
        graduation_status = request.args.get('graduation_status')
        unregistered = request.args.get('unregistered', '').lower() == 'true'
        limit = request.args.get('limit', default=100, type=int)
        offset = request.args.get('offset', default=0, type=int)

        # Validate parameters
        if limit > 1000:
            ns.abort(400, "Limit cannot exceed 1000")
        if limit <= 0:
            ns.abort(400, "Limit must be positive")
        if offset < 0:
            ns.abort(400, "Offset cannot be negative")
        if min_grade is not None and (min_grade < 0 or min_grade > 100):
            ns.abort(400, "min_grade must be between 0 and 100")
        if max_grade is not None and (max_grade < 0 or max_grade > 100):
            ns.abort(400, "max_grade must be between 0 and 100")
        if year is not None and (year < 1 or year > 5):
            ns.abort(400, "year must be between 1 and 5")

        try:
            query = db.session.query(Student).options(
                selectinload(Student.program),
                selectinload(Student.advisor),
                selectinload(Student.enrollments).selectinload(Enrollment.offering).selectinload(CourseOffering.course)
            )

            # Apply filters
            if year:
                query = query.filter(Student.year_of_study == year)
            if min_grade is not None:
                query = query.filter(Student.current_grades >= min_grade)
            if max_grade is not None:
                query = query.filter(Student.current_grades <= max_grade)
            if program_id:
                query = query.filter(Student.enrolled_program_id == program_id)
            if department_id:
                query = query.join(Program).filter(Program.department_id == department_id)
            if graduation_status is not None:
                grad_bool = graduation_status.lower() == 'true'
                query = query.filter(Student.graduation_status == grad_bool)

            # Handle unregistered students filter
            if unregistered:
                now = datetime.now()
                current_year = now.year
                if now.month <= 6:
                    start_date = date(current_year, 1, 1)
                    end_date = date(current_year, 6, 30)
                else:
                    start_date = date(current_year, 8, 1)
                    end_date = date(current_year, 12, 31)

                subquery = db.session.query(Enrollment.student_id).filter(
                    Enrollment.enrollment_date.between(start_date, end_date),
                    Enrollment.status == 'active'
                )
                query = query.filter(~Student.student_id.in_(subquery))

            # Apply pagination and execute
            students = query.offset(offset).limit(limit).all()

            if not students:
                ns.abort(404, "No students found matching the criteria")

            return [s.to_dict() for s in students]

        except SQLAlchemyError as e:
            db.session.rollback()
            ns.abort(500, f"Database error: {str(e)}")
        except Exception as e:
            ns.abort(500, f"Unexpected error: {str(e)}")


class StudentDetail(Resource):
    """Resource for handling individual student operations."""
    
    def get(self, student_id, ns, models):
        """Get detailed information about a specific student."""
        try:
            student = db.session.query(Student).options(
                selectinload(Student.program).selectinload(Program.department),
                selectinload(Student.advisor).selectinload(Lecturer.department),
                selectinload(Student.enrollments).selectinload(Enrollment.offering).selectinload(CourseOffering.course),
                selectinload(Student.enrollments).selectinload(Enrollment.offering).selectinload(CourseOffering.lecturer)
            ).filter(Student.student_id == student_id).first()

            if not student:
                ns.abort(404, f"Student with ID {student_id} not found")

            # Use detailed=True to get comprehensive information
            return student.to_dict(detailed=True)

        except SQLAlchemyError as e:
            db.session.rollback()
            ns.abort(500, f"Database error: {str(e)}")


class StudentAdvisor(Resource):
    """Resource for handling student advisor information."""
    
    def get(self, student_id, ns, models):
        """Get advisor information for a specific student."""
        try:
            student = db.session.query(Student).options(
                selectinload(Student.advisor).selectinload(Lecturer.department)
            ).filter(Student.student_id == student_id).first()

            if not student:
                ns.abort(404, f"Student with ID {student_id} not found")

            if not student.advisor:
                ns.abort(404, "No advisor assigned to this student")

            return student.advisor.to_dict(include_stats=False)

        except SQLAlchemyError as e:
            db.session.rollback()
            ns.abort(500, f"Database error: {str(e)}")


class LecturersList(Resource):
    """Resource for handling multiple lecturers operations."""
    
    def get(self, ns, models):
        """List lecturers with optional filtering."""
        department_id = request.args.get('department_id', type=int)
        expertise_area = request.args.get('expertise_area')
        research_area = request.args.get('research_area')
        employment_type = request.args.get('employment_type')
        min_course_load = request.args.get('min_course_load', type=int)
        max_course_load = request.args.get('max_course_load', type=int)
        top_supervisors = request.args.get('top_supervisors', '').lower() == 'true'
        limit = request.args.get('limit', default=100, type=int)
        offset = request.args.get('offset', default=0, type=int)

        # Validate parameters
        if limit > 1000:
            ns.abort(400, "Limit cannot exceed 1000")
        if limit <= 0:
            ns.abort(400, "Limit must be positive")
        if offset < 0:
            ns.abort(400, "Offset cannot be negative")

        try:
            # Handle top supervisors special case
            if top_supervisors:
                lecturers = db.session.query(
                    Lecturer,
                    func.count(ResearchProject.project_id).label('project_count')
                ).outerjoin(
                    ResearchProject,
                    Lecturer.lecturer_id == ResearchProject.principal_investigator_id
                ).options(
                    selectinload(Lecturer.department)
                ).group_by(Lecturer.lecturer_id).order_by(
                    func.count(ResearchProject.project_id).desc()
                ).offset(offset).limit(limit).all()

                if not lecturers:
                    ns.abort(404, "No research supervisors found")

                return [{
                    **l[0].to_dict(),
                    "projects_count": l[1],
                    "rank": idx + 1 + offset
                } for idx, l in enumerate(lecturers)]

            # Standard filtering with eager loading
            query = db.session.query(Lecturer).options(
                selectinload(Lecturer.department),
                selectinload(Lecturer.offerings)
            )

            if department_id:
                query = query.filter(Lecturer.department_id == department_id)
            if expertise_area:
                query = query.filter(Lecturer.areas_of_expertise.ilike(f"%{expertise_area}%"))
            if research_area:
                query = query.filter(Lecturer.research_interests.ilike(f"%{research_area}%"))
            if employment_type:
                query = query.filter(Lecturer.employment_type.ilike(f"%{employment_type}%"))
            if min_course_load is not None:
                query = query.filter(Lecturer.course_load >= min_course_load)
            if max_course_load is not None:
                query = query.filter(Lecturer.course_load <= max_course_load)

            lecturers = query.offset(offset).limit(limit).all()

            if not lecturers:
                ns.abort(404, "No lecturers found matching the criteria")

            return [l.to_dict() for l in lecturers]

        except SQLAlchemyError as e:
            db.session.rollback()
            ns.abort(500, f"Database error: {str(e)}")
        except Exception as e:
            ns.abort(500, f"Unexpected error: {str(e)}")


class LecturerDetail(Resource):
    """Resource for handling individual lecturer operations."""
    
    def get(self, lecturer_id, ns, models):
        """Get detailed information about a specific lecturer."""
        try:
            lecturer = db.session.query(Lecturer).options(
                selectinload(Lecturer.department),
                selectinload(Lecturer.research_projects),
                selectinload(Lecturer.research_group),
                selectinload(Lecturer.offerings).selectinload(CourseOffering.course),
                selectinload(Lecturer.offerings).selectinload(CourseOffering.enrollments),
                selectinload(Lecturer.advisees).selectinload(Student.program)
            ).filter(Lecturer.lecturer_id == lecturer_id).first()

            if not lecturer:
                ns.abort(404, f"Lecturer with ID {lecturer_id} not found")

            return lecturer.to_dict(detailed=True)

        except SQLAlchemyError as e:
            db.session.rollback()
            ns.abort(500, f"Database error: {str(e)}")


class LecturerAdvisees(Resource):
    """Resource for handling lecturer advisees."""
    
    def get(self, lecturer_id, ns, models):
        """Get list of students advised by a specific lecturer."""
        try:
            # Check if lecturer exists
            lecturer = db.session.get(Lecturer, lecturer_id)
            if not lecturer:
                ns.abort(404, f"Lecturer with ID {lecturer_id} not found")

            students = db.session.query(Student).options(
                selectinload(Student.program),
                selectinload(Student.enrollments).selectinload(Enrollment.offering).selectinload(CourseOffering.course)
            ).filter(Student.advisor_id == lecturer_id).all()

            if not students:
                ns.abort(404, "This lecturer has no advisees")

            return [s.to_dict() for s in students]

        except SQLAlchemyError as e:
            db.session.rollback()
            ns.abort(500, f"Database error: {str(e)}")


class CoursesList(Resource):
    """Resource for handling multiple courses operations."""
    
    def get(self, ns, models):
        """List courses with optional filtering."""
        department_id = request.args.get('department_id', type=int)
        level = request.args.get('level')
        min_credits = request.args.get('min_credits', type=int)
        max_credits = request.args.get('max_credits', type=int)
        lecturer_id = request.args.get('lecturer_id', type=int)
        student_id = request.args.get('student_id', type=int)
        limit = request.args.get('limit', default=100, type=int)
        offset = request.args.get('offset', default=0, type=int)

        # Validate parameters
        if limit > 1000:
            ns.abort(400, "Limit cannot exceed 1000")
        if limit <= 0:
            ns.abort(400, "Limit must be positive")
        if offset < 0:
            ns.abort(400, "Offset cannot be negative")

        try:
            # Build optimized query
            query = db.session.query(Course).options(
                selectinload(Course.department),
                selectinload(Course.offerings)
            )

            if department_id:
                query = query.filter(Course.department_id == department_id)
            if level:
                query = query.filter(Course.level.ilike(f"%{level}%"))
            if min_credits is not None:
                query = query.filter(Course.credits >= min_credits)
            if max_credits is not None:
                query = query.filter(Course.credits <= max_credits)
            if lecturer_id:
                query = query.filter(Course.offerings.any(lecturer_id=lecturer_id))
            if student_id:
                query = query.join(CourseOffering).join(Enrollment).filter(
                    Enrollment.student_id == student_id,
                    Enrollment.status == 'active'
                )

            courses = query.distinct().offset(offset).limit(limit).all()

            if not courses:
                ns.abort(404, "No courses found matching the criteria")

            return [c.to_dict() for c in courses]

        except SQLAlchemyError as e:
            db.session.rollback()
            ns.abort(500, f"Database error: {str(e)}")
        except Exception as e:
            ns.abort(500, f"Unexpected error: {str(e)}")


class CourseDetail(Resource):
    """Resource for handling individual course operations."""
    
    def get(self, course_code, ns, models):
        """Get detailed information about a specific course."""
        try:
            course = db.session.query(Course).filter(Course.code == course_code.upper()).first()

            if not course:
                ns.abort(404, f"Course with code {course_code} not found")

            return course.to_dict(detailed=True)

        except SQLAlchemyError as e:
            db.session.rollback()
            ns.abort(500, f"Database error: {str(e)}")


class EnrollmentsList(Resource):
    """Resource for handling multiple enrollments operations."""
    
    def get(self, ns, models):
        """List enrollments with optional filtering."""
        course_code = request.args.get('course_code')
        student_id = request.args.get('student_id', type=int)
        lecturer_id = request.args.get('lecturer_id', type=int)
        semester = request.args.get('semester')
        year = request.args.get('year', type=int)
        status = request.args.get('status')
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        has_grade = request.args.get('has_grade')
        limit = request.args.get('limit', default=100, type=int)
        offset = request.args.get('offset', default=0, type=int)

        # Validate parameters
        if limit > 1000:
            ns.abort(400, "Limit cannot exceed 1000")
        if limit <= 0:
            ns.abort(400, "Limit must be positive")
        if offset < 0:
            ns.abort(400, "Offset cannot be negative")

        try:
            # Build optimized query with eager loading
            query = db.session.query(Enrollment).options(
                selectinload(Enrollment.offering).selectinload(CourseOffering.course),
                selectinload(Enrollment.offering).selectinload(CourseOffering.lecturer).selectinload(Lecturer.department),
                selectinload(Enrollment.student).selectinload(Student.program),
                selectinload(Enrollment.student).selectinload(Student.advisor)
            )

            # Apply filters
            if course_code:
                query = query.filter(Enrollment.offering.has(CourseOffering.course.has(code=course_code.upper())))
            if student_id:
                query = query.filter(Enrollment.student_id == student_id)
            if lecturer_id:
                query = query.filter(Enrollment.offering.has(lecturer_id=lecturer_id))
            if semester:
                query = query.filter(Enrollment.offering.has(CourseOffering.semester.ilike(f"%{semester}%")))
            if year:
                query = query.filter(Enrollment.offering.has(CourseOffering.year == year))
            if status:
                query = query.filter(Enrollment.status.ilike(f"%{status}%"))

            # Date range filtering
            if from_date:
                try:
                    from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
                    query = query.filter(Enrollment.enrollment_date >= from_date_obj)
                except ValueError:
                    ns.abort(400, "Invalid from_date format. Use YYYY-MM-DD")

            if to_date:
                try:
                    to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
                    query = query.filter(Enrollment.enrollment_date <= to_date_obj)
                except ValueError:
                    ns.abort(400, "Invalid to_date format. Use YYYY-MM-DD")

            if has_grade is not None:
                if has_grade.lower() == 'true':
                    query = query.filter(Enrollment.grade.isnot(None))
                elif has_grade.lower() == 'false':
                    query = query.filter(Enrollment.grade.is_(None))

            enrollments = query.offset(offset).limit(limit).all()

            if not enrollments:
                ns.abort(404, "No enrollments found matching the criteria")

            return [enrollment.to_dict(simplified=True) for enrollment in enrollments]

        except SQLAlchemyError as e:
            db.session.rollback()
            ns.abort(500, f"Database error: {str(e)}")
        except Exception as e:
            ns.abort(500, f"Unexpected error: {str(e)}")


class DepartmentsList(Resource):
    """Resource for handling multiple departments operations."""
    
    def get(self, ns, models):
        """List all departments."""
        try:
            departments = db.session.query(Department).options(
                selectinload(Department.lecturers),
                selectinload(Department.courses),
                selectinload(Department.programs)
            ).all()

            if not departments:
                ns.abort(404, "No departments found")

            return [{
                "department_id": d.department_id,
                "name": d.name,
                "faculty": d.faculty,
                "research_areas": d.research_areas,
                "lecturer_count": len(d.lecturers),
                "course_count": len(d.courses),
                "program_count": len(d.programs)
            } for d in departments]

        except SQLAlchemyError as e:
            db.session.rollback()
            ns.abort(500, f"Database error: {str(e)}")


class DepartmentDetail(Resource):
    """Resource for handling individual department operations."""
    
    def get(self, department_id, ns, models):
        """Get detailed information about a specific department."""
        try:
            department = db.session.query(Department).filter(Department.department_id == department_id).first()

            if not department:
                ns.abort(404, f"Department with ID {department_id} not found")

            return department.to_dict(detailed=True)

        except SQLAlchemyError as e:
            db.session.rollback()
            ns.abort(500, f"Database error: {str(e)}")


class StaffList(Resource):
    """Resource for handling non-academic staff operations."""
    
    def get(self, ns, models):
        """List non-academic staff with optional filtering."""
        department_id = request.args.get('department_id', type=int)
        job_title = request.args.get('job_title')
        employment_type = request.args.get('employment_type')
        limit = request.args.get('limit', default=100, type=int)
        offset = request.args.get('offset', default=0, type=int)

        # Validate parameters
        if limit > 1000:
            ns.abort(400, "Limit cannot exceed 1000")
        if limit <= 0:
            ns.abort(400, "Limit must be positive")
        if offset < 0:
            ns.abort(400, "Offset cannot be negative")

        try:
            # Build optimized query
            query = db.session.query(NonAcademicStaff).options(
                selectinload(NonAcademicStaff.department)
            )

            # Apply filters
            if department_id:
                query = query.filter(NonAcademicStaff.department_id == department_id)
            if job_title:
                query = query.filter(NonAcademicStaff.job_title.ilike(f"%{job_title}%"))
            if employment_type:
                query = query.filter(NonAcademicStaff.employment_type.ilike(f"%{employment_type}%"))

            staff = query.offset(offset).limit(limit).all()

            if not staff:
                ns.abort(404, "No staff found matching the criteria")

            return [s.to_dict() for s in staff]

        except SQLAlchemyError as e:
            db.session.rollback()
            ns.abort(500, f"Database error: {str(e)}")
        except Exception as e:
            ns.abort(500, f"Unexpected error: {str(e)}")
