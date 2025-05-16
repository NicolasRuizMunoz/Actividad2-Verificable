from math import isclose

from mysql.connector import IntegrityError

from db import DatabaseConnection
from services.evaluations_manager import EvaluationManager


class EvaluationInstanceManager:
    def __init__(self):
        self.db = DatabaseConnection() # Aca el error documentado
        self.cur = self.db.connect()
        self.eval_mgr = EvaluationManager()

    def _execute(
        self, sql: str, params: tuple = (), *, duplicate_message: str = None
    ) -> dict:
        try:
            self.cur.execute(sql, params)
            self.db.commit()
            return {"status": "ok"}
        except IntegrityError as e:
            self.db.rollback()
            msg = str(e).lower()
            if duplicate_message and "duplicate entry" in msg:
                return {"status": "error", "message": duplicate_message}
            return {"status": "error", "message": "Error de integridad en la BD."}
        except Exception:
            self.db.rollback()
            return {
                "status": "error",
                "message": "Error inesperado al acceder a la BD.",
            }

    def _current_sum(self, evaluation_id: int, exclude_id: int = None) -> float:
        sql = "SELECT COALESCE(SUM(weight),0) AS total FROM evaluation_instance WHERE evaluation_id = %s"
        params = [evaluation_id]
        if exclude_id:
            sql += " AND id <> %s"
            params.append(exclude_id)
        self.cur.execute(sql, tuple(params))
        return float(self.cur.fetchone()["total"])

    def _convert_to_weight(self, evaluation_id: int):
        evaluation = self.eval_mgr.get_evaluation_by_id(evaluation_id)
        total_pct = self._current_sum(evaluation_id)
        if total_pct == 0:
            return
        target = evaluation["weight"]
        self.cur.execute(
            "SELECT id, weight FROM evaluation_instance WHERE evaluation_id = %s",
            (evaluation_id,),
        )
        for row in self.cur.fetchall():
            new_w = round(row["weight"] / 100 * target, 2)
            self.cur.execute(
                "UPDATE evaluation_instance SET weight = %s WHERE id = %s",
                (new_w, row["id"]),
            )
        self.db.commit()

    def _convert_to_percentage(self, evaluation_id: int):
        self.cur.execute(
            "SELECT id, weight FROM evaluation_instance WHERE evaluation_id = %s",
            (evaluation_id,),
        )
        rows = self.cur.fetchall()
        total = sum(r["weight"] for r in rows)
        if total == 0:
            return
        for r in rows:
            pct = round(r["weight"] / total * 100, 2)
            self.cur.execute(
                "UPDATE evaluation_instance SET weight = %s WHERE id = %s",
                (pct, r["id"]),
            )
        self.db.commit()

    def create_instance(
        self,
        evaluation_id: int,
        name: str,
        weight_type: str,
        weight: float,
        is_optional: bool,
    ) -> dict:
        existing = self.get_instances_by_evaluation_id(evaluation_id)
        if existing and weight_type != existing[0]["weight_type"]:
            return {
                "status": "error",
                "message": f"Debe usar '{existing[0]['weight_type']}' para esta evaluación",
            }
        if weight_type == "percentage":
            total = self._current_sum(evaluation_id) + weight
            if total > 100 and not isclose(total, 100.0, abs_tol=1e-2):
                return {
                    "status": "error",
                    "message": "La suma de porcentajes supera 100 %",
                }
        try:
            self.cur.execute(
                "INSERT INTO evaluation_instance (evaluation_id, name, weight_type, weight, is_optional) VALUES (%s, %s, %s, %s, %s)",
                (evaluation_id, name, weight_type, weight, is_optional),
            )
            instance_id = self.cur.lastrowid
            self.db.commit()
            return {"status": "ok", "id": instance_id}
        except IntegrityError as e:
            self.db.rollback()
            err = str(e).lower()
            if "duplicate entry" in err:
                return {
                    "status": "error",
                    "message": "Nombre de instancia duplicado en esta evaluación",
                }
            return {"status": "error", "message": "Error de integridad en la BD."}
        except Exception:
            self.db.rollback()
            return {
                "status": "error",
                "message": "Error inesperado al acceder a la BD.",
            }

    def get_instances_by_evaluation_id(self, evaluation_id: int) -> list[dict]:
        self.cur.execute(
            "SELECT * FROM evaluation_instance WHERE evaluation_id = %s ORDER BY id",
            (evaluation_id,),
        )
        return self.cur.fetchall()

    def get_instance_by_id(self, instance_id: int) -> dict:
        self.cur.execute(
            "SELECT * FROM evaluation_instance WHERE id = %s", (instance_id,)
        )
        return self.cur.fetchone()

    def update_instance(
        self,
        instance_id: int,
        name: str,
        weight_type: str,
        weight: float,
        is_optional: bool,
    ) -> dict:
        inst = self.get_instance_by_id(instance_id)
        if not inst:
            return {"status": "error", "message": "Instancia no encontrada"}

        old_type = inst["weight_type"]

        if old_type != weight_type:
            if weight_type == "percentage":
                self._convert_to_percentage(inst["evaluation_id"])
                self.cur.execute(
                    "SELECT weight FROM evaluation_instance WHERE id = %s",
                    (instance_id,),
                )
                weight = float(self.cur.fetchone()["weight"])
        else:
            if weight_type == "percentage":
                total = self._current_sum(inst["evaluation_id"], exclude_id=instance_id)
                if total + weight > 100:
                    return {
                        "status": "error",
                        "message": "La suma de porcentajes supera 100 %",
                    }

        return self._execute(
            """
            UPDATE evaluation_instance
            SET name        = %s,
                weight_type = %s,
                weight      = %s,
                is_optional = %s
            WHERE id = %s
            """,
            (name, weight_type, weight, is_optional, instance_id),
            duplicate_message="Instancia duplicada para esta evaluación",
        )

    def delete_instance(self, instance_id: int) -> dict:
        return self._execute(
            "DELETE FROM evaluation_instance WHERE id = %s", (instance_id,)
        )
