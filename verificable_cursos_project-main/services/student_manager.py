from datetime import date

from mysql.connector import IntegrityError

from db import DatabaseConnection


class StudentManager:
    def __init__(self):
        self.db = DatabaseConnection() # Aca el error documentado
        self.cur = self.db.connect()

    def _execute(
        self,
        sql: str,
        params: tuple = (),
        *,
        duplicate_message: str = None,
        return_id: bool = False
    ) -> dict:
        try:
            self.cur.execute(sql, params)
            self.db.commit()
            if return_id:
                return {"status": "ok", "id": self.cur.lastrowid}
            return {"status": "ok"}
        except IntegrityError as e:
            self.db.rollback()
            err = str(e).lower()
            if duplicate_message and "duplicate entry" in err:
                return {"status": "error", "message": duplicate_message}
            return {"status": "error", "message": "Error de integridad en la BD."}
        except Exception:
            self.db.rollback()
            return {
                "status": "error",
                "message": "Error inesperado al acceder a la BD.",
            }

    def create_student(self, name: str, email: str, enrollment_date: date) -> dict:
        return self._execute(
            "INSERT INTO student (name, email, enrollment_date) VALUES (%s, %s, %s)",
            (name, email, enrollment_date),
            duplicate_message="Este correo ya está registrado.",
            return_id=True,
        )

    def get_all_students(self) -> list[dict]:
        self.cur.execute("SELECT * FROM student")
        return self.cur.fetchall()

    def get_student_by_id(self, student_id: int) -> dict:
        self.cur.execute("SELECT * FROM student WHERE id = %s", (student_id,))
        return self.cur.fetchone()

    def update_student(
        self, student_id: int, name: str, email: str, enrollment_date: date
    ) -> dict:
        return self._execute(
            "UPDATE student SET name = %s, email = %s, enrollment_date = %s WHERE id = %s",
            (name, email, enrollment_date, student_id),
            duplicate_message="Este correo ya está registrado.",
        )

    def delete_student(self, student_id: int) -> dict:
        try:
            return self._execute("DELETE FROM student WHERE id = %s", (student_id,))
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": str(e)}
