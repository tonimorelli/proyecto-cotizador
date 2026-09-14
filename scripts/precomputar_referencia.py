"""Precomputa la distribucion etaria desde la referencia corporativa.

Uso:
    python scripts/precomputar_referencia.py

Recorre la referencia una sola vez y deja cache/distribucion_edad.csv.
Falla si la agrupacion de la referencia no coincide con el mapeo declarado.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from cotizador.referencia import precomputar  # noqa: E402

REFERENCIA = pathlib.Path("Referencia/referencia_cartera_corpo_2026_08_28.xlsx")
SALIDA = pathlib.Path("cache/distribucion_edad.csv")


def main() -> int:
    if not REFERENCIA.exists():
        print(f"ERROR: no se encuentra {REFERENCIA}", file=sys.stderr)
        return 1
    resumen = precomputar(REFERENCIA, SALIDA)
    for k, v in resumen.items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
