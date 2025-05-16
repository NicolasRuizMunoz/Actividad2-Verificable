from datetime import date

from flask import Blueprint, redirect, render_template, request, url_for

from app.validators.course_instance import CourseInstanceSchema
from decorators.courses_decorators import validate_with
from http_errors import HTTP_BAD_REQUEST
from services.courses_instances_manager import CourseInstanceManager
from services.courses_manager import CourseManager
from services.evaluations_manager import EvaluationManager
from services.section_manager import SectionManager
from settings import ERROR_PAGE

instances_bp = Blueprint(
    "course_instances",
    __name__,
    url_prefix="/courses/<int:course_id>/instances",
)

course_mgr = CourseManager()
cim = CourseInstanceManager()
section_mgr = SectionManager()
evaluation_mgr = EvaluationManager()


@instances_bp.route("/create", methods=["GET", "POST"])
@validate_with(
    schema=CourseInstanceSchema,
    template="courses_instances/create_instance.html",
    form_key="form",
    error_key="errors",
)
def create_course_instance(
    course_id: int,
    validated: CourseInstanceSchema = None,
):
    course = course_mgr.get_course_by_id(course_id)
    if not course:
        return render_template(ERROR_PAGE, error="Curso no encontrado"), 404

    if request.method == "GET":
        form = {
            "course_id": course_id,
            "semester": "",
            "year": date.today().year,
        }
        return render_template(
            "courses_instances/create_instance.html",
            form=form,
            course=course,
            current_year=date.today().year,
        )

    res = cim.create_course_instance(
        validated.course_id, validated.semester, validated.year
    )
    if res["status"] != "ok":
        return (
            render_template(
                "courses_instances/create_instance.html",
                form=validated.model_dump(),
                course=course,
                error=res["message"],
                current_year=date.today().year,
            ),
            HTTP_BAD_REQUEST,
        )

    return redirect(url_for("courses.course_detail", course_id=course_id))


@instances_bp.route("/<int:instance_id>", methods=["GET"])
def course_instance_detail(course_id: int, instance_id: int):
    course = course_mgr.get_course_by_id(course_id)
    if not course:
        return render_template(ERROR_PAGE, error="Curso no encontrado"), 404

    inst = cim.get_course_instance_by_id(instance_id)
    if not inst or inst["course_id"] != course_id:
        return (
            render_template(
                ERROR_PAGE,
                error="Instancia no encontrada",
            ),
            404,
        )

    sections = section_mgr.get_sections_by_instance_id(instance_id)
    evaluations = evaluation_mgr.get_evaluations_by_instance_id(instance_id)

    return render_template(
        "courses_instances/instance_detail.html",
        course=course,
        instance=inst,
        sections=sections,
        evaluations=evaluations,
    )


@instances_bp.route("/<int:instance_id>/edit", methods=["GET", "POST"])
@validate_with(
    schema=CourseInstanceSchema,
    template="courses_instances/edit_instance.html",
    form_key="form",
    error_key="errors",
)
def edit_course_instance(
    course_id: int, instance_id: int, validated: CourseInstanceSchema = None
):
    course = course_mgr.get_course_by_id(course_id)
    if not course:
        return render_template(ERROR_PAGE, error="Curso no encontrado"), 404

    inst = cim.get_course_instance_by_id(instance_id)
    if not inst or inst["course_id"] != course_id:
        return (
            render_template(
                ERROR_PAGE,
                error="Instancia no encontrada",
            ),
            404,
        )

    if request.method == "GET":
        form = {
            "course_id": course_id,
            "semester": inst["semester"],
            "year": inst["year"],
        }
        return render_template(
            "courses_instances/edit_instance.html",
            form=form,
            course=course,
            instance=inst,
            current_year=date.today().year,
        )

    res = cim.update_course_instance(
        instance_id,
        validated.semester,
        validated.year,
    )
    if res["status"] != "ok":
        return (
            render_template(
                "courses_instances/edit_instance.html",
                form=validated.model_dump(),
                course=course,
                instance=inst,
                error=res["message"],
                current_year=date.today().year,
            ),
            HTTP_BAD_REQUEST,
        )

    return redirect(
        url_for(
            "course_instances.course_instance_detail",
            course_id=course_id,
            instance_id=instance_id,
        )
    )


@instances_bp.route("/<int:instance_id>/delete", methods=["POST"])
def delete_course_instance(course_id: int, instance_id: int):
    res = cim.delete_course_instance(instance_id)
    if res["status"] != "ok":
        return (
            render_template(
                ERROR_PAGE,
                error=res["message"],
            ),
            HTTP_BAD_REQUEST,
        )
    return redirect(url_for("courses.course_detail", course_id=course_id))
