from pydantic import BaseModel, Field


class ClassroomSchema(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=50)
    capacidad: int = Field(..., gt=0)

    class Config:
        json_schema_extra = {"example": {"nombre": "A1", "capacidad": 30}}
