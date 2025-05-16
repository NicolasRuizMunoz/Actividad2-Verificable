CREATE TABLE course (
  id INT AUTO_INCREMENT PRIMARY KEY,
  code VARCHAR(50) NOT NULL UNIQUE,
  description TEXT NOT NULL,
  requisites JSON NOT NULL,
  credits INT NOT NULL,
  closed BOOLEAN NOT NULL DEFAULT FALSE,
  CHECK (credits > 0 AND credits <= 30),
  CHECK (JSON_VALID(requisites)),
  CHECK (CHAR_LENGTH(code) BETWEEN 1 AND 50)
);

CREATE TABLE professor (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  CHECK (CHAR_LENGTH(name) BETWEEN 1 AND 255),
  CHECK (CHAR_LENGTH(email) BETWEEN 5 AND 255),
  CHECK (email REGEXP '^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$')
);

CREATE TABLE course_instance (
  id INT AUTO_INCREMENT PRIMARY KEY,
  course_id INT,
  semester ENUM('01','02') NOT NULL,
  year INT,
  FOREIGN KEY (course_id) REFERENCES course(id) ON DELETE CASCADE,
  UNIQUE (course_id, semester, year)
);

CREATE TABLE section (
  id INT AUTO_INCREMENT PRIMARY KEY,
  course_instance_id INT,
  section_number VARCHAR(50),
  evaluation_scheme ENUM('percentage','weight'),
  FOREIGN KEY (course_instance_id) REFERENCES course_instance(id) ON DELETE CASCADE,
  UNIQUE (course_instance_id, section_number)
);

CREATE TABLE professor_assignment (
  id INT AUTO_INCREMENT PRIMARY KEY,
  professor_id INT,
  course_instance_id INT,
  section_id INT,
  FOREIGN KEY (professor_id) REFERENCES professor(id) ON DELETE CASCADE,
  FOREIGN KEY (course_instance_id) REFERENCES course_instance(id) ON DELETE CASCADE,
  FOREIGN KEY (section_id) REFERENCES section(id) ON DELETE CASCADE,
  UNIQUE (professor_id, course_instance_id, section_id)
);

CREATE TABLE student (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  enrollment_date DATE NOT NULL,
  CHECK (CHAR_LENGTH(name) BETWEEN 1 AND 255),
  CHECK (CHAR_LENGTH(email) BETWEEN 5 AND 255),
  CHECK (email REGEXP '^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$')
);

CREATE TABLE student_assignment (
  id INT AUTO_INCREMENT PRIMARY KEY,
  student_id INT,
  course_instance_id INT,
  section_id INT,
  FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE,
  FOREIGN KEY (course_instance_id) REFERENCES course_instance(id) ON DELETE CASCADE,
  FOREIGN KEY (section_id) REFERENCES section(id) ON DELETE CASCADE,
  UNIQUE (student_id, course_instance_id, section_id)
);

CREATE TABLE evaluation (
  id INT AUTO_INCREMENT PRIMARY KEY,
  course_instance_id INT,
  section_id INT,
  name VARCHAR(255),
  weight FLOAT,
  FOREIGN KEY (course_instance_id) REFERENCES course_instance(id) ON DELETE CASCADE,
  FOREIGN KEY (section_id) REFERENCES section(id) ON DELETE CASCADE,
  UNIQUE (course_instance_id, section_id, name)
);

CREATE TABLE evaluation_instance (
  id INT AUTO_INCREMENT PRIMARY KEY,
  evaluation_id INT,
  name VARCHAR(255),
  weight_type VARCHAR(50),
  weight FLOAT,
  is_optional BOOLEAN,
  FOREIGN KEY (evaluation_id) REFERENCES evaluation(id) ON DELETE CASCADE,
  UNIQUE (evaluation_id, name)
);

CREATE TABLE grade (
  id INT AUTO_INCREMENT PRIMARY KEY,
  student_id INT,
  evaluation_instance_id INT,
  grade FLOAT,
  FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE,
  FOREIGN KEY (evaluation_instance_id) REFERENCES evaluation_instance(id) ON DELETE CASCADE,
  UNIQUE (student_id, evaluation_instance_id)
);

CREATE TABLE classroom (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(50) NOT NULL UNIQUE,
  capacity INT NOT NULL,
  CHECK (capacity > 0),
  CHECK (CHAR_LENGTH(name) BETWEEN 1 AND 50)
);

CREATE TABLE classroom_schedule (
  id INT AUTO_INCREMENT PRIMARY KEY,
  classroom_id INT NOT NULL,
  section_id INT NOT NULL,
  day_of_week ENUM('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday') NOT NULL,
  start_time TIME NOT NULL,
  end_time TIME NOT NULL,
  FOREIGN KEY (classroom_id) REFERENCES classroom(id) ON DELETE CASCADE,
  FOREIGN KEY (section_id) REFERENCES section(id) ON DELETE CASCADE,
  CHECK (start_time >= '09:00:00' AND end_time <= '18:00:00'),
  CHECK (start_time < end_time),
  CHECK ((start_time >= '14:00:00') OR (end_time <= '13:00:00')),
  UNIQUE (classroom_id, day_of_week, start_time, end_time)
);
