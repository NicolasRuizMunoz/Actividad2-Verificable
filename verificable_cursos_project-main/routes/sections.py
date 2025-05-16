from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.validators.section import SectionSchema
from decorators.courses_decorators import validate_with
from http_errors import HTTP_BAD_REQUEST
from services.courses_instances_manager import CourseInstanceManager
from services.courses_manager import CourseManager
from services.professor_manager import ProfessorManager
from services.section_manager import SectionManager
from services.student_manager import StudentManager
from settings import ERROR_PAGE, STATUS_ERROR

sections_bp = Blueprint(
    "sections",
    __name__,
    url_prefix="/courses/<int:course_id>/instances/<int:instance_id>/sections",
)

course_mgr = CourseManager()
instance_mgr = CourseInstanceManager()
section_mgr = SectionManager()
professor_mrg = ProfessorManager()
student_mrg = StudentManager()


@sections_bp.route("/create", methods=["GET", "POST"])
@validate_with(
    schema=SectionSchema,
    template="sections/create_section.html",
    form_key="form",
    error_key="errors",
)
def create_section(course_id: int, instance_id: int, validated: SectionSchema = None):
    course = course_mgr.get_course_by_id(course_id)
    if not course:
        return (
            render_template(ERROR_PAGE, error="Curso no encontrado"),
            HTTP_BAD_REQUEST,
        )

    if course.get("closed"):
        flash("No se pueden crear secciones en un curso cerrado", "danger")
        return redirect(
            url_for(
                "course_instances.course_instance_detail",
                course_id=course_id,
                instance_id=instance_id,
            )
        )

    instance = instance_mgr.get_course_instance_by_id(instance_id)
    if not instance or instance["course_id"] != course_id:
        return (
            render_template(ERROR_PAGE, error="Instancia no encontrada"),
            HTTP_BAD_REQUEST,
        )

    if request.method == "GET":
        form = {
            "course_instance_id": instance_id,
            "section_number": "",
            "evaluation_scheme": "percentage",
        }
        return render_template(
            "sections/create_section.html", form=form, course=course, instance=instance
        )

    res = section_mgr.create_section(
        validated.course_instance_id,
        validated.section_number,
        validated.evaluation_scheme,
    )
    if res["status"] != "ok":
        return (
            render_template(
                "sections/create_section.html",
                form=validated.model_dump(),
                course=course,
                instance=instance,
                error=res["message"],
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


@sections_bp.route("/<int:section_id>", methods=["GET"])
def detail_section(course_id: int, instance_id: int, section_id: int):
    course = course_mgr.get_course_by_id(course_id)
    if not course:
        return render_template(ERROR_PAGE, error="Curso no encontrado"), 404

    inst = instance_mgr.get_course_instance_by_id(instance_id)
    if not inst or inst["course_id"] != course_id:
        return render_template(ERROR_PAGE, error="Instancia no encontrada"), 404

    section = section_mgr.get_section_by_id(section_id)
    if not section or section["course_instance_id"] != instance_id:
        return render_template(ERROR_PAGE, error="Sección no encontrada"), 404

    professors = section_mgr.get_professors_by_section(section_id)
    students = section_mgr.get_students_by_section(section_id)
    evaluations = section_mgr.get_evaluations_by_section(section_id, instance_id)
    total_people = len(professors) + len(students)

    return render_template(
        "sections/section_detail.html",
        course=course,
        instance=inst,
        section=section,
        professors=professors,
        students=students,
        evaluations=evaluations,
        total_people=total_people,
    )


@sections_bp.route("/<int:section_id>/edit", methods=["GET", "POST"])
@validate_with(
    schema=SectionSchema,
    template="sections/edit_section.html",
    form_key="form",
    error_key="errors",
)
def edit_section(
    course_id: int, instance_id: int, section_id: int, validated: SectionSchema = None
):
    course = course_mgr.get_course_by_id(course_id)
    if not course:
        return render_template(ERROR_PAGE, error="Curso no encontrado"), 404

    if course.get("closed"):
        flash("No se puede editar una sección en un curso cerrado", "danger")
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
            "course_instance_id": instance_id,
            "section_number": section["section_number"],
        }
        return render_template(
            "sections/edit_section.html",
            form=form,
            course=course,
            instance=inst,
            section=section,
        )

    res = section_mgr.update_section(
        section_id,
        validated.course_instance_id,
        validated.section_number,
        validated.evaluation_scheme,
    )
    if res["status"] != "ok":
        return (
            render_template(
                "sections/edit_section.html",
                form=validated.model_dump(),
                course=course,
                instance=inst,
                section=section,
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


@sections_bp.route("/<int:section_id>/delete", methods=["POST"])
def delete_section(course_id: int, instance_id: int, section_id: int):
    res = section_mgr.delete_section(section_id)
    print(res)
    if res["status"] != "ok":
        return render_template(ERROR_PAGE, error=res["message"]), HTTP_BAD_REQUEST

    return redirect(
        url_for(
            "course_instances.course_instance_detail",
            course_id=course_id,
            instance_id=instance_id,
        )
    )


@sections_bp.route("/<int:section_id>/assign-professor", methods=["GET", "POST"])
def assign_professor(course_id: int, instance_id: int, section_id: int): # aca el error documentado
    course = course_mgr.get_course_by_id(course_id)
    if not course:
        return (
            render_template(ERROR_PAGE, error="Curso no encontrado"),
            HTTP_BAD_REQUEST,
        )

    instance = instance_mgr.get_course_instance_by_id(instance_id)
    if not instance:
        return (
            render_template(ERROR_PAGE, error="Instancia no encontrada"),
            HTTP_BAD_REQUEST,
        )

    section = section_mgr.get_section_by_id(section_id)
    if not section:
        return (
            render_template(ERROR_PAGE, error="Sección no encontrada"),
            HTTP_BAD_REQUEST,
        )

    if course.get("closed"):
        flash("No se pueden asignar profesores en un curso cerrado", "danger")
        return redirect(
            url_for(
                "sections.detail_section",
                course_id=course_id,
                instance_id=instance_id,
                section_id=section_id,
            )
        )

    if request.method == "POST":
        pid = request.form.get("professor_id", "").strip()
        if not pid:
            return (
                render_template(
                    "courses/assign_professor.html",
                    professors=professor_mrg.get_all_professors(),
                    course=course,
                    instance=instance,
                    section=section,
                    error="ID de profesor obligatorio.",
                ),
                HTTP_BAD_REQUEST,
            )

        res = section_mgr.assign_professor_to_section(section_id, int(pid))
        if res["status"] == STATUS_ERROR:
            return (
                render_template(
                    "courses/assign_professor.html",
                    professors=professor_mrg.get_all_professors(),
                    course=course,
                    instance=instance,
                    section=section,
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

    return render_template(
        "courses/assign_professor.html",
        professors=professor_mrg.get_all_professors(),
        course=course,
        instance=instance,
        section=section,
    )


@sections_bp.route("/<int:section_id>/assign_student", methods=["GET", "POST"])
def assign_student(course_id: int, instance_id: int, section_id: int): # aca el error documentado
    course = course_mgr.get_course_by_id(course_id)
    if not course:
        return (
            render_template(ERROR_PAGE, error="Curso no encontrado"),
            HTTP_BAD_REQUEST,
        )

    instance = instance_mgr.get_course_instance_by_id(instance_id)
    if not instance:
        return (
            render_template(ERROR_PAGE, error="Instancia no encontrada"),
            HTTP_BAD_REQUEST,
        )

    section = section_mgr.get_section_by_id(section_id)
    if not section:
        return (
            render_template(ERROR_PAGE, error="Sección no encontrada"),
            HTTP_BAD_REQUEST,
        )

    if course.get("closed"):
        flash("No se pueden asignar estudiantes en un curso cerrado", "danger")
        return redirect(
            url_for(
                "sections.detail_section",
                course_id=course_id,
                instance_id=instance_id,
                section_id=section_id,
            )
        )

    if request.method == "POST":
        sid = request.form.get("student_id", "").strip()
        if not sid:
            return (
                render_template(
                    "courses/assign_student.html",
                    students=student_mrg.get_all_students(),
                    course=course,
                    instance=instance,
                    section=section,
                    error="ID de estudiante obligatorio.",
                ),
                HTTP_BAD_REQUEST,
            )

        res = section_mgr.assign_student_to_section(section_id, int(sid))
        if res["status"] == STATUS_ERROR:
            return (
                render_template(
                    "courses/assign_student.html",
                    students=student_mrg.get_all_students(),
                    course=course,
                    instance=instance,
                    section=section,
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

    return render_template(
        "courses/assign_student.html",
        students=student_mrg.get_all_students(),
        course=course,
        instance=instance,
        section=section,
    )
