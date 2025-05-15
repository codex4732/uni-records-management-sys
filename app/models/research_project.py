from app.utils.database import db

class ResearchProject(db.Model):
    __tablename__ = 'research_projects'

    project_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    funding_sources = db.Column(db.String(250))
    publications = db.Column(db.Text)
    outcomes = db.Column(db.String(250))

    # Relationships
    principal_investigator_id = db.Column(db.Integer, db.ForeignKey('lecturers.lecturer_id'))
    principal_investigator = db.relationship('Lecturer', back_populates='research_group')
    team_members = db.relationship('Lecturer', secondary='project_team_members', back_populates='projects')

    def __repr__(self):
        return f"<ResearchProject {self.project_id} - {self.title}>"
