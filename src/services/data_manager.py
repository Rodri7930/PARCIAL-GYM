import json
from pathlib import Path
from typing import List, Dict, Any


class DataManager:
    """Clase encargada de gestionar la persistencia de datos en archivos JSON."""

    def __init__(self, data_folder: str = "data"):
        self.data_folder = Path(data_folder)
        self.data_folder.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, filename: str) -> Path:
        """Genera la ruta completa al archivo JSON."""
        return self.data_folder / f"{filename}.json"

    def save_data(self, filename: str, data: List[Dict[str, Any]]) -> None:
        """Guarda una lista de diccionarios en un archivo JSON."""
        file_path = self._get_file_path(filename)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def load_data(self, filename: str) -> List[Dict[str, Any]]:
        """Carga y devuelve los datos desde un archivo JSON. Retorna [] si no existe o si está vacío."""
        file_path = self._get_file_path(filename)
        if not file_path.exists():
            return []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []