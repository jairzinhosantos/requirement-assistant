"""Endpoint Flask. Su unico trabajo: traer de la web {session_id, query|audio}
y derivarlo al orquestador. No carga config ni logica de negocio.
"""

import os
import tempfile

from flask import Flask, jsonify, render_template, request

from config.config import Config
from orchestrator import Orchestrator

config = Config()
orquestador = Orchestrator(config)

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html", banco=orquestador.banco)


@app.route("/chat", methods=["POST"])
def chat():
    # Caso 1: audio (multipart/form-data)
    if "audio" in request.files:
        session_id = request.form.get("session_id")
        audio = request.files["audio"]
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            audio.save(tmp.name)
            ruta = tmp.name
        try:
            resultado = orquestador.procesar(session_id, audio_path=ruta)
        finally:
            os.unlink(ruta)
    # Caso 2: texto (JSON)
    else:
        datos = request.get_json(force=True)
        session_id = datos.get("session_id")
        query = datos.get("query")
        resultado = orquestador.procesar(session_id, query=query)

    return jsonify(resultado)


if __name__ == "__main__":
    cfg = config.app
    app.run(
        host=cfg.get("host", "127.0.0.1"),
        port=cfg.get("port", 5000),
        debug=cfg.get("debug", True),
    )
