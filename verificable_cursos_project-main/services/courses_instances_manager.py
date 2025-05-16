from mysql.connector import IntegrityError

from db import DatabaseConnection


class CourseInstanceManager:
    def __init__(self):
        self.db = DatabaseConnection()
        self.cur = self.db.connect()

    def _execute(
        self,
        sql: str,
        params: tuple,
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
            msg = str(e)
            if duplicate_message and "Duplicate entry" in msg:
                return {"status": "error", "message": duplicate_message}
            if fk_message and "Cannot delete or update a parent row" in msg:
                return {"status": "error", "message": fk_message}
            return {"status": "error", "message": msg}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def create_course_instance(self, course_id: int, semester: str, year: int) -> dict:
        return self._execute(
            """
            INSERT INTO course_instance
              (course_id, semester, year)
            VALUES (%s, %s, %s)
            """,
            (course_id, semester, year),
            duplicate_message="Ya existe esa instancia (curso+semestre+año).",
            return_id=True,
        )

    def get_course_instance_by_id(self, instance_id: int) -> dict:
        self.cur.execute("SELECT * FROM course_instance WHERE id = %s", (instance_id,))
        return self.cur.fetchone()

    def update_course_instance(
        self, instance_id: int, semester: str, year: int
    ) -> dict:
        self.cur.execute("SELECT 1 FROM course_instance WHERE id = %s", (instance_id,))
        if not self.cur.fetchone():
            return {"status": "error", "message": "Instancia no encontrada"}

        return self._execute(
            """
            UPDATE course_instance
            SET semester = %s,
                year = %s
            WHERE id = %s
            """,
            (semester, year, instance_id),
        )

    def delete_course_instance(self, instance_id: int) -> dict:
        return self._execute(
            "DELETE FROM course_instance WHERE id = %s",
            (instance_id,),
            fk_message="No se puede eliminar: hay secciones o evaluaciones asociadas.",
        )
