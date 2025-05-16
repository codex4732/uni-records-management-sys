from flask import Flask, request

from .config import config
from .utils.database import db
from .routes import api_bp
from .utils.validation import validate_id

def create_app(config_name='development'):
    """Application factory function"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api')

    # Register before_request handler
    @app.before_request
    def validate_ids():
        # request.view_args may be None if route doesn't have parameters
        if request.view_args:
            ids = [v for k, v in request.view_args.items() if 'id' in k]
            if ids:
                validate_id(*ids)
    
    return app
