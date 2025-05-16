import os
from pathlib import Path

from flask import (
    Blueprint,
    current_app,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

from db import DatabaseConnection
from populate_db import PopulateDB
from services.scheduling_manager import SchedulingManager
from settings import HOME_PAGE

home_bp = Blueprint("home", __name__)


@home_bp.route("/", methods=["GET"])
def index_professor():
    db = DatabaseConnection()
    cur = db.connect()
    cur.execute("SELECT COUNT(*) as count FROM classroom_schedule")
    result = cur.fetchone()
    schedule_empty = result["count"] == 0
    return render_template(HOME_PAGE, schedule_empty=schedule_empty)


@home_bp.route("/create_schedule", methods=["POST"])
def create_schedule(): # Aca el error documentado
    try:
        scheduler = SchedulingManager()
        scheduler.clear_schedule()

        if not scheduler.generate_schedule():
            flash(
                "Error al generar el horario: No se pudieron programar todas las secciones",
                "danger",
            )
            return redirect(url_for("home.index_professor"))

        excel_path = os.path.join(current_app.root_path, "static", "schedule.xlsx")
        os.makedirs(os.path.dirname(excel_path), exist_ok=True)
        scheduler.export_to_excel(excel_path)

        if not os.path.exists(excel_path):
            flash("Error: No se pudo generar el archivo Excel", "danger")
            return redirect(url_for("home.index_professor"))

        scheduler.db.commit()
        flash("Horario creado exitosamente", "success")
        return redirect(url_for("home.index_professor"))

    except Exception as e:
        flash(f"Error al crear el horario: {str(e)}", "danger")
        return redirect(url_for("home.index_professor"))


@home_bp.route("/download_schedule")
def download_schedule():
    try:
        excel_path = os.path.join(current_app.root_path, "static", "schedule.xlsx")
        if not os.path.exists(excel_path):
            flash("Error: Archivo no encontrado", "danger")
            return redirect(url_for("home.index_professor"))

        response = make_response(
            send_file(
                excel_path,
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                as_attachment=True,
                download_name="horario.xlsx",
            )
        )
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    except Exception as e:
        flash(f"Error al descargar el archivo: {str(e)}", "danger")
        return redirect(url_for("home.index_professor"))


@home_bp.route("/upload_json", methods=["POST"])
def upload_json():
    data_dir = Path(current_app.root_path) / "data"
    data_dir.mkdir(exist_ok=True)
    for f in request.files.getlist("json_files"):
        f.save(data_dir / f.filename)
    flash("JSONs subidos correctamente", "success")
    return redirect(url_for("home.index_professor"))


@home_bp.route("/run_populate", methods=["POST"])
def run_populate():
    try:
        PopulateDB().run()
        flash("Carga masiva completada exitosamente", "success")
    except Exception as e:
        flash(f"Error en carga masiva: {e}", "danger")
    return redirect(url_for("home.index_professor"))
