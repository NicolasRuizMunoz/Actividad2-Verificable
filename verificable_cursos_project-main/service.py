import mysql.connector

from db import DatabaseConnection


class StudentManager:
    def __init__(self):
        self.database = DatabaseConnection() #Aca el error documentado
        self.cursor = self.database.connect()

    def create_student(self, name, email, enrollment_date):
        try:
            sql = (
                "INSERT INTO student (name, email, enrollment_date) "
                "VALUES (%s, %s, %s)"
            )
            self.cursor.execute(sql, (name, email, enrollment_date))
            self.database.commit()
            return {"status": "ok"}
        except mysql.connector.IntegrityError as e:
            if "Duplicate entry" in str(e):
                return {"status": "error", "message": "Este correo ya está registrado."}
            return {"status": "error", "message": "Error al guardar el estudiante."}

    def get_all_students(self):
        self.cursor.execute("SELECT * FROM student")
        return self.cursor.fetchall()

    def get_student_by_id(self, student_id):
        sql = "SELECT * FROM student WHERE id = %s"
        self.cursor.execute(sql, (student_id,))
        return self.cursor.fetchone()

    def update_student(self, student_id, name, email, enrollment_date):
        sql = (
            "UPDATE student SET name = %s, email = %s, enrollment_date = %s "
            "WHERE id = %s"
        )
        self.cursor.execute(sql, (name, email, enrollment_date, student_id))
        self.database.commit()

    def delete_student(self, student_id):
        self.cursor.execute("DELETE FROM student WHERE id = %s", (student_id,))
        self.database.commit()


class ProfessorManager:
    def __init__(self):
        self.database = DatabaseConnection()
        self.cursor = self.database.connect()

    def create_professor(self, name: str, email: str):
        try:
            sql = "INSERT INTO professor (name, email) VALUES (%s, %s)"
            self.cursor.execute(sql, (name, email))
            self.database.commit()
            return {"status": "ok"}
        except mysql.connector.IntegrityError as e:
            if "Duplicate entry" in str(e):
                return {
                    "status": "error",
                    "message": ("Este correo ya está registrado para otro profesor."),
                }
            return {
                "status": "error",
                "message": ("Error al guardar el profesor."),
            }
        except Exception as e:
            print("Error al guardar profesor:", e)
            return {
                "status": "error",
                "message": ("Error inesperado al guardar el profesor."),
            }

    def get_all_professors(self):
        self.cursor.execute("SELECT * FROM professor")
        return self.cursor.fetchall()

    def get_professor_by_id(self, professor_id):
        sql = "SELECT * FROM professor WHERE id = %s"
        self.cursor.execute(sql, (professor_id,))
        return self.cursor.fetchone()

    def update_professor(self, professor_id, name, email):
        sql = "UPDATE professor SET name = %s, email = %s WHERE id = %s"
        self.cursor.execute(sql, (name, email, professor_id))
        self.database.commit()

    def delete_professor(self, professor_id):
        self.cursor.execute("DELETE FROM professor WHERE id = %s", (professor_id,))
        self.database.commit()
