"""Carga y expone la parametrizacion del proyecto (config.json + secretos de entorno)."""

import json
import os
from pathlib import Path

from dotenv import load_dotenv


class Config:
    """Lee config.json una sola vez y lo expone al resto del proyecto.

    La logica NO vive aqui: esta clase solo carga y entrega parametros.
    Los secretos (API keys) se leen desde variables de entorno / .env.
    """

    def __init__(self, ruta: str = "config/config.json"):
        load_dotenv()
        self.base_dir = Path(__file__).resolve().parent.parent
        self.ruta = self.base_dir / ruta

        with open(self.ruta, "r", encoding="utf-8") as f:
            self._data = json.load(f)

        # Secretos (nunca en config.json)
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

    # --- acceso generico ---
    def __getitem__(self, key):
        return self._data[key]

    def get(self, key, default=None):
        return self._data.get(key, default)

    def ruta_absoluta(self, ruta_relativa: str) -> Path:
        """Convierte una ruta relativa del config en absoluta respecto a la raiz."""
        return self.base_dir / ruta_relativa

    # --- accesos por seccion (comodidad) ---
    @property
    def app(self) -> dict:
        return self._data["app"]

    @property
    def llm(self) -> dict:
        return self._data["llm"]

    @property
    def whisper(self) -> dict:
        return self._data["whisper"]

    @property
    def prompts(self) -> dict:
        return self._data["prompts"]

    @property
    def data(self) -> dict:
        return self._data["data"]

    @property
    def banco(self) -> dict:
        return self._data["banco"]
