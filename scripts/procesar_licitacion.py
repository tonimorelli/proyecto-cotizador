"""Procesa una carpeta de licitacion y escribe el Excel de salida.

Uso:
    python scripts/procesar_licitacion.py "Ejemplos input de cotizaciones/Ejemplo 1" caso_a

Deja el Excel en output/ y la evidencia de la corrida en runs/<caso>/<timestamp>/.
Ninguna de las dos carpetas se commitea.
"""
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from cotizador import agente, pipeline  # noqa: E402

TABLA_ST = pathlib.Path("Referencia/Escenarios_proporcion_ST.xlsx")
CACHE = pathlib.Path("cache/distribucion_edad.csv")


def main(argv) -> int:
    if len(argv) < 3:
        print(__doc__, file=sys.stderr)
        return 2
    carpeta, caso = pathlib.Path(argv[1]), argv[2]
    if not carpeta.is_dir():
        print(f"ERROR: no existe la carpeta {carpeta}", file=sys.stderr)
        return 1
    if not TABLA_ST.exists():
        print(f"ERROR: falta {TABLA_ST}", file=sys.stderr)
        return 1

    sello = time.strftime("%Y%m%d_%H%M%S")
    destino_corrida = pathlib.Path("runs") / caso / sello
    destino_excel = pathlib.Path("output") / f"{caso}_{sello}.xlsx"

    try:
        cliente = agente.ClienteCLI()
        print(f"backend de modelo: CLI, modelo {cliente.modelo}")
    except RuntimeError as exc:
        cliente = None
        print(f"AVISO: sin backend de modelo ({exc}). "
              f"Se corre solo la parte deterministica.", file=sys.stderr)

    m = pipeline.procesar(
        carpeta, nombre_caso=caso, destino_excel=destino_excel,
        destino_corrida=destino_corrida, path_tabla_st=TABLA_ST,
        path_cache=CACHE, cliente=cliente)

    print(f"\ncaso            : {m['caso']}")
    if m.get("sin_poblacion"):
        print("SIN FUENTE DE POBLACION: se emitio el Excel solo con Diagnostico")
        return 0
    print(f"duracion        : {m['duracion_s']} s")
    print(f"fuentes         : {len(m['entradas'])}")
    print(f"poblacion       : {m['poblacion']['personas_en_cartera']:.0f} personas "
          f"en {m['poblacion']['combinaciones_edad_provincia_plan']} combinaciones "
          f"(de {m['poblacion']['filas_leidas']} filas leidas)")
    for esc in ("optimista", "pesimista"):
        c = m["controles"][esc]
        print(f"  {esc:<10} total_licitacion={c['total_licitacion']:.6f}  "
              f"alternativas={c['alternativas_controladas']}")
    comp = m["controles"].get("comparacion_entre_escenarios", {})
    if comp:
        print(f"  comparacion: {comp['combinaciones_comparadas']} combinaciones, "
              f"max dif {comp['maxima_diferencia_absoluta']:.2e}")
    print(f"  coberturas  : {m['salida']['hojas'].get('Coberturas', 0)} filas")
    print(f"modelo          : {m['modelo']}")
    print(f"excel           : {m['salida']['excel']}")
    print(f"corrida         : {destino_corrida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
