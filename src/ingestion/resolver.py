import polars as pl
from pathlib import Path
import re

BASE_DIR    = Path(__file__).resolve().parents[2]
MASTER_PATH = BASE_DIR / "data" / "processed" / "icd11_master.parquet"
OUT_PATH    = BASE_DIR / "data" / "processed" / "deis_to_icd11_resolver.parquet"

# OP00 es un sentinel interno, no un código CIE-11
# marca filas operacionales que no representan causas clínicas
_OPERACIONAL = "OP00"


def normalizar_glosa(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\xa0", " ")
    text = re.sub(r"^[ \-.\u00A0]+", "", text)
    text = re.sub(r"\s*\(.*?\)\s*", " ", text)
    text = re.sub(r"\s*[A-Z][0-9][0-9](\.[0-9])?.*$", "", text)
    return text.strip().upper()


_RAW_MAPPINGS = [

    # circulatorio
    ("TOTAL CAUSAS SISTEMA CIRCULATORIO",       "11",    "SISTEMA CIRCULATORIO", "CARDIOVASCULAR",  True,  False),
    ("CAUSAS SISTEMA CIRCULATORIO",             "11",    "SISTEMA CIRCULATORIO", "CARDIOVASCULAR",  True,  False),
    ("Crisis hipertensiva",                     "BA00",  "SISTEMA CIRCULATORIO", "CARDIOVASCULAR",  False, False),
    ("Arritmia grave",                          "BC9Z",  "SISTEMA CIRCULATORIO", "CARDIOVASCULAR",  False, False),
    ("Infarto agudo miocardio",                 "BA41",  "SISTEMA CIRCULATORIO", "CARDIOVASCULAR",  False, False),
    ("Otras causas circulatorias",              "BE2Y",  "SISTEMA CIRCULATORIO", "CARDIOVASCULAR",  False, True),
    # en CIE-11 el ACV pasa al capítulo neurológico (antes era circulatorio)
    ("Accidente vascular encefálico",           "8B20",  "SISTEMA NERVIOSO",     "CARDIOVASCULAR",  False, False),

    # respiratorio
    ("TOTAL CAUSAS SISTEMA RESPIRATORIO",       "12",    "SISTEMA RESPIRATORIO", "RESPIRATORIO",    True,  False),
    ("CAUSAS SISTEMA RESPIRATORIO",             "12",    "SISTEMA RESPIRATORIO", "RESPIRATORIO",    True,  False),
    ("IRA Alta",                                "CA00",  "SISTEMA RESPIRATORIO", "RESPIRATORIO",    False, False),
    # en CIE-11 la influenza pasa al capítulo de infecciosas (antes era respiratorio)
    ("Influenza",                               "1E32",  "SISTEMA RESPIRATORIO", "RESPIRATORIO",    False, False),
    ("Neumonía",                                "CA40",  "SISTEMA RESPIRATORIO", "RESPIRATORIO",    False, False),
    ("Bronquitis/bronquiolitis aguda",          "CA42",  "SISTEMA RESPIRATORIO", "RESPIRATORIO",    False, False),
    ("Crisis obstructiva bronquial",            "CA23",  "SISTEMA RESPIRATORIO", "RESPIRATORIO",    False, False),
    ("Otra causa respiratoria",                 "CA4Z",  "SISTEMA RESPIRATORIO", "RESPIRATORIO",    False, True),
    ("COVID 19 Sospechoso",                     "RA01.1","COVID-19",             "RESPIRATORIO",    False, False),
    ("COVID 19 Confirmado",                     "RA01.0","COVID-19",             "RESPIRATORIO",    False, False),
    ("COVID-19, VIRUS IDENTIFICADO",            "RA01.0","COVID-19",             "RESPIRATORIO",    False, False),
    ("COVID-19, VIRUS NO IDENTIFICADO",         "RA01.1","COVID-19",             "RESPIRATORIO",    False, False),

    # trauma
    ("TOTAL TRAUMATISMOS Y ENVENENAMIENTO",     "22",    "TRAUMA",               "TRAUMA",          True,  False),
    ("TRAUMATISMOS Y ENVENENAMIENTOS",          "22",    "TRAUMA",               "TRAUMA",          True,  False),
    ("Accidentes del tránsito",                 "PA0Z",  "TRAUMA",               "TRAUMA",          False, False),
    ("Otras causas externas",                   "NB9Z",  "TRAUMA",               "TRAUMA",          False, True),
    ("Lesiones autoinfligidas intencionalmente","MB23.S","TRAUMA",               "SALUD MENTAL",    False, False),

    # salud mental
    ("TOTAL CAUSAS DE TRASTORNOS MENTALES",     "06",    "MENTAL",               "SALUD MENTAL",    True,  False),
    ("CAUSAS POR TRASTORNOS MENTALES",          "06",    "MENTAL",               "SALUD MENTAL",    True,  False),
    ("Trastornos mentales y del comportamiento","06",    "MENTAL",               "SALUD MENTAL",    False, False),
    ("Trastornos del Humor",                    "6A6Z",  "MENTAL",               "SALUD MENTAL",    False, False),
    ("Ideación Suicida",                        "MB26.A","MENTAL",               "SALUD MENTAL",    False, False),

    # digestivo
    ("DIARREA AGUDA",                           "1A0Z",  "DIGESTIVO",            "DIGESTIVO",       False, False),

    # otras causas
    ("LAS DEMÁS CAUSAS",                        "MG4Y",  "OTRAS CAUSAS",         "OTROS",           False, True),
    ("TOTAL DEMÁS CAUSAS",                      "21",    "OTRAS CAUSAS",         "OTROS",           True,  True),

    # operacional
    ("TOTAL ATENCIONES DE URGENCIA",            _OPERACIONAL, "OPERACIONAL",     "GESTIÓN",         True,  False),
    ("TOTAL DE HOSPITALIZACIONES",              _OPERACIONAL, "OPERACIONAL",     "GESTIÓN",         True,  False),
    ("TOTAL DEMANDA",                           _OPERACIONAL, "OPERACIONAL",     "GESTIÓN",         True,  False),
    ("CIRUGÍAS DE URGENCIA",                    _OPERACIONAL, "OPERACIONAL",     "GESTIÓN",         True,  False),
    ("Pacientes en espera de hospitalización",  _OPERACIONAL, "OPERACIONAL",     "GESTIÓN",         False, False),

    # variantes del formulario hospitalario — mismas causas con texto distinto según año
    ("SECCIÓN 1. TOTAL ATENCIONES DE URGENCIA",  _OPERACIONAL, "OPERACIONAL",   "GESTIÓN",         True,  False),
    ("SECCIÓN 2. TOTAL DE HOSPITALIZACIONES",    _OPERACIONAL, "OPERACIONAL",   "GESTIÓN",         True,  False),
    ("Pacientes en espera de hospitalización que esperan menos de 12 horas para ser trasladados a cama hospitalaria",
                                                 _OPERACIONAL, "OPERACIONAL",   "GESTIÓN",         False, False),
    ("Trastornos mentales y del comportamiento debidos al uso de sustancias psicoactivas (F10-F19)",
                                                 "6C4Z",       "MENTAL",        "SALUD MENTAL",    False, False),
    ("Trastornos neuróticos, trastornos relacionados con el estrés y trastornos somatomorfos (F40-F48) Incluído el trastorno de pánico (F41.0)",
                                                 "6B0Z",       "MENTAL",        "SALUD MENTAL",    False, False),
    ("Otros trastornos mentales no contenidos en las categorías anteriores",
                                                 "6E8Y",       "MENTAL",        "SALUD MENTAL",    False, True),
    ("Lesiones por Quemaduras, exposición al humo, fuego, llamas, contacto con calor y sustancias calientes (Causa Externa X00-X19)",
                                                 "ND9Z",       "TRAUMA",        "TRAUMA",          False, False),
]


def construir_resolver() -> pl.DataFrame:
    if not MASTER_PATH.exists():
        raise FileNotFoundError(
            f"tabla maestra no encontrada en {MASTER_PATH}\n"
            "ejecuta primero: uv run python src/ingestion/master.py"
        )

    rows = []
    seen_keys = set()
    for item in _RAW_MAPPINGS:
        glosa_original, codigo, grupo_epi, grupo_gest, es_total, es_residual = item
        key = normalizar_glosa(glosa_original)

        if key in seen_keys:
            print(f"   duplicado ignorado: '{glosa_original}'")
            continue
        seen_keys.add(key)

        precision = "Agregada" if es_total else ("Proxy" if es_residual else "Exacta")
        riesgo = "Alto" if codigo in ("1E32", "8B20") else "Bajo"

        rows.append({
            "glosa_norm":           key,
            "glosa_original":       glosa_original,
            "codigo_tallo_cie11":   codigo,
            "grupo_epidemiologico": grupo_epi,
            "grupo_gestion_red":    grupo_gest,
            "es_total":             es_total,
            "es_residual":          es_residual,
            "precision_semantica":  precision,
            "riesgo_quiebre_serie": riesgo,
        })

    resolver_df = pl.DataFrame(rows)
    master = pl.read_parquet(MASTER_PATH)

    resolver = (
        resolver_df
        .join(
            master.select(["codigo_tallo", "descripcion", "nombre_capitulo"]),
            left_on="codigo_tallo_cie11",
            right_on="codigo_tallo",
            how="left",
        )
        .with_columns(
            pl.col("descripcion").fill_null("-").alias("descripcion_cie11"),
            pl.col("nombre_capitulo").fill_null("-")
        )
        .drop("descripcion")
    )

    sin_match = resolver.filter(
        pl.col("nombre_capitulo").is_null() &
        ~pl.col("codigo_tallo_cie11").is_in([_OPERACIONAL, "11", "12", "06", "22", "21"])
    )
    if sin_match.height > 0:
        print(f"\n   códigos sin match en master:")
        for row in sin_match.select(["glosa_original", "codigo_tallo_cie11"]).iter_rows():
            print(f"      {row[1]:<10} ← '{row[0]}'")
    print(f"todos los códigos resueltos.")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    resolver.write_parquet(OUT_PATH, compression="zstd")

    n_exactos   = resolver.filter(pl.col("precision_semantica") == "Exacta").height
    n_agregados = resolver.filter(pl.col("precision_semantica") == "Agregada").height
    n_proxy     = resolver.filter(pl.col("precision_semantica") == "Proxy").height
    n_riesgo    = resolver.filter(pl.col("riesgo_quiebre_serie") == "Alto").height


    print(f"  llaves únicas    : {resolver.height:,}")
    print(f"  exactas          : {n_exactos:,}")
    print(f"  agregadas        : {n_agregados:,}")
    print(f"  proxy            : {n_proxy:,}")
    print(f"  quiebre serie    : {n_riesgo:,}")
    return resolver


if __name__ == "__main__":
    construir_resolver()