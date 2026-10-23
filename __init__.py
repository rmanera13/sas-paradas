import os
from flask import Flask, render_template


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev"),
        DATABASE=os.environ.get("DATABASE_URL", os.path.join(app.root_path, "..", "sas.sqlite")),
    )
    if test_config:
        app.config.update(test_config)

    from . import db, api
    db.init_app(app)
    app.register_blueprint(api.bp)

    # Cria tabelas + carga inicial automaticamente (necessario no plano free do Render)
    with app.app_context():
        db.ensure_db()

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/dashboard")
    def dashboard():
        return render_template("dashboard.html")

    return app
