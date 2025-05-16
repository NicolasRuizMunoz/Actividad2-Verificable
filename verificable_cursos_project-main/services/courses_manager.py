import json

from mysql.connector import IntegrityError

from db import DatabaseConnection
from settings import STATUS_ERROR


class CourseManager:
    def __init__(self):
        self.db = DatabaseConnection() # Aca el error documentado
        self.cur = self.db.connect()

    def _execute(
        self,
        sql: str,
        params: tuple = (),
        *,
        duplicate_message: str = None,
        fk_message: str = None,
        return_id: bool = False,
    ) -> dict:
        try:
            self.cur.execute(sql, params)
            self.db.commit()
            if return_id:
                return {"status": "ok", "id": self.cur.lastrowid}
            return {"status": "ok"}
        except IntegrityError as e:
            self.db.rollback()
            msg = "Error de integridad en la base de datos."
            text = str(e).lower()
            if duplicate_message and "duplicate entry" in text:
                msg = duplicate_message
            elif fk_message and ("foreign key" in text or "constraint" in text):
                msg = fk_message
            return {"status": "error", "message": msg}
        except Exception:
            self.db.rollback()
            return {
                "status": "error",
                "message": "Error inesperado al acceder a la BD.",
            }

    def create_course(
        self,
        code: str,
        description: str,
        requisites: list[str],
        credits: int,
    ) -> dict:
        req_json = json.dumps(requisites, ensure_ascii=False)
        return self._execute(
            """
            INSERT INTO course
              (code, description, requisites, credits)
            VALUES (%s, %s, %s, %s)
            """,
            (code, description, req_json, credits),
            duplicate_message="Este código ya está registrado para otro curso.",
            return_id=True,
        )

    def get_all_courses(self) -> list[dict]:
        self.cur.execute(
            """
            SELECT 
                id,
                code,
                description,
                requisites,
                credits,
                closed
            FROM course
            ORDER BY code
        """
        )
        rows = self.cur.fetchall()
        for r in rows:
            try:
                r["requisites"] = json.loads(r.get("requisites") or "[]")
            except (TypeError, ValueError):
                r["requisites"] = []
        return rows

    def get_course_by_id(self, course_id: int) -> dict:
        self.cur.execute("SELECT * FROM course WHERE id = %s", (course_id,))
        row = self.cur.fetchone()
        if not row:
            return None
        try:
            row["requisites"] = json.loads(row.get("requisites") or "[]")
        except (TypeError, ValueError):
            row["requisites"] = []
        return row

    def get_course_by_code(self, code: str) -> dict:
        self.cur.execute("SELECT * FROM course WHERE code = %s", (code,))
        return self.cur.fetchone()

    def search_courses_by_code(self, query: str, limit: int = 10) -> list[dict]:
        sql = """
            SELECT code, description
              FROM course
             WHERE UPPER(code) LIKE %s
             ORDER BY code
             LIMIT %s
        """
        pattern = f"%{query.upper()}%"
        self.cur.execute(sql, (pattern, limit))
        return self.cur.fetchall()

    def update_course(
        self,
        course_id: int,
        code: str,
        description: str,
        requisites: list[str],
        credits: int,
    ) -> dict:
        req_json = json.dumps(requisites, ensure_ascii=False)
        return self._execute(
            """
            UPDATE course
            SET code = %s,
                description = %s,
                requisites = %s,
                credits = %s
            WHERE id = %s
            """,
            (code, description, req_json, credits, course_id),
            duplicate_message="Este código ya está registrado para otro curso.",
        )

    def remove_prerequisite_references(self, code: str) -> None:
        import json

        self.cur.execute(
            "SELECT id, requisites FROM course WHERE JSON_CONTAINS(requisites, %s, '$')",
            (json.dumps(code),),
        )
        for row in self.cur.fetchall():
            reqs = json.loads(row["requisites"] or "[]")
            nuevos = [r for r in reqs if r != code]
            self.cur.execute(
                "UPDATE course SET requisites = %s WHERE id = %s",
                (json.dumps(nuevos), row["id"]),
            )
        self.cur._connection.commit()

    def delete_course(self, course_id: int) -> dict:
        course = self.get_course_by_id(course_id)
        if not course:
            return {"status": STATUS_ERROR, "message": "Curso no encontrado"}
        self.remove_prerequisite_references(course["code"])
        return self._execute(
            "DELETE FROM course WHERE id = %s",
            (course_id,),
            fk_message="No se puede eliminar curso con instancias o secciones asociadas.",
        )

    def get_instances_by_course_id(self, course_id: int) -> list[dict]:
        self.cur.execute(
            "SELECT * FROM course_instance WHERE course_id = %s", (course_id,)
        )
        return self.cur.fetchall()

    def create_section(self, course_instance_id: int, section_number: str) -> dict:
        return self._execute(
            "INSERT INTO section (course_instance_id, section_number) VALUES (%s, %s)",
            (course_instance_id, section_number),
            duplicate_message="Esta sección ya está registrada.",
        )

    def get_sections_by_instance_id(self, course_instance_id: int) -> list[dict]:
        self.cur.execute(
            "SELECT * FROM section WHERE course_instance_id = %s", (course_instance_id,)
        )
        return self.cur.fetchall()

    def get_section_by_id(self, section_id: int) -> dict:
        self.cur.execute("SELECT * FROM section WHERE id = %s", (section_id,))
        return self.cur.fetchone()

    def update_section(self, section_id: int, section_number: str) -> dict:
        return self._execute(
            "UPDATE section SET section_number = %s WHERE id = %s",
            (section_number, section_id),
            duplicate_message="Ya existe otra sección con ese número.",
        )

    def delete_section(self, section_id: int) -> dict:
        return self._execute(
            "DELETE FROM section WHERE id = %s",
            (section_id,),
            fk_message="No se puede eliminar sección con asignaciones o evaluaciones.",
        )

    def create_evaluation(
        self,
        course_instance_id: int,
        section_id: int,
        name: str,
        weight_type: str,
        weight: float,
    ) -> dict:
        return self._execute(
            "INSERT INTO evaluation (course_instance_id, section_id, name, weight_type, weight) "
            "VALUES (%s, %s, %s, %s, %s)",
            (course_instance_id, section_id, name, weight_type, weight),
            duplicate_message="Esta evaluación ya está registrada para esta instancia/sección.",
        )

    def get_evaluation_scheme(self, instance_id: int) -> str:
        self.cur.execute(
            "SELECT evaluation_scheme FROM course_instance WHERE id = %s",
            (instance_id,),
        )
        row = self.cur.fetchone()
        return row["evaluation_scheme"] if row else None

    def get_evaluations_by_instance_id(self, instance_id: int) -> list[dict]:
        self.cur.execute(
            "SELECT id, name, weight_type, weight, section_id "
            "FROM evaluation WHERE course_instance_id = %s "
            "ORDER BY name ASC",
            (instance_id,),
        )
        return self.cur.fetchall()

    def get_evaluation_by_id(self, evaluation_id: int) -> dict:
        self.cur.execute("SELECT * FROM evaluation WHERE id = %s", (evaluation_id,))
        return self.cur.fetchone()

    def update_evaluation(
        self, evaluation_id: int, name: str, weight_type: str, weight: float
    ) -> dict:
        return self._execute(
            "UPDATE evaluation SET name = %s, weight_type = %s, weight = %s WHERE id = %s",
            (name, weight_type, weight, evaluation_id),
            duplicate_message="Ya existe otra evaluación con ese nombre.",
        )

    def create_evaluation_instance(
        self, evaluation_id: int, name: str, weight: float, is_optional: bool
    ) -> dict:
        return self._execute(
            "INSERT INTO evaluation_instance (evaluation_id, name, weight_type, weight, is_optional) "
            "VALUES (%s, %s, %s, %s, %s)",
            (evaluation_id, name, "percentage", weight, is_optional),
            duplicate_message="Esta instancia de evaluación ya existe.",
        )

    def get_evaluation_instance_by_id(self, instance_id: int) -> dict:
        self.cur.execute(
            "SELECT * FROM evaluation_instance WHERE id = %s", (instance_id,)
        )
        return self.cur.fetchone()

    def update_evaluation_instance(
        self, instance_id: int, name: str, weight: float, is_optional: bool
    ) -> dict:
        return self._execute(
            "UPDATE evaluation_instance SET name = %s, weight = %s, is_optional = %s WHERE id = %s",
            (name, weight, is_optional, instance_id),
            duplicate_message="Ya existe otra instancia con ese nombre.",
        )

    def get_grades_for_instance(self, instance_id: int) -> dict:
        self.cur.execute(
            "SELECT student_id, grade FROM grade WHERE evaluation_instance_id = %s",
            (instance_id,),
        )
        return {row["student_id"]: row["grade"] for row in self.cur.fetchall()}

    def save_grade(self, student_id: int, instance_id: int, grade: float) -> dict:
        return self._execute(
            "INSERT INTO grade (student_id, evaluation_instance_id, grade) "
            "VALUES (%s, %s, %s) "
            "ON DUPLICATE KEY UPDATE grade = VALUES(grade)",
            (student_id, instance_id, grade),
        )

    def delete_grade(self, student_id: int, instance_id: int) -> dict:
        return self._execute(
            "DELETE FROM grade WHERE student_id = %s AND evaluation_instance_id = %s",
            (student_id, instance_id),
        )

    def get_grades_for_instances(self, instance_ids: list[int]) -> dict:
        if not instance_ids:
            return {}
        placeholders = ",".join(["%s"] * len(instance_ids))
        sql = (
            f"SELECT student_id, evaluation_instance_id, grade "
            f"FROM grade WHERE evaluation_instance_id IN ({placeholders})"
        )
        self.cur.execute(sql, instance_ids)
        return {
            (row["evaluation_instance_id"], row["student_id"]): row["grade"]
            for row in self.cur.fetchall()
        }

    def close_course(self, course_id: int) -> dict:
        """Close a course, preventing further modifications"""
        try:
            self.cur.execute(
                """
                UPDATE course 
                SET closed = TRUE 
                WHERE id = %s
                """,
                (course_id,),
            )
            if self.cur.rowcount == 0:
                return {"status": "error", "message": "Curso no encontrado"}
            self.db.commit()
            return {"status": "ok"}
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": str(e)}
