// session_id por pestaña: ventana nueva => sesión nueva => historial limpio.
let sessionId = sessionStorage.getItem("session_id");
if (!sessionId) {
  sessionId = crypto.randomUUID();
  sessionStorage.setItem("session_id", sessionId);
}

const chat = document.getElementById("chat");
const input = document.getElementById("input");
const sendBtn = document.getElementById("send");
const micBtn = document.getElementById("mic");
const statusEl = document.getElementById("status");

function addMsg(text, who, tag) {
  const el = document.createElement("div");
  el.className = `msg ${who}`;
  if (tag) {
    const t = document.createElement("span");
    t.className = "tag";
    t.textContent = tag;
    el.appendChild(t);
  }
  el.appendChild(document.createTextNode(text));
  chat.appendChild(el);
  chat.scrollTop = chat.scrollHeight;
  return el;
}

function addTyping() {
  const el = document.createElement("div");
  el.className = "msg bot typing";
  el.innerHTML = "<span></span><span></span><span></span>";
  chat.appendChild(el);
  chat.scrollTop = chat.scrollHeight;
  return el;
}

function setStatus(msg) { statusEl.textContent = msg || ""; }

function pintarRespuesta(data) {
  addMsg(data.respuesta || "(sin respuesta)", "bot");
  const est = data.estado || {};
  if (est.requerimiento_completo) {
    setStatus("✅ Requerimiento completo y validado.");
  } else if (est.fuera_de_scope) {
    setStatus("⚠️ El pedido tiene elementos fuera de alcance.");
  } else {
    setStatus("");
  }
}

async function enviarTexto() {
  const texto = input.value.trim();
  if (!texto) return;
  addMsg(texto, "user");
  input.value = "";
  input.style.height = "auto";
  const typing = addTyping();
  try {
    const r = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, query: texto }),
    });
    const data = await r.json();
    typing.remove();
    pintarRespuesta(data);
  } catch (e) {
    typing.remove();
    setStatus("Error de conexión.");
  }
}

// --- audio (speech-to-text) ---
let mediaRecorder = null;
let chunks = [];

async function toggleGrabacion() {
  if (mediaRecorder && mediaRecorder.state === "recording") {
    mediaRecorder.stop();
    return;
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    chunks = [];
    mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
    mediaRecorder.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      micBtn.classList.remove("recording");
      const blob = new Blob(chunks, { type: "audio/webm" });
      await enviarAudio(blob);
    };
    mediaRecorder.start();
    micBtn.classList.add("recording");
    setStatus("Grabando… toca el micrófono de nuevo para enviar.");
  } catch (e) {
    setStatus("No se pudo acceder al micrófono.");
  }
}

async function enviarAudio(blob) {
  setStatus("Transcribiendo audio…");
  const form = new FormData();
  form.append("session_id", sessionId);
  form.append("audio", blob, "audio.webm");
  const typing = addTyping();
  try {
    const r = await fetch("/chat", { method: "POST", body: form });
    const data = await r.json();
    typing.remove();
    if (data.transcripcion) addMsg(data.transcripcion, "user", "🎤 Tu audio");
    pintarRespuesta(data);
  } catch (e) {
    typing.remove();
    setStatus("Error al procesar el audio.");
  }
}

// --- eventos ---
sendBtn.addEventListener("click", enviarTexto);
input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); enviarTexto(); }
});
input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 150) + "px";
});
micBtn.addEventListener("click", toggleGrabacion);

// saludo inicial del asistente
window.addEventListener("load", () => {
  const typing = addTyping();
  fetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, query: "Hola" }),
  })
    .then((r) => r.json())
    .then((data) => { typing.remove(); pintarRespuesta(data); })
    .catch(() => { typing.remove(); setStatus("No se pudo iniciar la conversación."); });
});
