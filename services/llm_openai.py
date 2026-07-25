"""Servicio LLM: envuelve la llamada al modelo de chat con function calling forzado.

Una sola funcion (`gestionar_requerimiento`) estructura CADA turno del asistente:
devuelve el mensaje para el usuario + los flags de control del loop.
"""

import json

from openai import AzureOpenAI, OpenAI


class LLM:
    def __init__(self, config):
        cfg = config.llm
        self.temperature = cfg.get("temperature", 0.3)
        self.max_tokens = cfg.get("max_tokens", 1200)
        provider = cfg.get("provider", "openai")

        if provider == "azure":
            self.client = AzureOpenAI(
                api_key=config.azure_api_key,
                api_version=cfg.get("api_version"),
                azure_endpoint=config.azure_endpoint,
            )
            # En Azure el "model" es el nombre del deployment
            self.model = cfg.get("deployment", cfg["model"])
        else:
            self.client = OpenAI(api_key=config.openai_api_key)
            self.model = cfg["model"]

    def responder(self, messages: list, tool: dict) -> dict:
        """Llama al modelo forzando el function calling y devuelve los argumentos parseados.

        `tool` es el objeto function (name, description, parameters) cargado del schema.
        El retorno es un dict con `mensaje_al_usuario` + los flags definidos en el schema.
        """
        nombre = tool["name"]
        respuesta = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            tools=[{"type": "function", "function": tool}],
            tool_choice={"type": "function", "function": {"name": nombre}},
        )

        mensaje = respuesta.choices[0].message
        if not mensaje.tool_calls:
            # Fallback defensivo: el modelo no llamo la funcion
            return {"mensaje_al_usuario": mensaje.content or ""}

        return json.loads(mensaje.tool_calls[0].function.arguments)
