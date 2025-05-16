from mysql.connector import IntegrityError

from db import DatabaseConnection
from settings import STATUS_ERROR


class SectionManager:
    def __init__(self):
        self.db = DatabaseConnection()
        self.cur = self.db.connect()

    def _execute(
        self, sql: str, params: tuple = (), *, duplicate_message: str = None
    ) -> dict:
        try:
            self.cur.execute(sql, params)
            self.db.commit()
            return {"status": "ok"}
        except IntegrityError as e:
            self.db.rollback()
            err = str(e)
            print("SQL ERROR:", err)
            print("QUERY   :", sql)
            print("PARAMS  :", params)
            if duplicate_message and "duplicate entry" in err.lower():
                return {"status": "error", "message": duplicate_message}
            return {"status": "error", "message": err}
        except Exception as e:
            self.db.rollback()
            err = str(e)
            print("UNEXPECTED ERROR:", err)
            print("QUERY           :", sql)
            print("PARAMS          :", params)
            return {"status": "error", "message": err}

    def create_section(
        self, course_instance_id: int, section_number: str, evaluation_scheme: str
    ) -> dict:
        try:
            self.cur.execute(
                "INSERT INTO section (course_instance_id, section_number, evaluation_scheme) VALUES (%s, %s, %s)",
                (course_instance_id, section_number, evaluation_scheme),
            )
            section_id = self.cur.lastrowid
            self.db.commit()
            return {"status": "ok", "id": section_id}
        except IntegrityError as e:
            self.db.rollback()
            err = str(e)
            print("SQL ERROR:", err)
            if "duplicate entry" in err.lower():
                return {
                    "status": "error",
                    "message": "Sección duplicada en esta instancia",
                }
            return {"status": "error", "message": err}
        except Exception as e:
            self.db.rollback()
            err = str(e)
            print("UNEXPECTED ERROR:", err)
            return {"status": "error", "message": err}

    def get_sections_by_instance_id(self, instance_id: int) -> list[dict]:
        self.cur.execute(
            "SELECT * FROM section WHERE course_instance_id = %s ORDER BY id",
            (instance_id,),
        )
        return self.cur.fetchall()

    def get_section_by_id(self, section_id: int) -> dict:
        self.cur.execute("SELECT * FROM section WHERE id = %s", (section_id,))
        return self.cur.fetchone()

    def update_section(
        self,
        section_id: int,
        course_instance_id: int,
        section_number: str,
        evaluation_scheme: str,
    ) -> dict:
        self.cur.execute(
            "SELECT evaluation_scheme FROM section WHERE id = %s", (section_id,)
        )
        row = self.cur.fetchone()
        if not row:
            return {"status": "error", "message": "Sección no encontrada"}

        old_scheme = row["evaluation_scheme"]
        res = self._execute(
            "UPDATE section SET course_instance_id = %s, section_number = %s, evaluation_scheme = %s WHERE id = %s",
            (course_instance_id, section_number, evaluation_scheme, section_id),
            duplicate_message="Sección duplicada en esta instancia",
        )
        if res.get("status") != "ok":
            return res

        if old_scheme == "weight" and evaluation_scheme == "percentage":
            self._convert_weights_to_percentage(course_instance_id, section_id)
        return {"status": "ok"}

    def assign_professor_to_section(self, section_id: int, professor_id: int) -> dict:
        return self._execute(
            "INSERT INTO professor_assignment (professor_id, course_instance_id, section_id) VALUES (%s, (SELECT course_instance_id FROM section WHERE id = %s), %s)",
            (professor_id, section_id, section_id),
            duplicate_message="Este profesor ya está asignado a esta sección.",
        )

    def assign_student_to_section(self, section_id: int, student_id: int) -> dict:
        return self._execute(
            "INSERT INTO student_assignment (student_id, course_instance_id, section_id) VALUES (%s, (SELECT course_instance_id FROM section WHERE id = %s), %s)",
            (student_id, section_id, section_id),
            duplicate_message="Este estudiante ya está inscrito en esta sección.",
        )

    def get_professors_by_section(self, section_id: int) -> list[dict]:
        self.cur.execute(
            "SELECT p.* FROM professor p JOIN professor_assignment pa ON p.id = pa.professor_id WHERE pa.section_id = %s",
            (section_id,),
        )
        return self.cur.fetchall()

    def get_students_by_section(self, section_id: int) -> list[dict]:
        self.cur.execute(
            "SELECT s.* FROM student s JOIN student_assignment sa ON s.id = sa.student_id WHERE sa.section_id = %s",
            (section_id,),
        )
        return self.cur.fetchall()

    def get_evaluations_by_section(
        self, section_id: int, course_instance_id: int
    ) -> list[dict]:
        self.cur.execute(
            """
            SELECT * FROM evaluation
            WHERE course_instance_id = %s AND section_id = %s
            """,
            (course_instance_id, section_id),
        )
        return self.cur.fetchall()

    def delete_section(self, section_id: int) -> dict:
        try:
            self.cur.execute(
                """
                DELETE FROM grade
                WHERE evaluation_instance_id IN (
                    SELECT ei.id
                    FROM evaluation_instance ei
                    JOIN evaluation e ON e.id = ei.evaluation_id
                    WHERE e.section_id = %s
                )""",
                (section_id,),
            )

            self.cur.execute(
                """
                DELETE FROM evaluation_instance
                WHERE evaluation_id IN (
                    SELECT id FROM evaluation WHERE section_id = %s
                )""",
                (section_id,),
            )

            self.cur.execute(
                "DELETE FROM evaluation WHERE section_id = %s", (section_id,)
            )
            self.cur.execute(
                "DELETE FROM professor_assignment WHERE section_id = %s", (section_id,)
            )
            self.cur.execute(
                "DELETE FROM student_assignment WHERE section_id = %s", (section_id,)
            )
            self.cur.execute("DELETE FROM section WHERE id = %s", (section_id,))
            self.db.commit()
            return {"status": "ok"}
        except Exception as e:
            self.db.rollback()
            return {"status": STATUS_ERROR, "message": str(e)}

    def _convert_weights_to_percentage(self, instance_id: int, section_id: int):
        self.cur.execute(
            """
            SELECT SUM(weight) AS total
            FROM evaluation
            WHERE course_instance_id = %s AND section_id = %s
            GROUP BY section_id
            """,
            (instance_id, section_id),
        )
        row = self.cur.fetchone()
        total = row["total"] if row else 0
        if total <= 0:
            return

        self.cur.execute(
            "SELECT id, weight FROM evaluation WHERE course_instance_id = %s AND section_id = %s",
            (instance_id, section_id),
        )
        for ev in self.cur.fetchall():
            pct = round(ev["weight"] / total * 100, 2)
            self.cur.execute(
                "UPDATE evaluation SET weight = %s WHERE id = %s", (pct, ev["id"])
            )
        self.db.commit()
