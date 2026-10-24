/* mobile/assets/app.js */

const SAMPLES = {
  conflict_recon: `Alice: Why didn't you inform me about the sudden project deadline change?
Bob: I was overwhelmed with client meetings all morning, I didn't mean to keep you in the dark.
Alice: It completely ruined my afternoon schedule and I had to cancel personal plans.
Bob: I sincerely apologize for that. That was totally my fault, I should have texted earlier.
Alice: Thank you for acknowledging it. Let's make sure we sync on Slack every morning.
Bob: Absolutely. I'll take care of the final client deck so you don't have to work late.
Alice: That's very helpful, thank you so much! I appreciate your support.`,

  whatsapp_incident: `[10/24/24, 09:15:10 AM] Jordan: Hey team, did anyone check the deployment server logs?
[10/24/24, 09:16:02 AM] Morgan: Looking at them now. Database connection pool got exhausted.
[10/24/24, 09:17:40 AM] Jordan: This is terrible, we have customers waiting right now.
[10/24/24, 09:19:15 AM] Morgan: Don't panic, I found the leaked connection and patched it.
[10/24/24, 09:20:00 AM] Jordan: Wait, is the site back up?
[10/24/24, 09:21:20 AM] Morgan: Yes! All health checks are green and latency is under 40ms.
[10/24/24, 09:22:05 AM] Jordan: Awesome job Morgan! That was super fast. Great relief!`,

  meld_friends: `Ross: Hi.
Joey: Hey Ross, what's wrong?
Ross: Rachel told me she needs to take a break from us.
Joey: Woah... man, that is rough. Are you serious?
Ross: Yeah, I'm completely devastated. I have no idea what to do.
Joey: Come on, Ross. We're gonna order pizza, hang out, and talk through it.
Ross: Thanks Joey. You're a true friend.`
};

let currentAnalysis = null;
let activeFilter = "all";

document.addEventListener("DOMContentLoaded", () => {
  setupNavigationTabs();
  setupOnboarding();
  setupInputsAndReview();
  setupAdvancedToggle();
  setupAnalysisAction();
  setupFilters();
  setupExports();

  // Load initial sample
  loadSample("conflict_recon");
});

function setupNavigationTabs() {
  const navButtons = document.querySelectorAll(".nav-btn");
  navButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const target = btn.dataset.tab;
      document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(target).classList.add("active");

      if (target === "tab-results" && currentAnalysis) {
        drawTrajectoryCanvas(currentAnalysis.trajectory_stats);
      }
    });
  });

  // Overview quick-action buttons
  document.getElementById("overviewStartBtn").addEventListener("click", () => {
    document.querySelector("[data-tab='tab-analyze']").click();
  });
  document.getElementById("overviewDemoBtn").addEventListener("click", () => {
    loadSample("conflict_recon");
    document.querySelector("[data-tab='tab-analyze']").click();
  });
}

function setupOnboarding() {
  const banner = document.getElementById("onboardingBanner");
  const dismissBtn = document.getElementById("onboardingDismissBtn");
  const demoBtn = document.getElementById("onboardingDemoBtn");

  dismissBtn.addEventListener("click", () => {
    banner.style.display = "none";
  });

  demoBtn.addEventListener("click", () => {
    banner.style.display = "none";
    loadSample("conflict_recon");
    document.querySelector("[data-tab='tab-analyze']").click();
  });
}

function setupInputsAndReview() {
  const modeRadios = document.querySelectorAll("input[name='inputMode']");
  const sampleGroup = document.getElementById("sampleSelectorGroup");
  const fileGroup = document.getElementById("fileUploadGroup");
  const textGroup = document.getElementById("textInputGroup");
  const sampleSelect = document.getElementById("sampleSelect");
  const fileInput = document.getElementById("waFileInput");
  const textInput = document.getElementById("chatTextInput");
  const refreshBtn = document.getElementById("refreshPreviewBtn");

  modeRadios.forEach(r => {
    r.addEventListener("change", (e) => {
      const mode = e.target.value;
      if (mode === "sample") {
        sampleGroup.classList.remove("hidden");
        fileGroup.classList.add("hidden");
        textGroup.classList.remove("hidden");
        loadSample(sampleSelect.value);
      } else if (mode === "whatsapp") {
        sampleGroup.classList.add("hidden");
        fileGroup.classList.remove("hidden");
        textGroup.classList.add("hidden");
      } else {
        sampleGroup.classList.add("hidden");
        fileGroup.classList.add("hidden");
        textGroup.classList.remove("hidden");
      }
      refreshPreview();
    });
  });

  sampleSelect.addEventListener("change", (e) => {
    loadSample(e.target.value);
    refreshPreview();
  });

  fileInput.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (evt) => {
        textInput.value = evt.target.result;
        refreshPreview();
      };
      reader.readAsText(file);
    }
  });

  textInput.addEventListener("input", () => {
    if (currentAnalysis) {
      document.getElementById("staleNotice").classList.remove("hidden");
    }
    refreshPreview();
  });

  refreshBtn.addEventListener("click", refreshPreview);
}

