"""Servicio Whisper: speech-to-text.

Por ahora solo va en un sentido: recibe el audio del usuario y devuelve texto.
No genera audio de respuesta (eso queda para una fase posterior).
"""

from openai import OpenAI


class Whisper:
    def __init__(self, config):
        cfg = config.whisper
        self.model = cfg.get("model", "whisper-1")
        self.language = cfg.get("language", "es")
        # Whisper usa el cliente estandar de OpenAI
        self.client = OpenAI(api_key=config.openai_api_key)

    def transcribir(self, ruta_audio: str) -> str:
        """Transcribe un archivo de audio a texto."""
        with open(ruta_audio, "rb") as f:
            respuesta = self.client.audio.transcriptions.create(
                model=self.model,
                file=f,
                language=self.language,
            )
        return respuesta.text
