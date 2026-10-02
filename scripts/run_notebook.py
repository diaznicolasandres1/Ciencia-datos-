"""Ejecutar el informe sin red y guardar sus salidas dentro del .ipynb.

Uso desde el repositorio: python scripts/run_notebook.py
"""
from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache/matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / ".cache"))
os.environ.setdefault("JUPYTER_CONFIG_DIR", str(ROOT / ".cache/jupyter/config"))
os.environ.setdefault("JUPYTER_DATA_DIR", str(ROOT / ".cache/jupyter/data"))
os.environ.setdefault("JUPYTER_RUNTIME_DIR", str(ROOT / ".cache/jupyter/runtime"))
os.environ.setdefault("IPYTHONDIR", str(ROOT / ".cache/ipython"))
# El kernel debe usar el mismo entorno que ejecuta este script.
os.environ["PATH"] = str(Path(sys.executable).parent) + os.pathsep + os.environ.get("PATH", "")
os.environ["JUPYTER_PATH"] = str(Path(sys.prefix) / "share/jupyter") + os.pathsep + os.environ.get("JUPYTER_PATH", "")

import nbformat
from nbclient import NotebookClient


def main():
    path = ROOT / "notebooks/01_informe_elecciones.ipynb"
    notebook = nbformat.read(path, as_version=4)
    nbformat.validate(notebook)
    client = NotebookClient(notebook, timeout=180, kernel_name="python3", allow_errors=False,
                            resources={"metadata": {"path": str(ROOT)}})
    client.execute()
    code_cells = [cell for cell in notebook.cells if cell.cell_type == "code"]
    assert all(cell.execution_count is not None for cell in code_cells)
    assert not any(output.output_type == "error" for cell in code_cells for output in cell.outputs)
    nbformat.validate(notebook)
    nbformat.write(notebook, path)
    print(f"Notebook ejecutado: {len(code_cells)} celdas de código, sin errores.")
    print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
