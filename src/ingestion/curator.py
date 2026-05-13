import polars as pl
from pathlib import Path

BASE_DIR      = Path(__file__).resolve().parents[2]
RAW_DATA_PATH = BASE_DIR / "data" / "raw" / "urgencias_deis_2019_2025.parquet"
RESOLVER_PATH = BASE_DIR / "data" / "processed" / "deis_to_icd11_resolver.parquet"
OUT_PATH      = BASE_DIR / "data" / "processed" / "emergency_care_curated.parquet"


def curar_registros():
    if not RAW_DATA_PATH.exists():
        print(f"no se encontró el dataset en {RAW_DATA_PATH}")
        return

    if not RESOLVER_PATH.exists():
        print(f"resolver no encontrado, ejecuta primero resolver.py")
        return

    resolver = pl.read_parquet(RESOLVER_PATH)
    raw_lazy = pl.scan_parquet(RAW_DATA_PATH)

    # la normalización tiene que ser idéntica a normalize_text en resolver.py
    # se usa replace_all en vez de replace para cubrir glosas con múltiples paréntesis
    norm_expr = (
        pl.col("GlosaCausa")
        .str.replace_all("\u00A0", " ")
        .str.replace_all(r"^[ \-.\u00A0]+", "")
        .str.replace_all(r"\s*\(.*?\)\s*", " ")
        .str.replace_all(r"\s*[A-Z][0-9][0-9](\.[0-9])?.*$", "")
        .str.to_uppercase()
        .str.strip_chars()
        .alias("glosa_norm_key")
    )

    curated_lazy = (
        raw_lazy
        .with_columns(norm_expr)
        .join(
            resolver.lazy(),
            left_on="glosa_norm_key",
            right_on="glosa_norm",
            how="left",
        )
        .drop("glosa_norm_key")
    )

    curated_lazy.sink_parquet(OUT_PATH, compression="zstd")


def verificar_cobertura():
    df    = pl.scan_parquet(OUT_PATH)
    stats = df.select(
        pl.len().alias("total"),
        pl.col("codigo_tallo_cie11").is_null().sum().alias("unmapped"),
    ).collect()

    total    = stats["total"][0]
    unmapped = stats["unmapped"][0]
    mapped   = total - unmapped

    print("curación completada\n")

    print(f"  registros totales : {total:,}")
    print(f"  mapeados          : {mapped:,}")
    print(f"  sin mapear        : {unmapped:,}")
    print(f"  cobertura final   : {mapped / total:.1%}\n")

    print(f"  -> {OUT_PATH}\n")


if __name__ == "__main__":
    curar_registros()
    verificar_cobertura()