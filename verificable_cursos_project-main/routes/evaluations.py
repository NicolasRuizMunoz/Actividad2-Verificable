from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.validators.evaluation import EvaluationSchema
from decorators.courses_decorators import validate_with
from http_errors import HTTP_BAD_REQUEST
from services.courses_instances_manager import CourseInstanceManager
from services.courses_manager import CourseManager
from services.evaluation_instance_manager import EvaluationInstanceManager
from services.evaluations_manager import EvaluationManager
from services.section_manager import SectionManager
from settings import ERROR_PAGE

evaluations_bp = Blueprint(
    "evaluations",
    __name__,
    url_prefix="/courses/<int:course_id>/instances/<int:instance_id>/sections/<int:section_id>/evaluations",
)

course_mgr = CourseManager()
instance_mgr = CourseInstanceManager()
section_mgr = SectionManager()
eval_mgr = EvaluationManager()
inst_mgr = EvaluationInstanceManager()


@evaluations_bp.route("/", methods=["GET"])
def list_evaluations(course_id: int, instance_id: int, section_id: int):
    course = course_mgr.get_course_by_id(course_id)
    if not course:
        return render_template(ERROR_PAGE, error="Curso no encontrado"), 404

    inst = instance_mgr.get_course_instance_by_id(instance_id)
    if not inst or inst["course_id"] != course_id:
        return render_template(ERROR_PAGE, error="Instancia no encontrada"), 404

    sections = section_mgr.get_sections_by_instance_id(instance_id)
    if not any(s["id"] == section_id for s in sections):
        return render_template(ERROR_PAGE, error="Sección no encontrada"), 404

    evaluations = eval_mgr.get_evaluations_by_instance_id(instance_id, section_id)
    return render_template(
        "courses/evaluations/list.html",
        course=course,
        instance=inst,
        section_id=section_id,
        evaluations=evaluations,
    )


@evaluations_bp.route("/create", methods=["GET", "POST"])
@validate_with(
    schema=EvaluationSchema,
    template="evaluations/create_evaluation.html",
    form_key="form",
    error_key="errors",
)
def create_evaluation( # aca el error documentado
    course_id: int,
    instance_id: int,
    section_id: int,
    validated: EvaluationSchema = None,
):
    course = course_mgr.get_course_by_id(course_id)
    if not course:
        return (
            render_template(ERROR_PAGE, error="Curso no encontrado"),
            HTTP_BAD_REQUEST,
        )

    if course.get("closed"):
        flash("No se pueden crear evaluaciones en un curso cerrado", "danger")
        return redirect(
            url_for(
                "sections.detail_section",
                course_id=course_id,
                instance_id=instance_id,
                section_id=section_id,
            )
        )

    inst = instance_mgr.get_course_instance_by_id(instance_id)
    if not inst or inst["course_id"] != course_id:
        return render_template(ERROR_PAGE, error="Instancia no encontrada"), 404

    section = section_mgr.get_section_by_id(section_id)
    if not section or section["course_instance_id"] != instance_id:
        return render_template(ERROR_PAGE, error="Sección no encontrada"), 404

    if request.method == "GET":
        form = {
            "section_id": section_id,
            "name": "",
            "weight_type": section["evaluation_scheme"],
            "weight": "",
        }
        return render_template(
            "evaluations/create_evaluation.html",
            form=form,
            course=course,
            instance=inst,
            section=section,
            section_id=section_id,
        )

    res = eval_mgr.create_evaluation(
        instance_id, section_id, validated.name, validated.weight
    )
    if res["status"] != "ok":
        return (
            render_template(
                "evaluations/create_evaluation.html",
                form=validated.model_dump(),
                course=course,
                instance=inst,
                section=section,
                section_id=section_id,
                error=res["message"],
            ),
            HTTP_BAD_REQUEST,
        )

    return redirect(
        url_for(
            "sections.detail_section",
            course_id=course_id,
            instance_id=instance_id,
            section_id=section_id,
        )
    )


