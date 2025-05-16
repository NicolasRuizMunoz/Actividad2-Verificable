from datetime import date

from pydantic import EmailStr, constr

MIN_NAME_LEN = 1
MAX_NAME_LEN = 255
NameType = constr(
    strip_whitespace=True, min_length=MIN_NAME_LEN, max_length=MAX_NAME_LEN
)
EmailType = EmailStr
MinDate = date(1990, 1, 1)
MaxDate = date.today()
