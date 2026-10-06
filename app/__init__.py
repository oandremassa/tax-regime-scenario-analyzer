import os
from pathlib import Path
from flask import Flask
from .db import init_app as init_db_app, init_db
from .routes import bp
from .seed import seed_demo_data


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    default_db = Path(app.instance_path) / "tax_strategy.db"
    upload_folder = Path(os.getenv("UPLOAD_FOLDER", Path(app.root_path).parent / "uploads"))

    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "change-me-in-production"),
        DATABASE=os.getenv("DATABASE_PATH", str(default_db)),
        UPLOAD_FOLDER=str(upload_folder),
        MAX_CONTENT_LENGTH=12 * 1024 * 1024,
    )
    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    init_db_app(app)
    app.register_blueprint(bp)

    with app.app_context():
        init_db()
        seed_demo_data()

    return app
