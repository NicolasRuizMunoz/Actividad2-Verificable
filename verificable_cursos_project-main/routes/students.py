from flask import Blueprint, redirect, render_template, request, url_for

from app.validators.student import StudentSchema
from decorators.courses_decorators import validate_with
from http_errors import HTTP_BAD_REQUEST
from services.student_manager import StudentManager
from settings import (
    ALL_STUDENTS_PAGE,
    CREATE_STUDENT_PAGE,
    DETAIL_STUDENT_PAGE,
    EDIT_STUDENT_PAGE,
    ERROR_PAGE,
    MAX_DATE,
    MIN_DATE,
)

students_bp = Blueprint("students", __name__, url_prefix="/students")
mgr = StudentManager()


@students_bp.route("/", methods=["GET"])
def list_students():
    students = mgr.get_all_students()
    return render_template(ALL_STUDENTS_PAGE, students=students)


@students_bp.route("/create", methods=["GET", "POST"])
@validate_with(schema=StudentSchema, template=CREATE_STUDENT_PAGE)
def create_student(validated=None): # aca el error documentado
    if request.method == "POST":
        res = mgr.create_student(
            name=validated.nombre,
            email=validated.correo,
            enrollment_date=validated.anio_ingreso,
        )
        if res["status"] != "ok":
            return (
                render_template(
                    CREATE_STUDENT_PAGE,
                    form={
                        "nombre": validated.nombre,
                        "correo": validated.correo,
                        "anio_ingreso": validated.anio_ingreso.year,
                    },
                    error=res["message"],
                    min_year=MIN_DATE.year,
                    max_year=MAX_DATE.year,
                ),
                HTTP_BAD_REQUEST,
            )
        return redirect(url_for("students.list_students"))

    form = {"nombre": "", "correo": "", "anio_ingreso": MAX_DATE.year}
    return render_template(
        CREATE_STUDENT_PAGE,
        form=form,
        min_year=MIN_DATE.year,
        max_year=MAX_DATE.year,
        errors=None,
        error=None,
    )


@students_bp.route("/<int:student_id>", methods=["GET"])
def student_detail(student_id):
    student = mgr.get_student_by_id(student_id)
    if not student:
        return render_template(ERROR_PAGE, error="Estudiante no encontrado"), 404
    return render_template(DETAIL_STUDENT_PAGE, student=student)


@students_bp.route("/<int:student_id>/edit", methods=["GET", "POST"])
@validate_with(schema=StudentSchema, template=EDIT_STUDENT_PAGE)
def edit_student(student_id, validated=None):
    student = mgr.get_student_by_id(student_id)
    if not student:
        return render_template(ERROR_PAGE, error="Estudiante no encontrado"), 404

    if request.method == "POST":
        res = mgr.update_student(
            student_id=student_id,
            name=validated.nombre,
            email=validated.correo,
            enrollment_date=validated.anio_ingreso,
        )
        if res["status"] != "ok":
            return (
                render_template(
                    EDIT_STUDENT_PAGE,
                    form={
                        "nombre": validated.nombre,
                        "correo": validated.correo,
                        "anio_ingreso": validated.anio_ingreso.year,
                    },
                    student=student,
                    error=res["message"],
                    min_year=MIN_DATE.year,
                    max_year=MAX_DATE.year,
                ),
                HTTP_BAD_REQUEST,
            )
        return redirect(url_for("students.student_detail", student_id=student_id))

    form = {
        "nombre": student["name"],
        "correo": student["email"],
        "anio_ingreso": student["enrollment_date"].year,
    }
    return render_template(
        EDIT_STUDENT_PAGE,
        form=form,
        student=student,
        min_year=MIN_DATE.year,
        max_year=MAX_DATE.year,
        errors=None,
        error=None,
    )


@students_bp.route("/<int:student_id>/delete", methods=["POST"])
def delete_student(student_id):
    mgr.delete_student(student_id)
    return redirect(url_for("students.list_students"))
