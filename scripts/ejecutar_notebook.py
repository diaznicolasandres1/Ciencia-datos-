"""Ejecuta las celdas de código del notebook con la biblioteca estándar."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "analisis_elecciones_eeuu.ipynb"


def main() -> None:
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    namespace = {"__name__": "__notebook_test__"}
    for number, cell in enumerate(notebook["cells"], start=1):
        if cell["cell_type"] == "code":
            code = "".join(cell["source"])
            exec(compile(code, f"{NOTEBOOK.name}:cell-{number}", "exec"), namespace)
    print("OK: todas las celdas de código se ejecutaron sin errores.")


if __name__ == "__main__":
    main()
