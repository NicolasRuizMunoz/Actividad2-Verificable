import os

from flask import Flask

from routes.courses import courses_bp
from routes.courses_instances import instances_bp
from routes.evaluation_instances import evaluation_instances_bp
from routes.evaluations import evaluations_bp
from routes.grades import grades_bp
from routes.home import home_bp
from routes.professors import professors_bp
from routes.sections import sections_bp
from routes.students import students_bp


def scheme_es(value: str) -> str:
    return "Porcentaje" if value == "percentage" else "Peso"


def unit(value: str) -> str:
    return "%" if value == "percentage" else "pts"


app = Flask(__name__)
app.add_template_filter(scheme_es, "scheme_es")
app.add_template_filter(unit, "unit")
app.register_blueprint(home_bp)
app.register_blueprint(students_bp)
app.register_blueprint(professors_bp)
app.register_blueprint(courses_bp)
app.register_blueprint(instances_bp)
app.register_blueprint(evaluations_bp)
app.register_blueprint(sections_bp)
app.register_blueprint(evaluation_instances_bp)
app.register_blueprint(grades_bp)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")

if __name__ == "__main__":
    app.run(debug=True)
