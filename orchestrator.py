"""Orquestador: el cerebro del monoagente.

En su constructor carga TODO el config e instancia cada servicio.
En `procesar` corre el flujo de un turno:
  1. Si el input es audio -> Whisper (speech-to-text).
  2. Carga (o crea) el historial de la sesion.
  3. Arma el message = system_prompt + lineamientos + knowledge + historial + query.
  4. Llama al LLM con function calling -> salida estructurada + flags.
  5. Persiste el turno.
  6. Devuelve la respuesta y los flags de control del loop.
"""

import json

from config.config import Config
from services.history import History
from services.llm_openai import LLM
from services.stt_whisper import Whisper


class Orchestrator:
    def __init__(self, config: Config = None):
        self.config = config or Config()

        # --- servicios ---
        self.llm = LLM(self.config)
        self.whisper = Whisper(self.config)
        self.history = History(self.config)

        # --- prompt + function calling ---
        self.system_prompt_tpl = self._leer_texto(self.config.prompts["system_prompt_path"])
        self.tool = self._leer_json(self.config.prompts["function_calling_path"])

        # --- data (lineamientos + conocimiento) ---
        self.lineamientos = self._leer_directorio(self.config.data["compliance_dir"])
        self.knowledge = self._leer_directorio(self.config.data["knowledge_dir"])

        self.banco = self.config.banco["nombre"]

    def procesar(self, session_id: str, query: str = None, audio_path: str = None) -> dict:
        # 1. audio o texto
        transcripcion = None
        if audio_path:
            texto_usuario = self.whisper.transcribir(audio_path)
            transcripcion = texto_usuario
        else:
            texto_usuario = query

        # 2. historial (crea el archivito si es la primera vez)
        historial = self.history.cargar(session_id)

        # 3. arma los messages
        system = self.system_prompt_tpl.format(
            banco=self.banco,
            lineamientos=self.lineamientos or "(sin lineamientos cargados)",
            knowledge=self.knowledge or "(sin conocimiento adicional)",
        )
        messages = (
            [{"role": "system", "content": system}]
            + historial
            + [{"role": "user", "content": texto_usuario}]
        )

        # 4. LLM con function calling (salida estructurada)
        estado = self.llm.responder(messages, self.tool)
        respuesta = estado.get("mensaje_al_usuario", "")

        # 5. persiste el turno
        self.history.agregar(session_id, "user", texto_usuario)
        self.history.agregar(session_id, "assistant", respuesta)

        # 6. devuelve respuesta + flags de control (requerimiento_completo, fuera_de_scope, ...)
        return {
            "session_id": session_id,
            "transcripcion": transcripcion,
            "respuesta": respuesta,
            "estado": estado,
        }

    # --- helpers de carga ---
    def _leer_texto(self, ruta: str) -> str:
        p = self.config.ruta_absoluta(ruta)
        return p.read_text(encoding="utf-8") if p.exists() else ""

    def _leer_json(self, ruta: str) -> dict:
        with open(self.config.ruta_absoluta(ruta), "r", encoding="utf-8") as f:
            return json.load(f)

    def _leer_directorio(self, ruta: str) -> str:
        """Concatena todos los .md de un directorio (lineamientos / knowledge)."""
        p = self.config.ruta_absoluta(ruta)
        if not p.exists():
            return ""
        bloques = []
        for archivo in sorted(p.glob("*.md")):
            bloques.append(f"### {archivo.stem}\n{archivo.read_text(encoding='utf-8')}")
        return "\n\n".join(bloques)
