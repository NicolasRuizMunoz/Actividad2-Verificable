from typing import Annotated

from pydantic import Field

SectionNumberType = Annotated[
    str,
    Field(min_length=1, max_length=50, description="Número de sección (VARCHAR 50)"),
]


EvaluationSchemeType = Annotated[
    str,
    Field(
        pattern=r"^(?:percentage|weight)$",
        description="Mecanismo de evaluación: 'percentage' o 'weight'",
    ),
]
