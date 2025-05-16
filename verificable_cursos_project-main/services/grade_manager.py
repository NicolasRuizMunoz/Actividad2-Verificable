from db import DatabaseConnection


class GradeManager:
    def __init__(self):
        self.database = DatabaseConnection() # Aca el error documentado
        self.cursor = self.database.connect()

    def get_grades_for_instance(self, instance_id: int) -> dict[int, float]:
        sql = """
        SELECT student_id, grade
        FROM grade
        WHERE evaluation_instance_id = %s
        """
        self.cursor.execute(sql, (instance_id,))
        result = self.cursor.fetchall()
        return {row["student_id"]: row["grade"] for row in result}

    def save_grade(self, student_id: int, instance_id: int, grade: float):
        sql_check = """
        SELECT id
        FROM grade
        WHERE student_id = %s AND evaluation_instance_id = %s
        """
        self.cursor.execute(sql_check, (student_id, instance_id))
        existing = self.cursor.fetchone()
        if existing:
            sql_update = """
            UPDATE grade
            SET grade = %s
            WHERE student_id = %s AND evaluation_instance_id = %s
            """
            self.cursor.execute(sql_update, (grade, student_id, instance_id))
        else:
            sql_insert = """
            INSERT INTO grade (student_id, evaluation_instance_id, grade)
            VALUES (%s, %s, %s)
            """
            self.cursor.execute(sql_insert, (student_id, instance_id, grade))
        self.database.commit()
        return {"status": "ok"}

    def delete_grade(self, student_id: int, instance_id: int):
        sql_delete = """
        DELETE FROM grade
        WHERE student_id = %s AND evaluation_instance_id = %s
        """
        self.cursor.execute(sql_delete, (student_id, instance_id))
        self.database.commit()

    def get_grades_for_instances(
        self, instance_ids: list[int]
    ) -> dict[tuple[int, int], float]:
        if not instance_ids:
            return {}
        placeholders = ",".join(["%s"] * len(instance_ids))
        sql = f"""
        SELECT student_id, evaluation_instance_id, grade
        FROM grade
        WHERE evaluation_instance_id IN ({placeholders})
        """
        self.cursor.execute(sql, instance_ids)
        result = self.cursor.fetchall()
        return {
            (row["evaluation_instance_id"], row["student_id"]): row["grade"]
            for row in result
        }
