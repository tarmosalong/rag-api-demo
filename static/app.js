const SAMPLE_QUESTIONS = [
  "What is the project name?",
  "Which vector store is used?",
  "What does the Growth plan cost?",
  "How long is the trial?",
  "Where is customer data stored?",
];

const messagesEl = document.getElementById("messages");
const askForm = document.getElementById("askForm");
const questionInput = document.getElementById("question");
const submitBtn = document.getElementById("submitBtn");
const samplesEl = document.getElementById("samples");
const indexPill = document.getElementById("indexPill");
const statsMeta = document.getElementById("statsMeta");
const sourcesSection = document.getElementById("sourcesSection");
const sourceList = document.getElementById("sourceList");
const metaFoot = document.getElementById("metaFoot");
const fileInput = document.getElementById("fileInput");
const uploadBtn = document.getElementById("uploadBtn");
const uploadStatus = document.getElementById("uploadStatus");

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
      : "Indexing data/raw on startup when RAG_OFFLINE=1";
  } catch {
    indexPill.textContent = "API: unreachable";
    indexPill.classList.add("warn");
    statsMeta.textContent = "";
  }
}

function renderSources(sources, usage, latencyMs, requestId) {
  sourceList.innerHTML = "";
  if (!sources || sources.length === 0) {
    sourcesSection.hidden = true;
    return;
  }
  sourcesSection.hidden = false;
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

function setUploadStatus(message, isError = false) {
  uploadStatus.hidden = !message;
  uploadStatus.textContent = message || "";
  uploadStatus.classList.toggle("error", isError);
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
      sourcesSection.hidden = true;
      return;
    }

    addBubble(body.answer, "assistant");
    renderSources(body.sources, body.usage, body.latency_ms, body.request_id);
    await refreshStatus();
  } catch (err) {
    pending.remove();
    addBubble(err.message || "Network error", "error");
    sourcesSection.hidden = true;
  } finally {
    submitBtn.disabled = false;
    questionInput.focus();
  }
});

uploadBtn.addEventListener("click", async () => {
  const file = fileInput.files?.[0];
  if (!file) {
    setUploadStatus("Choose a .md or .txt file first.", true);
    return;
  }

  uploadBtn.disabled = true;
  setUploadStatus("Uploading…");

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch("/v1/upload", { method: "POST", body: formData });
    const body = await response.json().catch(() => ({}));

    if (!response.ok) {
      setUploadStatus(body.detail || `Upload failed (${response.status})`, true);
      return;
    }

    setUploadStatus(`Indexed ${body.source} (${body.chunk_count} chunks).`);
    fileInput.value = "";
    addBubble(
      `Added ${body.source} to the index (${body.chunk_count} chunks). You can ask about it now.`,
      "muted",
    );
    await refreshStatus();
  } catch (err) {
    setUploadStatus(err.message || "Upload failed", true);
  } finally {
    uploadBtn.disabled = false;
  }
});

addBubble(
  "Welcome. Ask about documents in the index, or upload a .md/.txt file on the right.",
  "muted",
);
renderSamples();
refreshStatus();