from datetime import date

# settings.py

# Status codes
STATUS_OK = "ok"
STATUS_ERROR = "error"

# Vistas estudiantes
ALL_STUDENTS_PAGE = "students/list.html"
CREATE_STUDENT_PAGE = "students/create.html"
EDIT_STUDENT_PAGE = "students/edit.html"
DETAIL_STUDENT_PAGE = "students/detail.html"

# Vistas profesores
ALL_PROFESSORS_PAGE = "professors/list.html"
CREATE_PROFESSOR_PAGE = "professors/create.html"
EDIT_PROFESSOR_PAGE = "professors/edit.html"
DETAIL_PROFESSOR_PAGE = "professors/detail.html"

# Vistas cursos
ALL_COURSES_PAGE = "courses/list.html"
CREATE_COURSE_PAGE = "courses/create.html"
EDIT_COURSE_PAGE = "courses/edit.html"
DETAIL_COURSE_PAGE = "courses/detail.html"
CREATE_COURSE_INSTANCE_PAGE = "courses/create_instance.html"
CREATE_SECTION_PAGE = "courses/create_section.html"
DETAIL_COURSE_INSTANCE_PAGE = "courses/detail_instance.html"

# Página de listado general
HOME_PAGE = "home/home.html"

# Error
ERROR_PAGE = "error/404.html"

# Configuración general
VIEW_BASE_URL = "templates"
STATIC_BASE_URL = "static"

# Constantes de Fechas Límite

MIN_DATE = date(1990, 1, 1)
MAX_DATE = date.today()

MIN_YEAR = MIN_DATE.year
MAX_YEAR = MAX_DATE.year
