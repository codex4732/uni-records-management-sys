from app import create_app
from app.utils.database import init_db

app = create_app()

if __name__ == '__main__':
    init_db(app)  # Pass app instance to init_db
    app.run(debug=True)
