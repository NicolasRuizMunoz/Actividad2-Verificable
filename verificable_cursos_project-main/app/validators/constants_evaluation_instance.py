from typing import Annotated

from pydantic import Field

NameType = Annotated[
    str,
    Field(
        min_length=1,
        max_length=255,
        description="Nombre de la instancia de evaluación (VARCHAR 255)",
    ),
]

WeightTypeType = Annotated[
    str,
    Field(
        pattern=r"^(percentage|weight)$",
        description="Tipo de ponderación: 'percentage' o 'weight'",
    ),
]

WeightValueType = Annotated[
    float, Field(ge=0, description="Valor de la instancia de evaluación")
]

IsOptionalType = Annotated[
    bool, Field(description="Indica si la instancia es opcional")
]
