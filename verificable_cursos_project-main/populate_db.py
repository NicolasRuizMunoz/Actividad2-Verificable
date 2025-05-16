import json
from datetime import date
from pathlib import Path

from app.validators import course as course_validator
from app.validators import course_instance as ci_validator
from app.validators import professor as professor_validator
from app.validators import student as student_validator
from db import DatabaseConnection
from services import (
    classroom_manager,
    courses_instances_manager,
    courses_manager,
    evaluation_instance_manager,
    evaluations_manager,
    grade_manager,
    professor_manager,
    section_manager,
    student_manager,
)

SCHEME_MAP = {"porcentaje": "percentage", "peso": "weight"}


class PopulateDB:
    DATA_DIR = Path(__file__).parent / "data"
    SCHEMA_SQL = Path(__file__).parent / "db" / "db.sql"

    def __init__(self):
        self.db = DatabaseConnection()
        self.cur = self.db.connect()
        self.stu_mgr = student_manager.StudentManager()
        self.prof_mgr = professor_manager.ProfessorManager()
        self.courses_mgr = courses_manager.CourseManager()
        self.ci_mgr = courses_instances_manager.CourseInstanceManager()
        self.sec_mgr = section_manager.SectionManager()
        self.ev_mgr = evaluations_manager.EvaluationManager()
        self.ei_mgr = evaluation_instance_manager.EvaluationInstanceManager()
        self.gr_mgr = grade_manager.GradeManager()
        self.classroom_mgr = classroom_manager.ClassroomManager()

    def load_json(self, name: str) -> dict:
        with open(self.DATA_DIR / name, encoding="utf-8") as f:
            return json.load(f)

    def reset_schema(self):
        self.cur.execute("SET FOREIGN_KEY_CHECKS=0;")
        self.cur.execute("SHOW TABLES;")
        for row in self.cur.fetchall():
            self.cur.execute(f"DROP TABLE IF EXISTS `{list(row.values())[0]}`;")
        self.cur.execute("SET FOREIGN_KEY_CHECKS=1;")
        self.db.commit()
        sql = self.SCHEMA_SQL.read_text(encoding="utf-8")
        for stmt in sql.split(";"):
            s = stmt.strip()
            if s:
                self.cur.execute(s + ";")
        self.db.commit()

    def load_professors(self):
        for raw in self.load_json("2-profesores.json")["profesores"]:
            prof = professor_validator.ProfessorSchema.model_construct(**raw)
            self.prof_mgr.create_professor(prof.nombre, prof.correo)

    def load_courses(self):
        for raw in self.load_json("3-cursos.json")["cursos"]:
            try:
                c = course_validator.CourseSchema(**raw)
            except Exception:
                c = course_validator.CourseSchema.model_construct(**raw)
            self.courses_mgr.create_course(
                c.codigo, c.descripcion, c.requisitos, c.creditos
            )

    def load_course_instances(self):
        for raw in self.load_json("4-instancias_cursos.json")["instancias"]:
            ci = ci_validator.CourseInstanceSchema.model_construct(
                id=raw["id"],
                course_id=raw["curso_id"],
                semester=str(raw.get("semestre", "01")).zfill(2),
                year=int(raw.get("año", date.today().year)),
            )
            self.ci_mgr.create_course_instance(ci.course_id, ci.semester, ci.year)

    def load_sections_and_evaluations(self): # Aca el error documentado
        """Load sections and their evaluations from JSON file."""
        data = self.load_json("5-instancia_cursos_con_secciones.json")

        for raw in data["secciones"]:
            # 5.1) sección
            r_sec = self.sec_mgr.create_section(
                raw["instancia_curso"], str(raw["id"]), "percentage"
            )
            if r_sec.get("status") != "ok":
                print("Section error:", r_sec.get("message"))
                continue

            sec_id = r_sec["id"]

            self.cur.execute(
                "INSERT INTO professor_assignment (section_id, professor_id, course_instance_id) VALUES (%s, %s, %s)",
                (sec_id, raw["profesor_id"], raw["instancia_curso"]),
            )

            # 5.2) evaluaciones
            scheme = (
                "percentage"
                if raw["evaluacion"]["tipo"] == "porcentaje"
                else raw["evaluacion"]["tipo"]
            )
            eval_ids = {}

            for topic in raw["evaluacion"]["combinacion_topicos"]:
                r_eval = self.ev_mgr.create_evaluation(
                    raw["instancia_curso"],  # course_instance_id
                    sec_id,  # section_id
                    topic["nombre"],  # name
                    float(topic["valor"]),  # weight
                )
                if r_eval.get("status") != "ok":
                    print("Evaluation error:", r_eval.get("message"))
                    continue

                eval_id = r_eval["id"]
                eval_ids[str(topic["id"])] = eval_id

                r_ie = self.ei_mgr.create_instance(
                    eval_id,
                    f"Instancia {topic['nombre']}",
                    scheme,
                    float(topic["valor"]),
                    True,
                )
                if r_ie.get("status") != "ok":
                    print("Evaluation instance error:", r_ie.get("message"))
                    continue

    def load_students(self):
        for raw in self.load_json("1-alumnos.json")["alumnos"]:
            alum = student_validator.StudentSchema.model_construct(**raw)
            year = getattr(alum.anio_ingreso, "year", int(raw["anio_ingreso"]))
            ins_date = date(year, 3, 1)
            self.stu_mgr.create_student(alum.nombre, alum.correo, ins_date)

    def load_enrollments(self):
        for raw in self.load_json("6-alumnos_por_seccion.json")["alumnos_seccion"]:
            self.sec_mgr.assign_student_to_section(raw["seccion_id"], raw["alumno_id"])

    def load_grades(self):
        for raw in self.load_json("7-notas_alumnos.json")["notas"]:
            self.gr_mgr.save_grade(raw["alumno_id"], raw["instancia"], raw["nota"])

    def load_classrooms(self):
        for raw in self.load_json("8-salas_de_clases.json")["salas"]:
            name = raw["nombre"]
            capacity = raw["capacidad"]
            self.classroom_mgr.create_classroom(name, capacity)

    def run(self):
        self.reset_schema()
        self.load_professors()
        self.load_courses()
        self.load_course_instances()
        self.load_classrooms()
        self.load_sections_and_evaluations()
        self.load_students()
        self.load_enrollments()
        self.load_grades()
        self.db.commit()
        print("▶ Carga masiva completada")


if __name__ == "__main__":
    PopulateDB().run()
