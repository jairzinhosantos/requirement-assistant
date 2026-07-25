# Nera — Asistente de Requerimientos (Banco AInerdd)

**Nera** es un prototipo de asistente conversacional (texto + voz→texto) que ayuda a
usuarios de negocio sin perfil técnico a aterrizar y validar requerimientos de soluciones
de IA, contrastándolos contra los lineamientos del banco.

Monoagente sobre **Flask**, con parametrización por `config`, orquestador central y
servicios desacoplados (LLM, Whisper, historial). Frontend embebido.

## Arquitectura

```
app.py            Endpoint Flask. Recibe {session_id, query|audio} y deriva al orquestador.
orchestrator.py   Carga el config, instancia servicios y corre el loop de elicitación.
config/
  config.json     Toda la parametrización (modelo, deployment, rutas, etc.).
  config.py       Clase Config: carga config.json + secretos de entorno.
services/
  llm_openai.py   Clase LLM (chat + function calling forzado = output structure).
  stt_whisper.py  Clase Whisper (speech-to-text).
  history.py      Clase History (historial por session_id en data/history).
prompts/
  system_prompt.md
  function_calling/gestionar_requerimiento.json   Schema que controla el loop.
data/
  compliance/     Lineamientos del banco (qué se puede / qué no).
  knowledge/      Conocimiento adicional para el modelo.
  history/        Un JSON por sesión.
templates/ static/  Frontend embebido (HTML/CSS/JS).
```

## Flujo de un turno
1. `app.py` recibe `session_id` + `query` (texto) o `audio`.
2. El orquestador: si es audio → Whisper lo transcribe.
3. Carga (o crea) el historial de esa sesión.
4. Arma `system_prompt + lineamientos + knowledge + historial + query`.
5. Llama al LLM con function calling → salida estructurada con flags.
6. Persiste el turno y devuelve respuesta + flags (`requerimiento_completo`, `fuera_de_scope`, …).

## Puesta en marcha
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # completa OPENAI_API_KEY
python app.py             # http://127.0.0.1:5000
```

## Alcance actual (lineamientos)
Casos permitidos: asistentes virtuales de IA, clasificadores de correos y asistentes de
voz por WhatsApp/Teams, sobre datos no estructurados (PDFs). La conexión a datos
transaccionales por API queda **fuera de alcance** (fase 2027).
