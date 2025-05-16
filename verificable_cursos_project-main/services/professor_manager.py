from mysql.connector import IntegrityError

from db import DatabaseConnection


class ProfessorManager:
    def __init__(self):
        self.db = DatabaseConnection() # Aca el error documentado
        self.cur = self.db.connect()

    def _execute(self, sql, params=(), *, duplicate_message=None, return_id=False):
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

    def create_professor(self, name: str, email: str):
        return self._execute(
            "INSERT INTO professor (name, email) VALUES (%s, %s)",
            (name, email),
            duplicate_message="Este correo ya está registrado para otro profesor.",
            return_id=True,
        )

    def get_all_professors(self) -> list[dict]:
        self.cur.execute("SELECT * FROM professor")
        return self.cur.fetchall()

    def get_professor_by_id(self, professor_id: int) -> dict:
        self.cur.execute("SELECT * FROM professor WHERE id = %s", (professor_id,))
        return self.cur.fetchone()

    def update_professor(self, professor_id: int, name: str, email: str):
        return self._execute(
            "UPDATE professor SET name = %s, email = %s WHERE id = %s",
            (name, email, professor_id),
            duplicate_message="Este correo ya está registrado para otro profesor.",
        )

    def delete_professor(self, professor_id: int):
        return self._execute(
            "DELETE FROM professor WHERE id = %s",
            (professor_id,),
        )
