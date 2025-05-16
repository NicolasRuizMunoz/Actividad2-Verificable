from math import isclose

from mysql.connector import IntegrityError

from db import DatabaseConnection


class EvaluationManager:
    def __init__(self):
        self.db = DatabaseConnection() # Aca el error documentado
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

    def create_evaluation(
        self, course_instance_id: int, section_id: int, name: str, weight: float
    ) -> dict:

        self.cur.execute(
            "SELECT evaluation_scheme FROM section WHERE id = %s", (course_instance_id,)
        )
        row = self.cur.fetchone()
        if not row:
            return {"status": "error", "message": "Instancia no encontrada"}

        scheme = row["evaluation_scheme"]

        total = self._current_sum(course_instance_id, section_id)

        ok, msg = self._check_weight(scheme, weight, total)
        if not ok:
            return {"status": "error", "message": msg}

        try:
            self.cur.execute(
                """
                INSERT INTO evaluation
                    (course_instance_id, section_id, name, weight)
                VALUES (%s, %s, %s, %s)
                """,
                (course_instance_id, section_id, name, weight),
            )
            eval_id = self.cur.lastrowid
            self.db.commit()
            return {"status": "ok", "id": eval_id}
        except IntegrityError as e:
            self.db.rollback()
            err = str(e).lower()
            if "duplicate entry" in err:
                return {
                    "status": "error",
                    "message": "Nombre de evaluación duplicado en esta sección",
                }
            return {"status": "error", "message": "Error de integridad en la BD."}
        except Exception:
            self.db.rollback()
            return {
                "status": "error",
                "message": "Error inesperado al acceder a la BD.",
            }

    def _current_sum(
        self, course_instance_id: int, section_id: int, exclude_id: int = None
    ) -> float:
        sql = """
            SELECT COALESCE(SUM(weight),0) AS total
            FROM evaluation
            WHERE course_instance_id = %s
              AND section_id          <=> %s
        """
        params = [course_instance_id, section_id]
        if exclude_id:
            sql += " AND id <> %s"
            params.append(exclude_id)
        self.cur.execute(sql, params)
        return float(self.cur.fetchone()["total"])

    def _check_weight(
        self, scheme: str, new_weight: float, current_sum: float
    ) -> tuple[bool, str]:
        if scheme == "percentage":
            if new_weight > 100:
                return False, "El porcentaje no puede superar 100 %."
            total = current_sum + new_weight
            if total > 100 and not isclose(total, 100, abs_tol=1e-2):
                faltante = 100 - current_sum
                return False, f"Solo quedan {faltante:.2f} % disponibles."
        return True, ""

    def get_evaluation_scheme(self, instance_id: int) -> str:
        self.cur.execute(
            "SELECT evaluation_scheme FROM course_instance WHERE id = %s",
            (instance_id,),
        )
        row = self.cur.fetchone()
        return row["evaluation_scheme"] if row else None

    def get_evaluations_by_instance_id(self, instance_id: int) -> list[dict]:
        self.cur.execute(
            "SELECT * FROM evaluation WHERE course_instance_id = %s ORDER BY id",
            (instance_id,),
        )
        return self.cur.fetchall()

    def get_evaluation_by_id(self, eval_id: int) -> dict:
        self.cur.execute("SELECT * FROM evaluation WHERE id = %s", (eval_id,))
        return self.cur.fetchone()

    def update_evaluation(self, eval_id: int, name: str, weight: float) -> dict:
        self.cur.execute("SELECT * FROM evaluation WHERE id = %s", (eval_id,))
        row = self.cur.fetchone()
        if not row:
            return {"status": "error", "message": "Evaluación no encontrada"}

        self.cur.execute(
            "SELECT evaluation_scheme FROM section WHERE id = %s",
            (row["course_instance_id"],),
        )
        inst = self.cur.fetchone()
        scheme = inst["evaluation_scheme"]

        total = self._current_sum(
            row["course_instance_id"], row["section_id"], exclude_id=eval_id
        )
        ok, msg = self._check_weight(scheme, weight, total)
        if not ok:
            return {"status": "error", "message": msg}

        return self._execute(
            """
            UPDATE evaluation
            SET name = %s,
                weight = %s
            WHERE id = %s
            """,
            (name, weight, eval_id),
            duplicate_message="Nombre de evaluación duplicado en esta sección",
        )

    def delete_evaluation(self, evaluation_id: int) -> dict:
        try:
            self.cur.execute(
                """
                DELETE FROM grade
                WHERE evaluation_instance_id IN (
                    SELECT id FROM evaluation_instance WHERE evaluation_id = %s
                )
                """,
                (evaluation_id,),
            )
            self.cur.execute(
                "DELETE FROM evaluation_instance WHERE evaluation_id = %s",
                (evaluation_id,),
            )
            self.cur.execute("DELETE FROM evaluation WHERE id = %s", (evaluation_id,))
            self.db.commit()
            return {"status": "ok"}
        except Exception as e:
            self.db.rollback()
            return {"status": "ERROR", "message": str(e)}
