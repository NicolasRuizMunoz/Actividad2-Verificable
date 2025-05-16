from typing import List, Optional

from db import DatabaseConnection


class ClassroomManager:
    def __init__(self):
        self.db = DatabaseConnection() # Aca el error documentado
        self.cur = self.db.connect()

    def create_classroom(self, name: str, capacity: int) -> dict:
        try:
            self.cur.execute(
                "INSERT INTO classroom (name, capacity) VALUES (%s, %s)",
                (name, capacity),
            )
            self.db.commit()
            return {"status": "ok", "id": self.cur.lastrowid}
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": str(e)}

    def get_classroom(self, classroom_id: int) -> Optional[dict]:
        self.cur.execute(
            "SELECT id, name, capacity FROM classroom WHERE id = %s", (classroom_id,)
        )
        result = self.cur.fetchone()
        if result:
            return {"id": result[0], "name": result[1], "capacity": result[2]}
        return None

    def get_all_classrooms(self) -> List[dict]:
        self.cur.execute("SELECT id, name, capacity FROM classroom")
        return [
            {"id": row[0], "name": row[1], "capacity": row[2]}
            for row in self.cur.fetchall()
        ]
