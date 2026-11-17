const SAMPLE_QUESTIONS = [
  "What is the project name?",
  "Which vector store is used?",
  "How do you run offline tests?",
];

const messagesEl = document.getElementById("messages");
const askForm = document.getElementById("askForm");
const questionInput = document.getElementById("question");
const submitBtn = document.getElementById("submitBtn");
const samplesEl = document.getElementById("samples");
const indexPill = document.getElementById("indexPill");
const statsMeta = document.getElementById("statsMeta");
const detail = document.getElementById("detail");
const sourceList = document.getElementById("sourceList");
const metaFoot = document.getElementById("metaFoot");

function addBubble(text, role) {
  const el = document.createElement("div");
  el.className = `bubble ${role}`;
  el.textContent = text;
  messagesEl.appendChild(el);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return el;
}

function renderSamples() {
  SAMPLE_QUESTIONS.forEach((q) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = q;
    btn.addEventListener("click", () => {
      questionInput.value = q;
      questionInput.focus();
    });
    samplesEl.appendChild(btn);
  });
}

async function refreshStatus() {
  try {
    const [health, stats] = await Promise.all([
      fetch("/health").then((r) => r.json()),
      fetch("/v1/stats").then((r) => r.json()),
    ]);
    const ready = health.index_ready;
    indexPill.textContent = ready ? "Index: ready" : "Index: not ready";
    indexPill.classList.toggle("warn", !ready);
    statsMeta.textContent = ready
      ? `${stats.document_count} docs · ${stats.chunk_count} chunks · v${health.version}`
      : "Run make seed-offline or make ingest";
  } catch {
    indexPill.textContent = "API: unreachable";
    indexPill.classList.add("warn");
    statsMeta.textContent = "";
  }
}

function renderSources(sources, usage, latencyMs, requestId) {
  sourceList.innerHTML = "";
  if (!sources || sources.length === 0) {
    detail.hidden = true;
    return;
  }
  detail.hidden = false;
  sources.forEach((s) => {
    const li = document.createElement("li");
    li.innerHTML = `<span class="src-name">${escapeHtml(s.source)} · score ${s.score}</span>
      <span class="snippet">${escapeHtml(s.snippet)}</span>`;
    sourceList.appendChild(li);
  });
  const tokens = usage?.total_tokens ?? 0;
  metaFoot.textContent = `${latencyMs?.toFixed?.(1) ?? latencyMs} ms · ${tokens} tokens · ${requestId}`;
}

function escapeHtml(str) {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

askForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = questionInput.value.trim();
  if (!question) return;

  addBubble(question, "user");
  questionInput.value = "";
  submitBtn.disabled = true;

  const pending = addBubble("Thinking…", "assistant muted");

  try {
    const response = await fetch("/v1/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const body = await response.json().catch(() => ({}));
    pending.remove();

    if (!response.ok) {
      const msg = body.detail || `Request failed (${response.status})`;
      addBubble(msg, "error");
      detail.hidden = true;
      return;
    }

    addBubble(body.answer, "assistant");
    renderSources(body.sources, body.usage, body.latency_ms, body.request_id);
  } catch (err) {
    pending.remove();
    addBubble(err.message || "Network error", "error");
    detail.hidden = true;
  } finally {
    submitBtn.disabled = false;
    questionInput.focus();
  }
});

addBubble(
  "Welcome. Ask a question about the documents in the index. Use the chips below for examples.",
  "muted",
);
renderSamples();
refreshStatus();