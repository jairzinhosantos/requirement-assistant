"""Servicio History: persiste el historial de conversacion por session_id.

Un archivito por sesion en data/history/{session_id}.json, con la lista de
mensajes en el formato que consume el modelo (role / content).
Ventana nueva -> session_id nuevo -> historial limpio (no se acumula).
"""

import json
from pathlib import Path


class History:
    def __init__(self, config):
        self.dir = config.ruta_absoluta(config.data["history_dir"])
        self.dir.mkdir(parents=True, exist_ok=True)

    def _ruta(self, session_id: str) -> Path:
        return self.dir / f"{session_id}.json"

    def existe(self, session_id: str) -> bool:
        return self._ruta(session_id).exists()

    def cargar(self, session_id: str) -> list:
        """Devuelve el historial. Si no existe, crea el archivito vacio."""
        ruta = self._ruta(session_id)
        if not ruta.exists():
            self._guardar_todo(session_id, [])
            return []
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)

    def agregar(self, session_id: str, role: str, content: str) -> list:
        """Anexa un turno (role/content) y persiste."""
        mensajes = self.cargar(session_id)
        mensajes.append({"role": role, "content": content})
        self._guardar_todo(session_id, mensajes)
        return mensajes

    def _guardar_todo(self, session_id: str, mensajes: list) -> None:
        with open(self._ruta(session_id), "w", encoding="utf-8") as f:
            json.dump(mensajes, f, ensure_ascii=False, indent=2)
