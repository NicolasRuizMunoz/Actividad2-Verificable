from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.validators.evaluation_instance import EvaluationInstanceSchema
from decorators.courses_decorators import validate_with
from http_errors import HTTP_BAD_REQUEST
from services.courses_instances_manager import CourseInstanceManager
from services.courses_manager import CourseManager
from services.evaluation_instance_manager import EvaluationInstanceManager
from services.evaluations_manager import EvaluationManager
from services.section_manager import SectionManager
from settings import ERROR_PAGE, STATUS_ERROR

evaluation_instances_bp = Blueprint(
    "evaluation_instances",
    __name__,
    url_prefix="/courses/<int:course_id>/instances/<int:instance_id>/sections/<int:section_id>/evaluations/<int:evaluation_id>/instances",
)

eval_mgr = EvaluationManager()
inst_mgr = EvaluationInstanceManager()
ci_mgr = CourseInstanceManager()
course_mgr = CourseManager()
section_mgr = SectionManager()


@evaluation_instances_bp.route("/create", methods=["GET", "POST"])
@validate_with(
    schema=EvaluationInstanceSchema,
    template="evaluations_instances/create_evaluation_instance.html",
    form_key="form",
    error_key="errors",
)
def create_evaluation_instance( # aca el error documentado
    course_id: int,
    instance_id: int,
    section_id: int,
    evaluation_id: int,
    validated: EvaluationInstanceSchema = None,
):
    course = course_mgr.get_course_by_id(course_id)
    if not course:
        return (
            render_template(ERROR_PAGE, error="Curso no encontrado"),
            HTTP_BAD_REQUEST,
        )

    if course.get("closed"):
        flash(
            "No se pueden agregar instancias de evaluación en un curso cerrado",
            "danger",
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

    evaluation = eval_mgr.get_evaluation_by_id(evaluation_id)
    if not evaluation:
        return (
            render_template(
                ERROR_PAGE,
                error="Evaluación no encontrada",
            ),
            404,
        )
    inst = ci_mgr.get_course_instance_by_id(instance_id)
    section = section_mgr.get_section_by_id(section_id)
    if request.method == "GET":
        form = {
            "evaluation_id": evaluation_id,
            "name": "",
            "weight": "",
            "is_optional": False,
        }
        return render_template(
            "evaluations_instances/create_evaluation_instance.html",
            form=form,
            course=course,
            instance=inst,
            section=section,
            evaluation=evaluation,
        )
    res = inst_mgr.create_instance(
        validated.evaluation_id,
        validated.name,
        validated.weight_type,
        validated.weight,
        validated.is_optional,
    )
    if res["status"] != "ok":
        return (
            render_template(
                "evaluations_instances/create_evaluation_instance.html",
                form=validated.model_dump(),
                course=course,
                instance=inst,
                section=section,
                evaluation=evaluation,
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


@evaluation_instances_bp.route(
    "/<int:instance_ev_id>/edit",
    methods=["GET", "POST"],
)
@validate_with(
    schema=EvaluationInstanceSchema,
    template="evaluations_instances/edit_evaluation_instance.html",
    form_key="form",
    error_key="errors",
)
def edit_evaluation_instance(
    course_id: int,
    instance_id: int,
    section_id: int,
    evaluation_id: int,
    instance_ev_id: int,
    validated: EvaluationInstanceSchema = None,
):
    evaluation = eval_mgr.get_evaluation_by_id(evaluation_id)
    if not evaluation:
        return (
            render_template(
                ERROR_PAGE,
                error="Evaluación no encontrada",
            ),
            404,
        )

    inst_ev = inst_mgr.get_instance_by_id(instance_ev_id)
    if not inst_ev or inst_ev["evaluation_id"] != evaluation_id:
        return (
            render_template(
                ERROR_PAGE,
                error="Instancia no encontrada",
            ),
            404,
        )

    course_instance = ci_mgr.get_course_instance_by_id(instance_id)
    course = course_mgr.get_course_by_id(course_id)
    section = section_mgr.get_section_by_id(section_id)

    if request.method == "GET":
        form = {
            "evaluation_id": evaluation_id,
            "name": inst_ev["name"],
            "weight_type": inst_ev["weight_type"],
            "weight": inst_ev["weight"],
            "is_optional": inst_ev["is_optional"],
        }
        return render_template(
            "evaluations_instances/edit_evaluation_instance.html",
            form=form,
            course=course,
            course_instance=course_instance,
            instance=inst_ev,
            section=section,
            evaluation=evaluation,
        )

    res = inst_mgr.update_instance(
        instance_ev_id,
        validated.name,
        validated.weight_type,
        validated.weight,
        validated.is_optional,
    )
    if res["status"] != "ok":
        return (
            render_template(
                "evaluations_instances/edit_evaluation_instance.html",
                form=validated.model_dump(),
                course=course,
                course_instance=course_instance,
                instance=inst_ev,
                section=section,
                evaluation=evaluation,
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


@evaluation_instances_bp.route(
    "/<int:instance_ev_id>/delete",
    methods=["POST"],
)
def delete_evaluation_instance(
    course_id: int,
    instance_id: int,
    section_id: int,
    evaluation_id: int,
    instance_ev_id: int,
):
    inst_ev = inst_mgr.get_instance_by_id(instance_ev_id)
    if not inst_ev or inst_ev["evaluation_id"] != evaluation_id:
        return (
            render_template(
                ERROR_PAGE,
                error="Instancia no encontrada",
            ),
            404,
        )
    res = inst_mgr.delete_instance(instance_ev_id)
    if res["status"] == STATUS_ERROR:
        return (
            render_template(
                ERROR_PAGE,
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
