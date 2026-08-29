const thread = document.getElementById("thread");
const empty = document.getElementById("empty");
const input = document.getElementById("input");
const sendBtn = document.getElementById("send");
const approveBtn = document.getElementById("approve");
const autopilot = document.getElementById("autopilot");
const modelLabel = document.getElementById("model-label");
const hint = document.getElementById("hint");

function cardHtml(card) {
  if (!card) return "";
  const pills = [
    card.location,
    card.severity,
    card.approval,
    card.media_provider && `media: ${card.media_provider}`,
  ]
    .filter(Boolean)
    .map((p) => `<span class="pill ${p === "approved" || p === "ROUTINE" ? "ok" : ""}">${p}</span>`)
    .join("");
  return `<div class="card">
    <h3>${card.story_id || "package"}</h3>
    <div class="meta">${pills}</div>
    <div class="script">${(card.script || card.social_blurb || "").replace(/</g, "")}</div>
    ${card.bundle_dir ? `<p class="hint">Leesa: ${card.bundle_dir}</p>` : ""}
  </div>`;
}

function addMsg(role, text, card) {
  empty?.remove();
  const row = document.createElement("div");
  row.className = `msg ${role}`;
  row.innerHTML = `<div class="bubble">${(text || "").replace(/</g, "")}${cardHtml(card)}</div>`;
  thread.appendChild(row);
  row.scrollIntoView({ behavior: "smooth", block: "end" });
}

function setPending(card) {
  approveBtn.hidden = !card || card.approval === "approved";
}

async function refresh() {
  const res = await fetch("/api/state");
  const data = await res.json();
  autopilot.checked = !!data.autopilot;
  modelLabel.textContent = data.model || "gemini-3.5-flash";
  setPending(data.pending);
}

async function sendTurn(message) {
  sendBtn.disabled = true;
  try {
    const res = await fetch("/api/turn", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, autopilot: autopilot.checked }),
    });
    const data = await res.json();
    const a = data.assistant || {};
    addMsg("assistant", a.text, a.card || data.pending);
    setPending(data.pending);
  } catch (err) {
    addMsg("assistant", `Desk error: ${err}`);
  } finally {
    sendBtn.disabled = false;
  }
}

sendBtn.addEventListener("click", () => {
  const text = input.value.trim();
  if (!text) return;
  addMsg("user", text);
  input.value = "";
  sendTurn(text);
});

input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendBtn.click();
  }
});

approveBtn.addEventListener("click", async () => {
  approveBtn.disabled = true;
  try {
    const res = await fetch("/api/approve", { method: "POST" });
    const data = await res.json();
    const a = data.assistant || {};
    addMsg("assistant", a.text || "Approved.", a.card);
    setPending(data.pending);
  } finally {
    approveBtn.disabled = false;
  }
});

autopilot.addEventListener("change", async () => {
  await fetch("/api/settings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ autopilot: autopilot.checked }),
  });
  hint.textContent = autopilot.checked
    ? "Autopilot on: WFAD runs Watch → Story. It will not send to Leesa until you approve."
    : "Autopilot off: still Gemini NLU, same tools. Ask explicitly to draft a package.";
});

refresh();
