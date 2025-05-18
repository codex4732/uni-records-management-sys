from flask import Flask, request
from flask_migrate import Migrate
from flask_restx import Api

from .config import config
from .utils.database import db
from .routes.api import ns as api_namespace
from .utils.validation import validate_id

def create_app(config_name='development'):
    """Application factory function"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    
    # Initialize Flask-Migrate
    migrate = Migrate(app, db)

    # Configure Flask-RESTx
    api = Api(
        app,
        version='1.0',
        title='University Record Management System API',
        description='API documentation for URMS',
        doc='/api/docs'
    )
    
    # Add namespaces
    api.add_namespace(api_namespace)

    # Register middleware
    @app.before_request
    def validate_ids():
        if request.view_args:
            ids = [v for k, v in request.view_args.items() if 'id' in k]
            if ids:
                validate_id(*ids)
    
    return app
