from datetime import date
from typing import Annotated

from pydantic import Field

SemesterType = Annotated[
    str,
    Field(
        min_length=2,
        max_length=2,
        pattern=r"^(?:01|02)$",
        description="Semestre: '01' (primer semestre) o '02' (segundo semestre)",
    ),
]

YearType = Annotated[
    int,
    Field(
        ge=1900,
        le=date.today().year,
        description="Año de la instancia (no puede exceder el año actual)",
    ),
]
