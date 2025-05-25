# Association tables
from sqlalchemy import func
from app.utils.database import db


project_team_members = db.Table('project_team_members',
                                db.Column('lecturer_id', db.Integer, db.ForeignKey('lecturers.lecturer_id'),
                                          primary_key=True),
                                db.Column('project_id', db.Integer, db.ForeignKey('research_projects.project_id'),
                                          primary_key=True)
                                )
