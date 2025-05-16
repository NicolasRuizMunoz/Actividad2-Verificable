from collections import defaultdict
from datetime import datetime, time
from typing import Optional

import pandas as pd

from db import DatabaseConnection


class SchedulingManager:
    START_TIME = time(9, 0)  # 9:00
    END_TIME = time(18, 0)  # 18:00
    LUNCH_START = time(13, 0)  # 13:00
    LUNCH_END = time(14, 0)  # 14:00
    DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    TIME_SLOTS = [
        time(9, 0),
        time(10, 0),
        time(11, 0),
        time(12, 0),  # Morning
        time(14, 0),
        time(15, 0),
        time(16, 0),
        time(17, 0),  # Afternoon
    ]

    def __init__(self):
        self.db = DatabaseConnection()
        self.cur = self.db.connect()
        self.classroom_schedule: dict[int, list[tuple[str, time, time]]] = {}
        self.professor_schedule: dict[int, list[tuple[str, time, time]]] = {}
        self.student_schedule: dict[int, list[tuple[str, time, time]]] = {}
        self.section_schedule: dict[int, dict] = {}

    def clear_schedule(self):
        self.cur.execute("DELETE FROM classroom_schedule")
        self.db.commit()
        self.classroom_schedule.clear()
        self.professor_schedule.clear()
        self.student_schedule.clear()
        self.section_schedule.clear()

    def get_all_sections(self) -> list[dict]:
        self.cur.execute(
            """
            SELECT
                s.id as section_id,
                c.credits,
                pa.professor_id,
                c.code,
                s.section_number,
                c.id as course_id
            FROM section s
            JOIN course_instance ci ON s.course_instance_id = ci.id
            JOIN course c ON ci.course_id = c.id
            JOIN professor_assignment pa ON s.id = pa.section_id
            ORDER BY c.credits DESC
        """
        )
        sections = self.cur.fetchall()
        return sections

    def get_suitable_classrooms(
        self, section_id: int, student_count: int
    ) -> list[dict]:
        try:
            self.cur.execute(
                """
                SELECT c.credits
                FROM section s
                JOIN course_instance ci ON s.course_instance_id = ci.id
                JOIN course c ON ci.course_id = c.id
                WHERE s.id = %s
            """,
                (section_id,),
            )
            credits = self.cur.fetchone()["credits"]

            self.cur.execute(
                """
                SELECT id, capacity
                FROM classroom
                WHERE capacity >= %s
                ORDER BY capacity ASC
            """,
                (student_count,),
            )

            classrooms = []
            for room in self.cur.fetchall():
                # Calculate fit score - lower is better
                capacity_diff = room["capacity"] - student_count
                usage_count = len(self.classroom_schedule.get(room["id"], []))

                # For 2-credit courses, prefer smaller rooms
                if credits == 2:
                    fit_score = capacity_diff * 2 + usage_count
                else:
                    fit_score = capacity_diff + usage_count

                classrooms.append(
                    {
                        "id": room["id"],
                        "capacity": room["capacity"],
                        "fit_score": fit_score,
                    }
                )

            # Sort by fit score
            classrooms.sort(key=lambda x: x["fit_score"])
            return classrooms

        except Exception as e:
            print(f"Error getting suitable classrooms: {str(e)}")
            return []

    def get_available_classrooms(self) -> list[dict]:
        self.cur.execute(
            "SELECT id, name, capacity FROM classroom ORDER BY capacity DESC"
        )
        classrooms = self.cur.fetchall()
        return classrooms

    def get_time_slot_score(
        self, day: str, start_time: time, end_time: time, classroom_id: int
    ) -> int:
        try:
            score = 0
            if classroom_id in self.classroom_schedule:
                for slot_day, slot_start, slot_end in self.classroom_schedule[
                    classroom_id
                ]:
                    if slot_day == day:
                        if slot_end == start_time or slot_start == end_time:
                            score -= 2
                        elif abs((slot_end.hour - start_time.hour)) == 2:
                            score += 1
                        elif abs((slot_end.hour - start_time.hour)) > 2:
                            score += 2

            if start_time.hour >= 14:
                score += 1

            return score
        except Exception:
            return 999

    def find_valid_time_slot(
        self, section_id: int, classroom_id: int, professor_id: int, credits: int
    ) -> Optional[tuple[str, time, time]]:
        if credits == 2:
            time_slots = [
                time(9),
                time(10),
                time(11),
                time(14),
                time(15),
                time(16),
            ]
        else:
            time_slots = [
                time(9),
                time(10),
                time(14),
                time(15),
            ]

        day_usage = defaultdict(int)
        for schedules in [
            self.classroom_schedule.values(),
            self.professor_schedule.values(),
        ]:
            for schedule in schedules:
                for day, _, _ in schedule:
                    day_usage[day] += 1

        sorted_days = sorted(self.DAYS, key=lambda d: day_usage[d])

        for day in sorted_days:
            for start_time in time_slots:
                end_hour = start_time.hour + credits
                if end_hour > 18:
                    continue

                end_time = time(end_hour)

                if (
                    self.is_valid_time_slot(start_time, end_time, credits)
                    and not self.has_classroom_conflict(
                        classroom_id, day, start_time, end_time
                    )
                    and not self.has_professor_conflict(
                        professor_id, day, start_time, end_time
                    )
                    and not self.has_student_conflicts(
                        section_id, day, start_time, end_time
                    )
                ):
                    return day, start_time, end_time

        return None

    def generate_schedule(self) -> bool:
        try:
            self.classroom_schedule.clear()
            self.professor_schedule.clear()
            self.student_schedule.clear()
            self.section_schedule.clear()

            sections = self.get_all_sections()
            if not sections:
                return False

            for section in sections:
                self.cur.execute(
                    """
                    SELECT
                        COUNT(*) as student_count,
                        GROUP_CONCAT(student_id) as student_ids
                    FROM student_assignment
                    WHERE section_id = %s
                    GROUP BY section_id
                """,
                    (section["section_id"],),
                )
                result = self.cur.fetchone()
                section["student_count"] = result["student_count"] if result else 0
                section["student_ids"] = (
                    [int(x) for x in result["student_ids"].split(",")]
                    if result and result["student_ids"]
                    else []
                )

                section["conflict_score"] = self.get_conflict_score(
                    section["section_id"]
                )
                possible_slots = 0
                for classroom in self.get_suitable_classrooms(
                    section["section_id"], section["student_count"]
                ):
                    for day in self.DAYS:
                        for hour in range(9, 18 - section["credits"]):
                            if hour != 13:  # Skip lunch hour
                                start_time = time(hour, 0)
                                end_time = time(hour + section["credits"], 0)
                                if not self.has_professor_conflict(
                                    section["professor_id"], day, start_time, end_time
                                ):
                                    possible_slots += 1

                section["flexibility_score"] = possible_slots

            # Sort sections by:
            # 1. Flexibility score (lower first - schedule less flexible sections first)
            # 2. Conflict score (higher first - schedule sections with more conflicts first)
            # 3. Credits (higher first)
            # 4. Student count (higher first)
            sections.sort(
                key=lambda x: (
                    x["flexibility_score"],
                    -x["conflict_score"],
                    -x["credits"],
                    -x["student_count"],
                )
            )

            unscheduled_sections = []
            for section in sections:
                try:
                    scheduled = False
                    student_ids = section["student_ids"]

                    suitable_classrooms = self.get_suitable_classrooms(
                        section["section_id"], section["student_count"]
                    )
                    if not suitable_classrooms:
                        unscheduled_sections.append(section)
                        continue

                    for classroom in suitable_classrooms:
                        try:
                            classroom_id = classroom["id"]

                            time_slot = self.find_valid_time_slot(
                                section["section_id"],
                                classroom_id,
                                section["professor_id"],
                                section["credits"],
                            )

                            if time_slot:
                                day, start_time, end_time = time_slot
                                self.schedule_section(
                                    section["section_id"],
                                    classroom_id,
                                    section["professor_id"],
                                    student_ids,
                                    day,
                                    start_time,
                                    end_time,
                                )
                                scheduled = True
                                break
                        except Exception as e:
                            print(f"Error with classroom {classroom_id}: {str(e)}")
                            continue

                    if not scheduled:
                        unscheduled_sections.append(section)
                except Exception as e:
                    print(f"Error with section {section['section_id']}: {str(e)}")
                    continue

            if unscheduled_sections:
                return False

            return True
        except Exception:
            import traceback

            traceback.print_exc()
            return False

    def export_to_excel(self, filename: str = "horario.xlsx") -> None:
        self.cur.execute(
            """
            SELECT
                c.code,
                c.description as course_name,
                s.section_number,
                cr.name as classroom,
                cs.day_of_week,
                cs.start_time,
                cs.end_time,
                p.name as professor
            FROM classroom_schedule cs
            JOIN section s ON cs.section_id = s.id
            JOIN course_instance ci ON s.course_instance_id = ci.id
            JOIN course c ON ci.course_id = c.id
            JOIN classroom cr ON cs.classroom_id = cr.id
            JOIN professor_assignment pa ON s.id = pa.section_id
            JOIN professor p ON pa.professor_id = p.id
            ORDER BY cs.day_of_week, cs.start_time
        """
        )

        schedule_data = []
        results = self.cur.fetchall()
        if not results:
            return

        for row in results:
            schedule_data.append(
                {
                    "Day": row["day_of_week"],
                    "Time": f"{row['start_time']} - {row['end_time']}",
                    "Course": f"{row['code']} - {row['course_name']} (Sección {row['section_number']})",
                    "Classroom": row["classroom"],
                    "Professor": row["professor"],
                }
            )

        df = pd.DataFrame(schedule_data)

        with pd.ExcelWriter(filename, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Horario")

            workbook = writer.book
            worksheet = writer.sheets["Horario"]

            # Set column widths - increased width for Course column
            column_widths = {
                "A": 12,  # Day
                "B": 20,  # Time
                "C": 50,  # Course (increased to accommodate full name)
                "D": 15,  # Classroom
                "E": 25,  # Professor
            }

            for col, width in column_widths.items():
                worksheet.set_column(f"{col}:{col}", width)

            header_format = workbook.add_format(
                {
                    "bold": True,
                    "text_wrap": True,
                    "valign": "top",
                    "fg_color": "#D7E4BC",
                    "border": 1,
                }
            )

            cell_format = workbook.add_format(
                {"text_wrap": True, "valign": "top", "border": 1}
            )
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)

            for row_num, row in enumerate(df.values, 1):
                for col_num, value in enumerate(row):
                    worksheet.write(row_num, col_num, value, cell_format)
            worksheet.set_row(0, 30)
            for row in range(1, len(df) + 1):
                worksheet.set_row(row, 45)

    def is_valid_time_slot(
        self, start_time: time, end_time: time, credits: int
    ) -> bool:
        if start_time < self.START_TIME or end_time > self.END_TIME:
            return False

        if not (end_time <= self.LUNCH_START or start_time >= self.LUNCH_END):
            return False

        duration = datetime.combine(datetime.today(), end_time) - datetime.combine(
            datetime.today(), start_time
        )
        if duration.seconds / 3600 != credits:
            return False

        return True

    def has_classroom_conflict(
        self, classroom_id: int, day: str, start_time: time, end_time: time
    ) -> bool:
        if classroom_id not in self.classroom_schedule:
            return False

        for slot in self.classroom_schedule[classroom_id]:
            if slot[0] == day:
                slot_start = slot[1]
                slot_end = slot[2]
                if start_time < slot_end and end_time > slot_start:
                    return True
        return False

    def has_professor_conflict(
        self, professor_id: int, day: str, start_time: time, end_time: time
    ) -> bool:
        if professor_id not in self.professor_schedule:
            return False

        for slot in self.professor_schedule[professor_id]:
            if slot[0] == day:
                slot_start = slot[1]
                slot_end = slot[2]
                if start_time < slot_end and end_time > slot_start:
                    return True
        return False

    def has_student_conflicts(
        self, section_id: int, day: str, start_time: time, end_time: time
    ) -> bool:
        try:
            self.cur.execute(
                """
                SELECT student_id, c.credits
                FROM student_assignment sa
                JOIN section s ON sa.section_id = s.id
                JOIN course_instance ci ON s.course_instance_id = ci.id
                JOIN course c ON ci.course_id = c.id
                WHERE section_id = %s
            """,
                (section_id,),
            )

            student_info = self.cur.fetchall()
            if not student_info:
                return False

            student_ids = [s["student_id"] for s in student_info]
            credits = student_info[0]["credits"] if student_info else 3

            # For 2-credit courses, we can be more lenient with conflicts
            conflict_threshold = 0.7 if credits == 2 else 0.5

            conflicts = 0
            total_students = len(student_ids)
            for student_id in student_ids:
                if student_id in self.student_schedule:
                    for (
                        scheduled_day,
                        scheduled_start,
                        scheduled_end,
                    ) in self.student_schedule[student_id]:
                        if scheduled_day == day and not (
                            end_time <= scheduled_start or start_time >= scheduled_end
                        ):
                            conflicts += 1
                            break

            conflict_ratio = conflicts / total_students if total_students > 0 else 0
            return conflict_ratio > conflict_threshold

        except Exception as e:
            print(f"Error checking student conflicts: {str(e)}")
            return False

    def get_conflict_score(self, section_id: int) -> int:
        """Calculate a conflict score for a section based on student overlaps.
        Higher scores mean more potential conflicts."""
        try:
            self.cur.execute(
                """
                SELECT c.credits
                FROM section s
                JOIN course_instance ci ON s.course_instance_id = ci.id
                JOIN course c ON ci.course_id = c.id
                WHERE s.id = %s
            """,
                (section_id,),
            )
            credits = self.cur.fetchone()["credits"]

            self.cur.execute(
                """
                WITH section_students AS (
                    SELECT student_id 
                    FROM student_assignment 
                    WHERE section_id = %s
                )
                SELECT 
                    COUNT(DISTINCT sa.student_id) as overlap_count
                FROM section_students ss
                JOIN student_assignment sa ON sa.student_id = ss.student_id
                WHERE sa.section_id != %s
                GROUP BY sa.section_id
                ORDER BY overlap_count DESC
                LIMIT 1
            """,
                (section_id, section_id),
            )

            result = self.cur.fetchone()
            overlap_count = result["overlap_count"] if result else 0

            # Prioritize 2-credit courses by giving them a lower score
            if credits == 2:
                return overlap_count * 0.8  # 20% lower score for 2-credit courses
            return overlap_count

        except Exception as e:
            print(f"Error calculating conflict score: {str(e)}")
            return 0

    def get_classroom_capacity(self, classroom_id: int) -> int:
        self.cur.execute(
            "SELECT capacity FROM classroom WHERE id = %s", (classroom_id,)
        )
        result = self.cur.fetchone()
        return result["capacity"] if result else 0

    def get_section_enrollment_count(self, section_id: int) -> int:
        self.cur.execute(
            "SELECT COUNT(*) as count FROM student_assignment WHERE section_id = %s",
            (section_id,),
        )
        result = self.cur.fetchone()
        return result["count"] if result else 0

    def schedule_section(
        self,
        section_id: int,
        classroom_id: int,
        professor_id: int,
        student_ids: list[int],
        day: str,
        start_time: time,
        end_time: time,
    ) -> bool:
        try:
            if classroom_id not in self.classroom_schedule:
                self.classroom_schedule[classroom_id] = []
            self.classroom_schedule[classroom_id].append((day, start_time, end_time))

            if professor_id not in self.professor_schedule:
                self.professor_schedule[professor_id] = []
            self.professor_schedule[professor_id].append((day, start_time, end_time))
            for student_id in student_ids:
                if student_id not in self.student_schedule:
                    self.student_schedule[student_id] = []
                self.student_schedule[student_id].append((day, start_time, end_time))

            self.section_schedule[section_id] = {
                "classroom_id": classroom_id,
                "professor_id": professor_id,
                "day": day,
                "start_time": start_time,
                "end_time": end_time,
            }

            self.cur.execute(
                """
                INSERT INTO classroom_schedule (section_id, classroom_id, day_of_week, start_time, end_time)
                VALUES (%s, %s, %s, %s, %s)
            """,
                (section_id, classroom_id, day, start_time, end_time),
            )

            self.db.commit()
            return True

        except Exception as e:
            print(f"Error scheduling section: {str(e)}")
            self.db.rollback()

            if classroom_id in self.classroom_schedule:
                self.classroom_schedule[classroom_id].pop()
            if professor_id in self.professor_schedule:
                self.professor_schedule[professor_id].pop()
            for student_id in student_ids:
                if student_id in self.student_schedule:
                    self.student_schedule[student_id].pop()
            if section_id in self.section_schedule:
                del self.section_schedule[section_id]

            return False

    def _check_conflicts(
        self,
        day: str,
        start_time: time,
        end_time: time,
        classroom_id: int,
        professor_id: int,
        student_ids: list[int],
    ) -> bool:
        if self.has_classroom_conflict(classroom_id, day, start_time, end_time):
            return True
        if self.has_professor_conflict(professor_id, day, start_time, end_time):
            return True
        if self.has_student_conflicts(student_ids, day, start_time, end_time):
            return True

        return False