function loadSample(key) {
  if (SAMPLES[key]) {
    document.getElementById("chatTextInput").value = SAMPLES[key];
    refreshPreview();
  }
}

function refreshPreview() {
  const rawText = document.getElementById("chatTextInput").value.trim();
  const tbody = document.getElementById("previewTbody");
  const statsBadge = document.getElementById("previewStatsBadge");
  tbody.innerHTML = "";

  if (!rawText) {
    tbody.innerHTML = "<tr><td colspan='3' class='text-center text-muted'>No messages detected yet.</td></tr>";
    statsBadge.textContent = "Parsed: 0 Messages | 0 Speakers";
    return;
  }

  const lines = rawText.split("\n").map(l => l.trim()).filter(l => l.length > 0);
  const speakers = new Set();

  lines.forEach((l, idx) => {
    let spk = `Speaker ${(idx % 2) + 1}`;
    let txt = l;

    if (l.startsWith("[") && l.includes("]") && l.split("]")[1].includes(":")) {
      const parts = l.split("]")[1].split(":");
      spk = parts[0].trim();
      txt = parts.slice(1).join(":").trim();
    } else if (l.includes(":")) {
      const parts = l.split(":");
      spk = parts[0].trim();
      txt = parts.slice(1).join(":").trim();
    }

    speakers.add(spk);

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${idx}</td>
      <td><strong>${escapeHtml(spk)}</strong></td>
      <td>${escapeHtml(txt.length > 40 ? txt.substring(0, 40) + "..." : txt)}</td>
    `;
    tbody.appendChild(tr);
  });

  statsBadge.textContent = `Parsed: ${lines.length} Messages | ${speakers.size} Speakers`;
}

function setupAdvancedToggle() {
  const toggleBtn = document.getElementById("toggleAdvBtn");
  const container = document.getElementById("advancedOptionsContainer");
  const tauSlider = document.getElementById("tauRange");
  const tauDisplay = document.getElementById("tauDisplay");
  const kSlider = document.getElementById("kRange");
  const kDisplay = document.getElementById("kDisplay");

  toggleBtn.addEventListener("click", () => {
    container.classList.toggle("hidden");
    toggleBtn.textContent = container.classList.contains("hidden") ? "⚙️ Options ▼" : "⚙️ Options ▲";
  });

  tauSlider.addEventListener("input", (e) => {
    tauDisplay.textContent = parseFloat(e.target.value).toFixed(2);
  });

  kSlider.addEventListener("input", (e) => {
    kDisplay.textContent = `${parseInt(e.target.value)} turns`;
  });
}

function setupAnalysisAction() {
  const runBtn = document.getElementById("runAnalysisBtn");
  runBtn.addEventListener("click", async () => {
    const rawText = document.getElementById("chatTextInput").value.trim();
    if (!rawText) {
      showToast("Please provide conversation messages before analyzing.");
      return;
    }

    runBtn.disabled = true;
    runBtn.innerHTML = "<span>⏳ Analyzing with RoBERTa...</span>";

    const modelType = document.getElementById("modelSelect").value;
    const tau = parseFloat(document.getElementById("tauRange").value);
    const k = parseInt(document.getElementById("kRange").value);

    try {
      // 1. Try local FastAPI backend
      const resp = await fetch("/api/analyze/text", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          conversation_text: rawText,
          model_type: modelType,
          turning_point_threshold: tau,
          context_window: k
        })
      });

      if (!resp.ok) throw new Error("API error");
      const result = await resp.json();
      displayResults(result);
      showToast("Analysis complete via Transformer model!");
    } catch (err) {
      // 2. Standalone Mobile Heuristic Engine Fallback
      console.warn("Backend offline, running standalone mobile engine:", err);
      const fallbackResult = runStandaloneAnalysis(rawText, tau);
      displayResults(fallbackResult);
      showToast("Analysis complete via Mobile Engine!");
    } finally {
      runBtn.disabled = false;
      runBtn.innerHTML = "<span>🚀 Run Trajectory Analysis</span>";
      document.getElementById("staleNotice").classList.add("hidden");
    }
  });
}

function displayResults(result) {
  currentAnalysis = result;

  const stats = result.trajectory_stats;
  const preds = result.predictions;
  const tps = stats.turning_points || [];

  // 1. Update KPI ribbon
  const meanP = stats.mean_polarity || 0;
  const drift = stats.net_change || 0;
  const vol = stats.volatility || 0;

  document.getElementById("kpiTurns").textContent = preds.length;
  document.getElementById("kpiMean").textContent = (meanP > 0 ? "+" : "") + meanP.toFixed(2);
  document.getElementById("kpiDrift").textContent = (drift > 0 ? "+" : "") + drift.toFixed(2);
  document.getElementById("kpiVol").textContent = vol.toFixed(2);

  // 2. Update Distribution Bar
  const posCount = preds.filter(p => p.pred_sentiment === "positive").length;
  const neuCount = preds.filter(p => p.pred_sentiment === "neutral").length;
  const negCount = preds.filter(p => p.pred_sentiment === "negative").length;
  const total = preds.length || 1;

  const posPct = ((posCount / total) * 100).toFixed(0);
  const neuPct = ((neuCount / total) * 100).toFixed(0);
  const negPct = ((negCount / total) * 100).toFixed(0);

  document.getElementById("distPositiveBar").style.width = `${posPct}%`;
  document.getElementById("distNeutralBar").style.width = `${neuPct}%`;
  document.getElementById("distNegativeBar").style.width = `${negPct}%`;

  document.getElementById("distPosLabel").textContent = `Positive: ${posCount} (${posPct}%)`;
  document.getElementById("distNeuLabel").textContent = `Neutral: ${neuCount} (${neuPct}%)`;
  document.getElementById("distNegLabel").textContent = `Negative: ${negCount} (${negPct}%)`;

  // 3. Render Candidate Shifts
  const tpContainer = document.getElementById("tpContainer");
  tpContainer.innerHTML = "";
  if (tps.length === 0) {
    tpContainer.innerHTML = "<p class='empty-state'>No candidate turning points detected at sensitivity threshold.</p>";
  } else {
    tps.forEach(tp => {
      const item = document.createElement("div");
      item.className = "tp-item";
      item.innerHTML = `
        <div><span class="tp-badge">⚡ Turn ${tp.turn_index}</span> — <strong>${tp.speaker}</strong>: "${escapeHtml(tp.text)}"</div>
        <div style="color:#777873; margin-top:3px; font-size:0.72rem;">Shift: <strong>${tp.delta > 0 ? "+" : ""}${tp.delta.toFixed(2)}</strong> (From ${tp.score_before.toFixed(2)} to ${tp.score_after.toFixed(2)})</div>
      `;
      tpContainer.appendChild(item);
    });
  }

  // 4. Render Chat Stream
  renderFilteredChatStream();

  // 5. Render Written Report
  renderWrittenReport(result);

  // 6. Draw Canvas & Switch to Results Tab
  document.querySelector("[data-tab='tab-results']").click();
  drawTrajectoryCanvas(stats);
}

function setupFilters() {
  const filterBtns = document.querySelectorAll(".filter-pill");
  filterBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      filterBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      activeFilter = btn.dataset.filter;
      if (currentAnalysis) {
        renderFilteredChatStream();
      }
    });
  });
}

function renderFilteredChatStream() {
  const container = document.getElementById("chatStream");
  container.innerHTML = "";

  const preds = currentAnalysis.predictions;
  const tps = currentAnalysis.trajectory_stats.turning_points || [];
  const tpMap = {};
  tps.forEach(tp => { tpMap[tp.turn_index] = tp; });

  const speakers = [...new Set(preds.map(p => p.speaker))];
  const primarySpeaker = speakers[0];

  preds.forEach((msg, idx) => {
    const isTp = !!tpMap[idx];
    const sent = msg.pred_sentiment;

    // Filter check
    if (activeFilter === "positive" && sent !== "positive") return;
    if (activeFilter === "neutral" && sent !== "neutral") return;
    if (activeFilter === "negative" && sent !== "negative") return;
    if (activeFilter === "shifts" && !isTp) return;

    const isPrimary = (msg.speaker === primarySpeaker);
    const bubble = document.createElement("div");
    bubble.className = `bubble ${isPrimary ? "bubble-left" : "bubble-right"} ${isTp ? "bubble-tp" : ""}`;

    const sentClass = sent === "positive" ? "sent-pos" : (sent === "negative" ? "sent-neg" : "sent-neu");
    const polarityStr = (msg.polarity_score > 0 ? "+" : "") + msg.polarity_score.toFixed(2);

    bubble.innerHTML = `
      <div class="bubble-header">
        <span>${msg.speaker} (T${idx})</span>
        <span class="sent-chip ${sentClass}">${sent.toUpperCase()} (${polarityStr})</span>
      </div>
      <div class="bubble-text">${escapeHtml(msg.text)}</div>
      ${isTp ? `<div style="color:#C9A94A; font-size:0.68rem; font-weight:700; margin-top:2px;">⚡ CANDIDATE SHIFT (${tpMap[idx].delta > 0 ? "+" : ""}${tpMap[idx].delta.toFixed(2)})</div>` : ""}
    `;
    container.appendChild(bubble);
  });
}

function drawTrajectoryCanvas(stats) {
  const canvas = document.getElementById("trajectoryCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * 2;
  canvas.height = rect.height * 2;
  ctx.scale(2, 2);

  const w = rect.width;
  const h = rect.height;
  const pad = { top: 20, bottom: 25, left: 35, right: 20 };

  ctx.clearRect(0, 0, w, h);

  const scores = stats.scores || [];
  const tps = stats.turning_points || [];
  const n = scores.length;
  if (n === 0) return;

  const plotW = w - pad.left - pad.right;
  const plotH = h - pad.top - pad.bottom;
  const midY = pad.top + plotH / 2;

  // Shaded Zones
  ctx.fillStyle = "rgba(90, 174, 145, 0.12)";
  ctx.fillRect(pad.left, pad.top, plotW, plotH * 0.425);

  ctx.fillStyle = "rgba(135, 149, 165, 0.08)";
  ctx.fillRect(pad.left, pad.top + plotH * 0.425, plotW, plotH * 0.15);

  ctx.fillStyle = "rgba(217, 120, 115, 0.12)";
  ctx.fillRect(pad.left, pad.top + plotH * 0.575, plotW, plotH * 0.425);

  // Equilibrium Baseline (s=0)
  ctx.strokeStyle = "rgba(119, 120, 115, 0.35)";
  ctx.setLineDash([4, 4]);
  ctx.beginPath();
  ctx.moveTo(pad.left, midY);
  ctx.lineTo(pad.left + plotW, midY);
  ctx.stroke();
  ctx.setLineDash([]);

  const getX = (t) => pad.left + (n === 1 ? plotW / 2 : (t / (n - 1)) * plotW);
  const getY = (s) => midY - (s * (plotH / 2) * 0.88);

  // Polarity Line
  ctx.strokeStyle = "#292A2D";
  ctx.lineWidth = 2.5;
  ctx.beginPath();
  for (let i = 0; i < n; i++) {
    const x = getX(i);
    const y = getY(scores[i]);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.stroke();

  // Nodes
  for (let i = 0; i < n; i++) {
    const x = getX(i);
    const y = getY(scores[i]);
    ctx.fillStyle = scores[i] > 0.15 ? "#5AAE91" : (scores[i] < -0.15 ? "#D97873" : "#8795A5");
    ctx.beginPath();
    ctx.arc(x, y, 3.5, 0, Math.PI * 2);
    ctx.fill();
  }

  // Turning Point Stars
  tps.forEach(tp => {
    const t = tp.turn_index;
    const x = getX(t);
    const y = getY(tp.score_after);

    ctx.fillStyle = "#C9A94A";
    ctx.beginPath();
    ctx.arc(x, y, 6.5, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = "#FFFDF6";
    ctx.beginPath();
    ctx.arc(x, y, 2.5, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = "#C9A94A";
    ctx.font = "bold 9px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(`T${t}`, x, y + (tp.score_after >= 0 ? -10 : 15));
  });

  // Y-Axis Labels
  ctx.fillStyle = "#777873";
  ctx.font = "9px sans-serif";
  ctx.textAlign = "right";
  ctx.fillText("+1.0", pad.left - 5, pad.top + 6);
  ctx.fillText(" 0.0", pad.left - 5, midY + 3);
  ctx.fillText("-1.0", pad.left - 5, pad.top + plotH);
}

function renderWrittenReport(result) {
  const exp = result.explanation || {};
  const stats = result.trajectory_stats || {};
  const tps = stats.turning_points || [];

  let text = `=======================================================
SENTIMENT TRAJECTORY ANALYSIS REPORT
=======================================================

1. EXECUTIVE OVERVIEW:
   • Overall Pattern:       ${exp.summary_description || "Dynamic trajectory evaluated."}
   • Total Analyzed Turns:  ${stats.num_turns || 0}
   • Mean Polarity:         ${(stats.mean_polarity || 0) > 0 ? "+" : ""}${(stats.mean_polarity || 0).toFixed(4)}
   • Net Score Drift:       ${(stats.net_change || 0) > 0 ? "+" : ""}${(stats.net_change || 0).toFixed(4)}
   • Emotional Volatility:  ${(stats.volatility || 0).toFixed(4)}

2. CANDIDATE TURNING POINTS:
`;

  if (tps.length === 0) {
    text += "   (No candidate shifts meeting threshold criteria)\n";
  } else {
    tps.forEach((tp, i) => {
      text += `   [${i + 1}] Turn ${tp.turn_index} — ${tp.speaker} (Shift: ${tp.delta > 0 ? "+" : ""}${tp.delta.toFixed(2)})\n`;
      text += `       Message: "${tp.text}"\n`;
      text += `       Transition: ${tp.score_before.toFixed(2)}  ==>  ${tp.score_after.toFixed(2)}\n\n`;
    });
  }

  text += `3. SCIENTIFIC BOUNDARIES & LIMITATIONS:
   ${exp.epistemic_disclaimer || "Polarity scores are model outputs and do not represent direct subjective emotional truth."}
=======================================================`;

  document.getElementById("reportPre").textContent = text;
}

function setupExports() {
  document.getElementById("copyReportBtn").addEventListener("click", () => {
    const text = document.getElementById("reportPre").textContent;
    navigator.clipboard.writeText(text);
    showToast("Report copied to clipboard!");
  });

  document.getElementById("exportCsvBtn").addEventListener("click", () => {
    if (!currentAnalysis) return showToast("Run an analysis first.");
    downloadFile("predictions.csv", generateCsvContent(currentAnalysis.predictions), "text/csv");
  });

  document.getElementById("exportReportBtn").addEventListener("click", () => {
    if (!currentAnalysis) return showToast("Run an analysis first.");
    downloadFile("report.md", document.getElementById("reportPre").textContent, "text/markdown");
  });

  document.getElementById("exportJsonBtn").addEventListener("click", () => {
    if (!currentAnalysis) return showToast("Run an analysis first.");
    downloadFile("analysis.json", JSON.stringify(currentAnalysis, null, 2), "application/json");
  });
}

function generateCsvContent(preds) {
  let csv = "turn_id,speaker,pred_sentiment,polarity_score,prob_negative,prob_neutral,prob_positive,text\n";
  preds.forEach(p => {
    // Risk #87 formula injection escaping
    const safeText = (p.text.startsWith("=") || p.text.startsWith("+") || p.text.startsWith("-") || p.text.startsWith("@")) ? `'${p.text}` : p.text;
    const safeSpk = (p.speaker.startsWith("=") || p.speaker.startsWith("+") || p.speaker.startsWith("-") || p.speaker.startsWith("@")) ? `'${p.speaker}` : p.speaker;
    csv += `${p.turn_id},"${safeSpk}","${p.pred_sentiment}",${p.polarity_score},${p.prob_negative},${p.prob_neutral},${p.prob_positive},"${safeText.replace(/"/g, '""')}"\n`;
  });
  return csv;
}

