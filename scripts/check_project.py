"""Validación mínima y sin dependencias de la estructura de Etapa 0."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
REQUIRED_PATHS = (
    "README.md",
    "AGENTS.md",
    "DECISIONES.md",
    ".gitignore",
    "prompts",
    "src",
    "tests",
    "config",
    "data/input",
    "data/reference",
    "data/sample",
    "output",
    "runs",
    "docs/ARQUITECTURA.md",
    "docs/ESTADO_PROYECTO.md",
)


def main() -> int:
    all_present = True
    for relative_path in REQUIRED_PATHS:
        path = ROOT / relative_path
        if path.exists():
            print(f"[PASS] {relative_path}")
        else:
            print(f"[FAIL] {relative_path}")
            all_present = False
    return 0 if all_present else 1


if __name__ == "__main__":
    sys.exit(main())
