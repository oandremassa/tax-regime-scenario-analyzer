import os
from pathlib import Path
from flask import Flask

from .db import init_db
from .routes import bp
from .seed import seed_demo_data


def create_app(test_config=None):
    app = Flask(__name__)
    base_dir = Path(__file__).resolve().parent.parent

    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-key"),
        DATABASE_PATH=os.getenv("DATABASE_PATH", str(base_dir / "data" / "app.db")),
        MAX_CONTENT_LENGTH=2 * 1024 * 1024,
    )

    if test_config:
        app.config.update(test_config)

    Path(app.config["DATABASE_PATH"]).parent.mkdir(parents=True, exist_ok=True)
    init_db(app.config["DATABASE_PATH"])
    seed_demo_data(app.config["DATABASE_PATH"])
    app.register_blueprint(bp)

    return app
