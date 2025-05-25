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
    principal_investigator = db.relationship('Lecturer', back_populates='research_projects')
    team_members = db.relationship('Lecturer', secondary='project_team_members', back_populates='research_group')

    @property
    def team_size(self):
        """Get team size efficiently"""
        if hasattr(self, '_precomputed_team_size'):
            return self._precomputed_team_size
        return len(self.team_members)
    
    @property
    def outcome_list(self):
        """Parse outcomes into list"""
        if hasattr(self, '_precomputed_outcomes'):
            return self._precomputed_outcomes
        return self.outcomes.split(';') if self.outcomes else []

    def to_dict(self):
        return {
            "project_id": self.project_id,
            "title": self.title,
            "principal_investigator": self.principal_investigator.name if self.principal_investigator else None,
            "team_size": self.team_size,
            "outcomes": self.outcome_list
        }

    def __repr__(self):
        return f"<ResearchProject {self.project_id}: {self.title}>"
