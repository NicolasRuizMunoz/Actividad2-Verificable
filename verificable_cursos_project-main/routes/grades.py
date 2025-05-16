from flask import Blueprint, flash, redirect, render_template, request, url_for

from services.courses_instances_manager import CourseInstanceManager
from services.courses_manager import CourseManager
from services.evaluation_instance_manager import EvaluationInstanceManager
from services.evaluations_manager import EvaluationManager
from services.grade_manager import GradeManager
from services.section_manager import SectionManager

grades_bp = Blueprint(
    "grades",
    __name__,
    url_prefix="/courses/<int:course_id>/instances/<int:instance_id>/sections/<int:section_id>/evaluations/<int:evaluation_id>/grades",
)

course_mgr = CourseManager()
instance_mgr = CourseInstanceManager()
section_mgr = SectionManager()
evaluation_mgr = EvaluationManager()
eval_inst_mgr = EvaluationInstanceManager()
grade_mgr = GradeManager()


@grades_bp.route("", methods=["GET", "POST"])
def section_enter_grades( # aca el error documentado
    course_id: int, instance_id: int, section_id: int, evaluation_id: int
):
    course = course_mgr.get_course_by_id(course_id)
    inst = instance_mgr.get_course_instance_by_id(instance_id)
    section = section_mgr.get_section_by_id(section_id)
    evaluation = evaluation_mgr.get_evaluation_by_id(evaluation_id)
    instances = eval_inst_mgr.get_instances_by_evaluation_id(evaluation_id)

    students = section_mgr.get_students_by_section(section_id)
    instance_ids = [i["id"] for i in instances]
    grades = grade_mgr.get_grades_for_instances(instance_ids)

    if request.method == "POST":
        if course.get("closed"):
            flash("No se pueden modificar las notas de un curso cerrado", "danger")
            return redirect(
                url_for(
                    "grades.section_enter_grades",
                    course_id=course_id,
                    instance_id=instance_id,
                    section_id=section_id,
                    evaluation_id=evaluation_id,
                )
            )

        for key, value in request.form.items():
            if not value.strip():
                continue
            _, inst_id, stud_id = key.split("_")
            grade_mgr.save_grade(int(stud_id), int(inst_id), float(value))
        return redirect(
            url_for(
                "grades.section_enter_grades",
                course_id=course_id,
                instance_id=instance_id,
                section_id=section_id,
                evaluation_id=evaluation_id,
            )
        )

    return render_template(
        "sections/section_enter_grades.html",
        course=course,
        instance=inst,
        section=section,
        evaluation=evaluation,
        instances=instances,
        students=students,
        grades=grades,
    )
