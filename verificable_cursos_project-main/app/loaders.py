import json
from pathlib import Path
from typing import Any, Dict, List


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_dataset(data_dir: Path | str) -> Dict[str, List[Dict[str, Any]]]:
    data_dir = Path(data_dir)

    alumnos = read_json(data_dir / "1-alumnos.json")["alumnos"]
    profesores = read_json(data_dir / "2-profesores.json")["profesores"]
    cursos = read_json(data_dir / "3-cursos.json")["cursos"]

    raw_inst = read_json(data_dir / "4-instancias_cursos.json")
    año = raw_inst["año"]
    sem_num = raw_inst["semestre"]
    sem_str = f"{año}-{10 if sem_num == 1 else 20}"
    instancias = [
        {
            **inst,
            "año": año,
            "semestre": sem_str,
        }
        for inst in raw_inst["instancias"]
    ]
    instancia_ids = {inst["id"] for inst in instancias}

    raw_secs = read_json(data_dir / "5-instancia_cursos_con_secciones.json")[
        "secciones"
    ]
    secciones: List[Dict[str, Any]] = []
    for sec in raw_secs:
        inst_id = int(sec["instancia_curso"])
        if inst_id in instancia_ids:
            secciones.append(
                {
                    "id": int(sec["id"]),
                    "instancia_curso": inst_id,
                    "profesor_id": int(sec["profesor_id"]),
                    "evaluacion": sec["evaluacion"],
                }
            )

    raw_asg = read_json(data_dir / "6-alumnos_por_seccion.json")["alumnos_seccion"]
    alumnos_seccion = [
        {
            "alumno_id": int(a["alumno_id"]),
            "seccion_id": int(a["seccion_id"]),
        }
        for a in raw_asg
        if int(a["seccion_id"]) in {s["id"] for s in secciones}
    ]

    raw_notas = read_json(data_dir / "7-notas_alumnos.json")["notas"]
    notas = [
        {
            "alumno_id": int(n["alumno_id"]),
            "evaluation_instance_id": int(n["evaluation_instance_id"]),
            "grade": float(n["grade"]),
        }
        for n in raw_notas
    ]

    return {
        "alumnos": alumnos,
        "profesores": profesores,
        "cursos": cursos,
        "instancias": instancias,
        "secciones": secciones,
        "alumnos_seccion": alumnos_seccion,
        "notas": notas,
    }
