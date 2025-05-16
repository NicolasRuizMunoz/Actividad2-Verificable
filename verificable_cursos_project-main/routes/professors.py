from flask import Blueprint, redirect, render_template, request, url_for

from app.validators.professor import ProfessorSchema
from decorators.courses_decorators import validate_with
from http_errors import HTTP_BAD_REQUEST
from services.professor_manager import ProfessorManager
from settings import (
    ALL_PROFESSORS_PAGE,
    CREATE_PROFESSOR_PAGE,
    DETAIL_PROFESSOR_PAGE,
    EDIT_PROFESSOR_PAGE,
    ERROR_PAGE,
)

professors_bp = Blueprint("professors", __name__, url_prefix="/professors")
mgr = ProfessorManager()


@professors_bp.route("/", methods=["GET"])
def list_professors():
    professors = mgr.get_all_professors()
    return render_template(ALL_PROFESSORS_PAGE, professors=professors)


@professors_bp.route("/create", methods=["GET", "POST"])
@validate_with(
    schema=ProfessorSchema,
    template=CREATE_PROFESSOR_PAGE,
    form_key="form",
    error_key="errors",
)
def create_professor(validated=None): # aca el error documentado
    if request.method == "POST":
        res = mgr.create_professor(name=validated.nombre, email=validated.correo)
        if res["status"] != "ok":
            return (
                render_template(
                    CREATE_PROFESSOR_PAGE,
                    form=validated.model_dump(),
                    error=res["message"],
                ),
                HTTP_BAD_REQUEST,
            )
        return redirect(url_for("professors.list_professors"))
    return render_template(CREATE_PROFESSOR_PAGE, form={"nombre": "", "correo": ""})


@professors_bp.route("/<int:professor_id>", methods=["GET"])
def professor_detail(professor_id):
    professor = mgr.get_professor_by_id(professor_id)
    if not professor:
        return render_template(ERROR_PAGE, error="Profesor no encontrado"), 404
    return render_template(DETAIL_PROFESSOR_PAGE, professor=professor)


@professors_bp.route("/<int:professor_id>/edit", methods=["GET", "POST"])
@validate_with(
    schema=ProfessorSchema,
    template=EDIT_PROFESSOR_PAGE,
    form_key="form",
    error_key="errors",
)
def edit_professor(professor_id, validated=None):
    professor = mgr.get_professor_by_id(professor_id)
    if not professor:
        return render_template(ERROR_PAGE, error="Profesor no encontrado"), 404
    if request.method == "POST":
        res = mgr.update_professor(
            professor_id=professor_id, name=validated.nombre, email=validated.correo
        )
        if res["status"] != "ok":
            return (
                render_template(
                    EDIT_PROFESSOR_PAGE,
                    form=validated.model_dump(),
                    professor=professor,
                    error=res["message"],
                ),
                HTTP_BAD_REQUEST,
            )
        return redirect(
            url_for("professors.professor_detail", professor_id=professor_id)
        )
    form = {
        "nombre": professor["name"],
        "correo": professor["email"],
    }
    return render_template(
        EDIT_PROFESSOR_PAGE, form=form, professor=professor, errors=None, error=None
    )


@professors_bp.route("/<int:professor_id>/delete", methods=["POST"])
def delete_professor(professor_id):
    mgr.delete_professor(professor_id)
    return redirect(url_for("professors.list_professors"))
