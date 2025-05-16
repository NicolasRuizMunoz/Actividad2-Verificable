from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from app.validators.course import CourseSchema
from decorators.courses_decorators import validate_with
from http_errors import HTTP_BAD_REQUEST
from services.courses_manager import CourseManager
from settings import (
    ALL_COURSES_PAGE,
    CREATE_COURSE_PAGE,
    DETAIL_COURSE_PAGE,
    EDIT_COURSE_PAGE,
    ERROR_PAGE,
    STATUS_ERROR,
)

courses_bp = Blueprint("courses", __name__, url_prefix="/courses")
mgr = CourseManager()


@courses_bp.route("/", methods=["GET"])
def list_courses():
    courses = mgr.get_all_courses()
    return render_template(ALL_COURSES_PAGE, courses=courses)


@courses_bp.route("/create", methods=["GET", "POST"])
@validate_with(
    schema=CourseSchema,
    template=CREATE_COURSE_PAGE,
    form_key="form",
    error_key="errors",
)
def create_course(validated: CourseSchema = None):
    if request.method == "POST":
        res = mgr.create_course(
            code=validated.codigo,
            description=validated.descripcion,
            requisites=validated.requisitos,
            credits=validated.creditos,
        )
        if res["status"] == STATUS_ERROR:
            return (
                render_template(
                    CREATE_COURSE_PAGE,
                    form=validated.dict(),
                    error=res["message"],
                ),
                HTTP_BAD_REQUEST,
            )
        return redirect(url_for("courses.list_courses"))

    empty = {"codigo": "", "descripcion": "", "requisitos": [], "creditos": ""}
    return render_template(CREATE_COURSE_PAGE, form=empty)


@courses_bp.route("/<int:course_id>", methods=["GET"])
def course_detail(course_id: int):
    course = mgr.get_course_by_id(course_id)
    if not course:
        return render_template(ERROR_PAGE, error="Curso no encontrado"), 404
    instances = mgr.get_instances_by_course_id(course_id)
    return render_template(
        DETAIL_COURSE_PAGE,
        course=course,
        instances=instances,
    )


@courses_bp.route("/<int:course_id>/edit", methods=["GET", "POST"])
@validate_with(
    schema=CourseSchema,
    template=EDIT_COURSE_PAGE,
    form_key="form",
    error_key="errors",
)
def edit_course(course_id: int, validated=None):
    course = mgr.get_course_by_id(course_id)
    if not course:
        return (
            render_template(
                DETAIL_COURSE_PAGE,
                error="Curso no encontrado",
            ),
            404,
        )

    if request.method == "POST":
        res = mgr.update_course(
            course_id=course_id,
            code=validated.codigo,
            description=validated.descripcion,
            requisites=validated.requisitos,
            credits=validated.creditos,
        )
        if res["status"] != "ok":
            return (
                render_template(
                    EDIT_COURSE_PAGE,
                    form=validated.dict(),
                    course=course,
                    error=res["message"],
                ),
                HTTP_BAD_REQUEST,
            )
        return redirect(url_for("courses.course_detail", course_id=course_id))

    form = {
        "codigo": course["code"],
        "descripcion": course["description"],
        "requisitos": course["requisites"],
        "creditos": course["credits"],
    }
    return render_template(
        EDIT_COURSE_PAGE,
        form=form,
        course=course,
        errors=None,
        error=None,
    )


@courses_bp.route("/<int:course_id>/delete", methods=["POST"])
def delete_course(course_id: int):
    res = mgr.delete_course(course_id)
    if res["status"] == STATUS_ERROR:
        return (
            render_template(
                ERROR_PAGE,
                error=res["message"],
            ),
            HTTP_BAD_REQUEST,
        )
    return redirect(url_for("courses.list_courses"))


@courses_bp.route("/<int:course_id>/close", methods=["POST"])
def close_course(course_id: int):
    try:
        course = mgr.get_course_by_id(course_id)
        if not course:
            flash("Curso no encontrado", "danger")
            return redirect(url_for("courses.list_courses"))
        if course.get("closed"):
            flash("Este curso ya está cerrado", "warning")
            return redirect(url_for("courses.list_courses"))

        res = mgr.close_course(course_id)
        if res["status"] != "ok":
            flash(f'Error al cerrar el curso: {res["message"]}', "danger")
        else:
            flash("Curso cerrado exitosamente", "success")
    except Exception as e:
        flash(f"Error al cerrar el curso: {str(e)}", "danger")

    return redirect(url_for("courses.list_courses"))


@courses_bp.route("/search", methods=["GET"])
def search_courses():
    q = request.args.get("q", "", type=str).strip()
    if not q:
        return jsonify([])

    try:
        resultados = mgr.search_courses_by_code(q, limit=10)
    except Exception:
        current_app.logger.exception("Error en search_courses:")
        return jsonify([]), 500

    payload = [
        {
            "id": curso["code"],
            "text": f"{curso['code']} – {curso['description']}",
        }
        for curso in resultados
    ]
    return jsonify(payload)