@evaluations_bp.route("/<int:evaluation_id>", methods=["GET"])
def detail_evaluation(
    course_id: int, instance_id: int, section_id: int, evaluation_id: int
):
    course = course_mgr.get_course_by_id(course_id)
    if not course:
        return render_template(ERROR_PAGE, error="Curso no encontrado"), 404

    inst = instance_mgr.get_course_instance_by_id(instance_id)
    if not inst or inst["course_id"] != course_id:
        return render_template(ERROR_PAGE, error="Instancia no encontrada"), 404

    evaluation = eval_mgr.get_evaluation_by_id(evaluation_id)
    if not evaluation or evaluation["section_id"] != section_id:
        return render_template(ERROR_PAGE, error="Evaluación no encontrada"), 404

    instances = inst_mgr.get_instances_by_evaluation_id(evaluation_id)

    return render_template(
        "evaluations/evaluation_detail.html",
        course=course,
        instance=inst,
        section_id=section_id,
        evaluation=evaluation,
        instances=instances,
        edit_mode=False,
        errors=None,
        error=None,
    )


@evaluations_bp.route("/<int:evaluation_id>/edit", methods=["GET", "POST"])
@validate_with(
    schema=EvaluationSchema,
    template="evaluations/edit_evaluation.html",
    form_key="form",
    error_key="errors",
)
def edit_evaluation(
    course_id: int,
    instance_id: int,
    section_id: int,
    evaluation_id: int,
    validated: EvaluationSchema = None,
):
    course = course_mgr.get_course_by_id(course_id)
    if not course:
        return (
            render_template(ERROR_PAGE, error="Curso no encontrado"),
            HTTP_BAD_REQUEST,
        )

    if course.get("closed"):
        flash("No se puede editar una evaluación en un curso cerrado", "danger")
        return redirect(
            url_for(
                "evaluations.detail_evaluation",
                course_id=course_id,
                instance_id=instance_id,
                section_id=section_id,
                evaluation_id=evaluation_id,
            )
        )

    inst = instance_mgr.get_course_instance_by_id(instance_id)
    if not inst or inst["course_id"] != course_id:
        return render_template(ERROR_PAGE, error="Instancia no encontrada"), 404

    evaluation = eval_mgr.get_evaluation_by_id(evaluation_id)
    if not evaluation or evaluation["section_id"] != section_id:
        return render_template(ERROR_PAGE, error="Evaluación no encontrada"), 404

    if request.method == "GET":
        form = {
            "section_id": section_id,
            "name": evaluation["name"],
            "weight": evaluation["weight"],
        }
        return render_template(
            "evaluations/edit_evaluation.html",
            form=form,
            course=course,
            instance=inst,
            evaluation=evaluation,
            section_id=section_id,
        )

    res = eval_mgr.update_evaluation(evaluation_id, validated.name, validated.weight)
    if res["status"] != "ok":
        return (
            render_template(
                "evaluations/edit_evaluation.html",
                form=validated.model_dump(),
                course=course,
                instance=inst,
                evaluation=evaluation,
                section_id=section_id,
                error=res["message"],
            ),
            HTTP_BAD_REQUEST,
        )

    return redirect(
        url_for(
            "evaluations.detail_evaluation",
            course_id=course_id,
            instance_id=instance_id,
            section_id=section_id,
            evaluation_id=evaluation_id,
        )
    )


@evaluations_bp.route("/<int:evaluation_id>/delete", methods=["POST"])
def delete_evaluation(
    course_id: int, instance_id: int, section_id: int, evaluation_id: int
):
    res = eval_mgr.delete_evaluation(evaluation_id)
    if res["status"] == "ERROR":
        return render_template(ERROR_PAGE, error=res["message"]), HTTP_BAD_REQUEST
    return redirect(
        url_for(
            "sections.detail_section",
            course_id=course_id,
            instance_id=instance_id,
            section_id=section_id,
        )
    )
