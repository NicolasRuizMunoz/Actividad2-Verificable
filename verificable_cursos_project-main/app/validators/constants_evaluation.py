from typing import Annotated

from pydantic import Field

NameType = Annotated[
    str, Field(min_length=1, max_length=255, description="Nombre de la evaluación")
]

WeightType = Annotated[
    str,
    Field(
        pattern=r"^(?:percentage|weight)$",
        description="Tipo de ponderación: 'percentage' o 'weight'",
    ),
]

WeightValue = Annotated[
    float, Field(gt=0, description="Valor del peso de la evaluación (debe ser > 0)")
]