function downloadFile(filename, content, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  showToast(`Downloaded ${filename}`);
}

// Standalone Mobile Engine Fallback
function runStandaloneAnalysis(rawText, tau) {
  const lines = rawText.split("\n").map(l => l.trim()).filter(l => l.length > 0);
  const posWords = ["thank", "thanks", "appreciate", "helpful", "good", "great", "awesome", "relief", "love", "apologize", "sorry", "glad", "happy", "yes"];
  const negWords = ["why", "terrible", "bad", "ruined", "fault", "panic", "devastated", "rough", "overwhelmed", "cancel", "hate", "issue", "exhausted", "late"];

  const predictions = [];
  const scores = [];

  lines.forEach((line, idx) => {
    let speaker = `Speaker ${(idx % 2) + 1}`;
    let text = line;
    if (line.includes("]") && line.includes(":")) {
      const p = line.split("]")[1].split(":");
      speaker = p[0].trim();
      text = p.slice(1).join(":").trim();
    } else if (line.includes(":")) {
      const p = line.split(":");
      speaker = p[0].trim();
      text = p.slice(1).join(":").trim();
    }

    const lower = text.toLowerCase();
    let posCount = 0;
    let negCount = 0;
    posWords.forEach(w => { if (lower.includes(w)) posCount++; });
    negWords.forEach(w => { if (lower.includes(w)) negCount++; });

    let pNeg = 0.15;
    let pNeu = 0.70;
    let pPos = 0.15;

    if (posCount > negCount) {
      pPos = Math.min(0.90, 0.45 + posCount * 0.15);
      pNeg = 0.05;
      pNeu = 1.0 - pPos - pNeg;
    } else if (negCount > posCount) {
      pNeg = Math.min(0.90, 0.45 + negCount * 0.15);
      pPos = 0.05;
      pNeu = 1.0 - pPos - pNeg;
    }

    const polarity = parseFloat((pPos - pNeg).toFixed(4));
    const sentiment = polarity > 0.15 ? "positive" : (polarity < -0.15 ? "negative" : "neutral");

    scores.push(polarity);
    predictions.push({
      turn_id: idx,
      speaker,
      text,
      pred_sentiment: sentiment,
      polarity_score: polarity,
      prob_negative: parseFloat(pNeg.toFixed(4)),
      prob_neutral: parseFloat(pNeu.toFixed(4)),
      prob_positive: parseFloat(pPos.toFixed(4))
    });
  });

  const n = scores.length;
  const deltas = [0];
  const tps = [];

  for (let i = 1; i < n; i++) {
    const d = scores[i] - scores[i - 1];
    deltas.push(d);
    if (Math.abs(d) >= tau || (scores[i - 1] < -0.15 && scores[i] > 0.15)) {
      tps.push({
        turn_index: i,
        speaker: predictions[i].speaker,
        text: predictions[i].text,
        score_before: scores[i - 1],
        score_after: scores[i],
        delta: d,
        shift_type: d > 0 ? "positive_shift" : "negative_shift"
      });
    }
  }

  const meanP = scores.reduce((a, b) => a + b, 0) / n;
  const drift = scores[n - 1] - scores[0];
  const vol = Math.sqrt(deltas.slice(1).map(d => d * d).reduce((a, b) => a + b, 0) / Math.max(1, n - 1));

  return {
    success: true,
    model_used: "mobile_standalone_engine",
    predictions: predictions,
    trajectory_stats: {
      num_turns: n,
      mean_polarity: meanP,
      net_change: drift,
      volatility: vol,
      turning_points: tps,
      scores: scores
    },
    explanation: {
      summary_description: drift > 0.2 ? "Significant positive recovery across conversation turns." : "Dynamic conversation trajectory.",
      epistemic_disclaimer: "Calculated via local client heuristics without external data transmission."
    }
  };
}

function escapeHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function showToast(msg) {
  if (window.AndroidApp && window.AndroidApp.showToast) {
    window.AndroidApp.showToast(msg);
  } else {
    const el = document.createElement("div");
    el.style.position = "fixed";
    el.style.bottom = "20px";
    el.style.left = "50%";
    el.style.transform = "translateX(-50%)";
    el.style.backgroundColor = "#2563EB";
    el.style.color = "#FFF";
    el.style.padding = "8px 16px";
    el.style.borderRadius = "20px";
    el.style.fontSize = "0.78rem";
    el.style.zIndex = "9999";
    el.style.boxShadow = "0 4px 12px rgba(0,0,0,0.5)";
    el.textContent = msg;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 2500);
  }
}
