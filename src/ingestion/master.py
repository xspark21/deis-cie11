from pathlib import Path

import polars as pl

BASE_DIR = Path(__file__).resolve().parents[2]
RAW_PATH = BASE_DIR / "data" / "raw" / "LinearizationMiniOutput-MMS-en.xlsx"
OUT_PATH = BASE_DIR / "data" / "processed" / "icd11_master.parquet"

# fastexcel no infiere bien estas columnas cuando vienen casi vacías
_SCHEMA_OVERRIDES = {
    "BrowserLink": pl.String,
    "Grouping1": pl.String,
    "Grouping2": pl.String,
    "Grouping3": pl.String,
    "Grouping4": pl.String,
    "Grouping5": pl.String,
}


def _tabla_capitulos(df: pl.DataFrame) -> pl.DataFrame:
    return (
        df.filter(pl.col("ClassKind") == "chapter")
        .select(
            pl.col("ChapterNo").alias("capitulo"),
            pl.col("Title").alias("nombre_capitulo"),
        )
        .unique()
    )


def procesar_icd11() -> pl.DataFrame | None:
    print(f"procesando tabla maestra desde: {RAW_PATH.name}")

    if not RAW_PATH.exists():
        print(f"✖  no se encontró el archivo en {RAW_PATH}")
        return None

    import sys, os
    stderr = sys.stderr
    sys.stderr = open(os.devnull, "w")
    df = pl.read_excel(RAW_PATH, schema_overrides=_SCHEMA_OVERRIDES)
    sys.stderr.close()
    sys.stderr = stderr
    lut = _tabla_capitulos(df)

    master_df = (
        df.select(
            pl.col("Code").alias("codigo_tallo"),
            pl.col("Title").str.replace(r"^[\-\s]+", "").alias("descripcion"),
            pl.col("Linearization (release) URI").alias("uri_mms"),
            pl.col("Foundation URI").alias("uri_foundation"),
            pl.col("isLeaf").str.to_lowercase().str.contains("true").alias("es_hoja"),
            pl.col("IsResidual").str.to_lowercase().str.contains("true").alias("es_residual"),
            pl.col("ChapterNo").alias("capitulo"),
            pl.col("DepthInKind").cast(pl.UInt8).alias("profundidad"),
        )
        .filter(
            pl.col("codigo_tallo").is_not_null()
            & (pl.col("codigo_tallo").str.strip_chars() != "")
        )
        .join(lut, on="capitulo", how="left")
        .select([
            "codigo_tallo",
            "descripcion",
            "capitulo",
            "nombre_capitulo",
            "profundidad",
            "es_hoja",
            "es_residual",
            "uri_mms",
            "uri_foundation",
        ])
    )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    master_df.write_parquet(OUT_PATH, compression="zstd")

    total = master_df.height
    n_hojas = master_df["es_hoja"].sum()
    n_residual = master_df["es_residual"].sum()
    n_caps = master_df["capitulo"].n_unique()

    print("\ntabla maestra lista\n")
    print(f"  códigos totales : {total:,}")
    print(f"  capítulos       : {n_caps}")
    print(f"  hojas terminales: {n_hojas:,}")
    print(f"  categorías NOS  : {n_residual:,}")

    print(f"\n  -> {OUT_PATH}")
    return master_df


if __name__ == "__main__":
    procesar_icd11()