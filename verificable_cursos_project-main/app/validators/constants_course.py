from pydantic import conint, constr

COURSE_CODE_REGEX = r"^[A-Z]{3}\d{4}$"
MAX_COURSE_CODE_LEN = 50
MAX_DESC_LEN = 2000
MIN_CREDITS = 1
MAX_CREDITS = 30

CourseCode = constr(
    strip_whitespace=True,
    min_length=1,
    max_length=MAX_COURSE_CODE_LEN,
    pattern=COURSE_CODE_REGEX,
)
Description = constr(
    strip_whitespace=True,
    min_length=1,
    max_length=MAX_DESC_LEN,
)
RequisiteCode = CourseCode
Credits = conint(ge=MIN_CREDITS, le=MAX_CREDITS)
