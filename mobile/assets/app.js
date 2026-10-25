/* mobile/assets/app.js
 * High-Performance Conversation Tone & Trajectory Studio
 * Optimized for Android Mobile & Tablet Viewports
 * Features: Peak-preserving bucket downsampling, windowed message streaming,
 * contextual dialogue drawers, plain-language guide, and 100% on-device processing.
 */

const PRESETS = {
  conflict_recon: {
    name: "Sample 1: Conflict to Reconciliation",
    text: `Alice: Why didn't you inform me about the sudden project deadline change?
Bob: I was overwhelmed with client meetings all morning, I didn't mean to keep you in the dark.
Alice: It completely ruined my afternoon schedule and I had to cancel personal plans.
Bob: I sincerely apologize for that. That was totally my fault, I should have texted earlier.
Alice: Thank you for acknowledging it. Let's make sure we sync on Slack every morning.
Bob: Absolutely. I'll take care of the final client deck so you don't have to work late.
Alice: That's very helpful, thank you so much! I appreciate your support.`
  },
  whatsapp_incident: {
    name: "Sample 2: WhatsApp Chat Format",
    text: `[10/24/24, 09:15:10 AM] Jordan: Hey team, did anyone check the deployment server logs?
[10/24/24, 09:16:02 AM] Morgan: Looking at them now. Database connection pool got exhausted.
[10/24/24, 09:17:40 AM] Jordan: This is terrible, we have customers waiting right now.
[10/24/24, 09:19:15 AM] Morgan: Don't panic, I found the leaked connection and patched it.
[10/24/24, 09:20:00 AM] Jordan: Wait, is the site back up?
[10/24/24, 09:21:20 AM] Morgan: Yes! All health checks are green and latency is under 40ms.
[10/24/24, 09:22:05 AM] Jordan: Awesome job Morgan! That was super fast. Great relief!`
  },
  meld_friends: {
    name: "Sample 3: MELD Friends Dialogue",
    text: `Ross: Hi.
Joey: Hey Ross, what's wrong?
Ross: Rachel told me she needs to take a break from us.
Joey: Woah... man, that is rough. Are you serious?
Ross: Yeah, I'm completely devastated. I have no idea what to do.
Joey: Come on, Ross. We're gonna order pizza, hang out, and talk through it.
Ross: Thanks Joey. You're a true friend.`
  },
  whatsapp_hinglish: {
    name: "Sample 4: WhatsApp Hinglish (Customer Escalation & Fix)",
    text: `Customer: Hello, mera order #98211 abhi tak deliver nahi hua
Support: Sir, let me check the tracking status for your order
Customer: Bhai 4 din se delay chal raha hai, bohot bekar service hai tumhari!
Support: Hum samajh sakte hain aapki pareshani, delivery partner se baat ho rahi hai
Customer: Mera paisa barbad ho gaya, urgent tha ye parcel!
Support: Sir package dispatch ho chuka hai aur agle 2 ghante me aapko mil jayega
Customer: Pakka mil jayega na? Mujhe aaj hi chahiye tha
Support: Haanji sir, guaranteed aaj deliver hoga. Asuvidha ke liye maafi
Customer: Chalo theek hai, bohot bohot shukriya aapki madad ke liye
Support: Thank you for contacting us, aapka din shubh ho!`
  },
  whatsapp_hindi: {
    name: "Sample 5: WhatsApp Hindi (पारिवारिक वार्तालाप)",
    text: `अमित: नमस्ते सभी को, क्या इस रविवार को मिलने की योजना बन सकती है?
नेहा: हाँ ज़रूर, बहुत दिनों से सब मिले नहीं हैं!
रोहन: मौसम बहुत खराब रहने वाला है, भारी बारिश की चेतावनी आई है
अमित: अरे यार, फिर बाहर जाना बहुत मुश्किल और परेशानी भरा होगा
नेहा: चिंता मत करो, हम सब घर पर ही दोपहर का भोजन रख सकते हैं
रोहन: यह तो बहुत ही बढ़िया और सुरक्षित विचार है!
अमित: सबको बहुत खुशी होगी, मैं गरमा-गरम नाश्ता लेकर आऊँगा
नेहा: धन्यवाद भाई, रविवार को दोपहर में मिलते हैं`
  }
};

// Global App State
let currentAnalysis = null;
let currentDatasetName = "Sample 1: Conflict to Reconciliation";
let activeView = "sec-overview";
let activeTimelinePreset = "all";
let isTableMode = false;

// Filter & Pagination State
let searchQuery = "";
let filterSpeaker = "all";
let filterSentiment = "all";
let filteredPredictions = [];
let visibleMessageCount = 25;
const MESSAGE_PAGE_CHUNK = 25;

document.addEventListener("DOMContentLoaded", () => {
  setupNavigation();
  setupConversationSelector();
  setupFileUpload();
  setupTimelineControls();
  setupMessageSearchAndFilters();
  setupDrawerControls();
  setupExportActions();

  // Load initial demonstration chat
  loadConversation("conflict_recon");
});

// ---------------------------------------------------------------------------
// 1. NAVIGATION (LABELED BOTTOM NAV & SETTINGS ACCESS)
// ---------------------------------------------------------------------------
function setupNavigation() {
  const bottomBtns = document.querySelectorAll(".bottom-nav-btn");
  bottomBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetId = btn.dataset.target;
      switchToView(targetId);

      bottomBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
    });
  });

  // Settings Gear in Masthead
  const settingsBtn = document.getElementById("openSettingsBtn");
  if (settingsBtn) {
    settingsBtn.addEventListener("click", () => {
      switchToView("sec-settings");
      bottomBtns.forEach(b => b.classList.remove("active"));
    });
  }

  // Overview "Deep View" Link
  const deepLink = document.getElementById("btnGoToDeepTimeline");
  if (deepLink) {
    deepLink.addEventListener("click", () => {
      const timelineBtn = document.querySelector("[data-target='sec-timeline']");
      if (timelineBtn) timelineBtn.click();
    });
  }
}

function switchToView(viewId) {
  activeView = viewId;
  document.querySelectorAll(".view-section").forEach(sec => sec.classList.remove("active"));
  const targetSec = document.getElementById(viewId);
  if (targetSec) {
    targetSec.classList.add("active");
  }

  // Trigger view updates
  if (viewId === "sec-overview") {
    renderOverviewTimeline();
  } else if (viewId === "sec-timeline") {
    renderDeepTimeline();
  } else if (viewId === "sec-people") {
    renderSpeakersView();
  } else if (viewId === "sec-messages") {
    renderMessagesList();
  }
}

// ---------------------------------------------------------------------------
// 2. CONVERSATION SELECTOR & FILE IMPORT
// ---------------------------------------------------------------------------
function setupConversationSelector() {
  const sel = document.getElementById("headerConvSelect");
  if (!sel) return;

  sel.addEventListener("change", (e) => {
    loadConversation(e.target.value);
  });
}

function setupFileUpload() {
  const uploadBtn = document.getElementById("quickUploadBtn");
  const fileInput = document.getElementById("waFileInput");
  if (!uploadBtn || !fileInput) return;

  uploadBtn.addEventListener("click", () => {
    fileInput.click();
  });

  fileInput.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (evt) => {
      const text = evt.target.result;
      const key = "custom_" + Date.now();
      PRESETS[key] = {
        name: file.name,
        text: text
      };

      const sel = document.getElementById("headerConvSelect");
      const opt = document.createElement("option");
      opt.value = key;
      opt.textContent = `📁 ${file.name}`;
      sel.appendChild(opt);
      sel.value = key;

      loadConversation(key);
      showToast(`Loaded ${file.name}`);
    };
    reader.readAsText(file, "UTF-8");
  });
}

function loadConversation(key) {
  const item = PRESETS[key];
  if (!item) return;

  currentDatasetName = item.name;
  const nameEl = document.getElementById("settingsDatasetName");
  if (nameEl) nameEl.textContent = item.name;

  currentAnalysis = runStandaloneAnalysis(item.text, 0.4);

  populateSpeakerFilterDropdown();

  searchQuery = "";
  filterSpeaker = "all";
  filterSentiment = "all";
  visibleMessageCount = 25;
  applyFilters();

  updateOverviewKpis();
  switchToView(activeView);
}

// ---------------------------------------------------------------------------
// 3. OVERVIEW DASHBOARD
// ---------------------------------------------------------------------------
function updateOverviewKpis() {
  if (!currentAnalysis) return;
  const stats = currentAnalysis.trajectory_stats || {};
  const preds = currentAnalysis.predictions || [];

  const meanP = stats.mean_polarity || 0.0;
  const drift = stats.net_change || 0.0;
  const vol = stats.volatility || 0.0;
  const tps = stats.turning_points || [];

  const participants = Array.from(new Set(preds.map(p => p.speaker)));

  // Update Scope Banner
  const badge = document.getElementById("overviewCoverageBadge");
  const details = document.getElementById("overviewScopeDetails");
  if (badge) badge.textContent = `${preds.length} Analyzed (100%)`;
  if (details) {
    details.textContent = `${preds.length} messages analyzed across ${participants.length} participants (${participants.join(', ')}). 0 messages skipped.`;
  }

  // Update KPI values
  const elMood = document.getElementById("kpiAvgMood");
  const elShift = document.getElementById("kpiNetShift");
  const elStab = document.getElementById("kpiStability");
  const elTP = document.getElementById("kpiTurningPoints");

  const moodDesc = meanP > 0.15 ? "Positive" : (meanP < -0.15 ? "Critical" : "Neutral");
  if (elMood) elMood.textContent = `${meanP >= 0 ? "+" : ""}${meanP.toFixed(2)} (${moodDesc})`;
  if (elShift) elShift.textContent = `${drift >= 0 ? "+" : ""}${drift.toFixed(2)} ${drift >= 0 ? "↗" : "↘"}`;
  if (elStab) elStab.textContent = `${Math.max(0, Math.min(100, Math.round((1 - vol) * 100)))}%`;
  if (elTP) elTP.textContent = `${tps.length} Shifts`;

  // Populate Executive Summary & Results of Analysis
  const totalTurns = preds.length || 1;
  const posCount = preds.filter(p => p.polarity_score > 0.15).length;
  const negCount = preds.filter(p => p.polarity_score < -0.15).length;
  const neuCount = totalTurns - posCount - negCount;

  const posPct = Math.round((posCount / totalTurns) * 100);
  const negPct = Math.round((negCount / totalTurns) * 100);
  const neuPct = 100 - posPct - negPct;

  // Health Status determination
  let healthText = "Balanced & Neutral";
  let healthCode = "neu";
  let takeaway = "Communication remained focused on routine task coordination.";
  if (drift >= 0.20 && meanP >= 0.05) {
    healthText = "Resolved & Positive";
    healthCode = "pos";
    takeaway = "Participants worked through initial friction to achieve mutual consensus and closure.";
  } else if (drift <= -0.20 && meanP <= -0.05) {
    healthText = "Tense & Unresolved";
    healthCode = "neg";
    takeaway = "Conversation ended with unaddressed friction; a clarifying follow-up is recommended.";
  } else if (meanP > 0.15) {
    healthText = "Cooperative & Supportive";
    healthCode = "pos";
    takeaway = "Strong interpersonal rapport and collaborative engagement were maintained throughout.";
  }

  const elHealth = document.getElementById("healthBadge");
  if (elHealth) {
    elHealth.textContent = healthText;
    elHealth.className = `health-badge ${healthCode}`;
  }

  // Story & Dynamics
  const firstSpk = preds[0]?.speaker || "Participant 1";
  const lastSpk = preds[preds.length - 1]?.speaker || "Participant 2";
  const firstTone = (preds[0]?.pred_sentiment || "neutral").toLowerCase();
  const lastTone = (preds[preds.length - 1]?.pred_sentiment || "neutral").toLowerCase();

  const storyEl = document.getElementById("execSummaryStory");
  if (storyEl) {
    storyEl.textContent = `This conversation spans ${totalTurns} messages among ${participants.length} participant${participants.length > 1 ? 's' : ''} (${participants.slice(0, 3).join(', ')}). It opened with a ${firstTone} turn by ${firstSpk} and evolved toward a ${lastTone} closing by ${lastSpk}. Overall mood drift is ${drift >= 0 ? '+' : ''}${drift.toFixed(2)}.`;
  }

  const dynEl = document.getElementById("execSummaryDynamics");
  if (dynEl) {
    dynEl.textContent = `Participation: ${participants.slice(0, 2).join(' and ')} drove the primary dialogue alternation. 0 messages were skipped or incomplete.`;
  }

  // Tone bar breakdown
  const pPos = document.getElementById("pctPos");
  const pNeu = document.getElementById("pctNeu");
  const pNeg = document.getElementById("pctNeg");
  if (pPos) pPos.textContent = `${posPct}%`;
  if (pNeu) pNeu.textContent = `${neuPct}%`;
  if (pNeg) pNeg.textContent = `${negPct}%`;

  const bPos = document.getElementById("barPos");
  const bNeu = document.getElementById("barNeu");
  const bNeg = document.getElementById("barNeg");
  if (bPos) bPos.style.width = `${posPct}%`;
  if (bNeu) bNeu.style.width = `${neuPct}%`;
  if (bNeg) bNeg.style.width = `${negPct}%`;

  // Key pivot moment
  const pivotEl = document.getElementById("resPivotText");
  if (pivotEl) {
    if (tps.length > 0) {
      const bestTp = tps.reduce((max, tp) => Math.abs(tp.delta || 0) > Math.abs(max.delta || 0) ? tp : max, tps[0]);
      const dir = (bestTp.delta || 0) > 0 ? "upward toward resolution" : "downward into disagreement";
      pivotEl.textContent = `Key Pivot: Turn #${bestTp.turn_index} by ${escapeHtml(bestTp.speaker)} shifted tone ${dir} (Δ ${(bestTp.delta || 0).toFixed(2)}).`;
    } else {
      pivotEl.textContent = "Key Pivot: No severe emotional swings detected; conversation tone was steady.";
    }
  }

  const takeEl = document.getElementById("resTakeawayText");
  if (takeEl) {
    takeEl.textContent = `Key Takeaway: ${takeaway}`;
  }

  const btnInspect = document.getElementById("btnInspectMessagesFromSummary");
  if (btnInspect && !btnInspect.dataset.bound) {
    btnInspect.dataset.bound = "true";
    btnInspect.addEventListener("click", () => {
      switchView("sec-messages");
    });
  }
}

// ---------------------------------------------------------------------------
// 4. LARGE-DATA DOWNSAMPLING & DUAL TIMELINE RENDERING
// ---------------------------------------------------------------------------
function downsampleTimeline(predictions, maxBuckets = 50) {
  const n = predictions.length;
  if (n <= maxBuckets) {
    return predictions.map(p => ({
      turn_center: p.turn_id,
      turn_start: p.turn_id,
      turn_end: p.turn_id,
      mean_score: p.polarity_score,
      min_score: p.polarity_score,
      max_score: p.polarity_score,
      volume: 1,
      speaker: p.speaker,
      text: p.text
    }));
  }

  const bucketSize = Math.ceil(n / maxBuckets);
  const buckets = [];

  for (let i = 0; i < n; i += bucketSize) {
    const chunk = predictions.slice(i, i + bucketSize);
    const scores = chunk.map(c => c.polarity_score);
    const meanS = scores.reduce((a, b) => a + b, 0) / chunk.length;
    const minS = Math.min(...scores);
    const maxS = Math.max(...scores);

    buckets.push({
      turn_center: Math.round((chunk[0].turn_id + chunk[chunk.length - 1].turn_id) / 2),
      turn_start: chunk[0].turn_id,
      turn_end: chunk[chunk.length - 1].turn_id,
      mean_score: parseFloat(meanS.toFixed(4)),
      min_score: parseFloat(minS.toFixed(4)),
      max_score: parseFloat(maxS.toFixed(4)),
      volume: chunk.length,
      speaker: chunk[0].speaker
    });
  }
  return buckets;
}

function renderOverviewTimeline() {
  const canvas = document.getElementById("overviewTimelineCanvas");
  if (!canvas || !currentAnalysis) return;

  const ctx = canvas.getContext("2d");
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  const w = rect.width || 340;
  const h = 180;

  canvas.width = w * dpr;
  canvas.height = h * dpr;
  ctx.scale(dpr, dpr);

  const preds = currentAnalysis.predictions || [];
  if (preds.length === 0) return;

  const data = downsampleTimeline(preds, 40);
  drawDualTimelineOnContext(ctx, data, w, h);
}

function renderDeepTimeline() {
  if (isTableMode) {
    renderAccessibleTimelineTable();
    return;
  }

  const canvas = document.getElementById("deepTimelineCanvas");
  if (!canvas || !currentAnalysis) return;

  const ctx = canvas.getContext("2d");
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  const w = rect.width || 340;
  const h = 240;

  canvas.width = w * dpr;
  canvas.height = h * dpr;
  ctx.scale(dpr, dpr);

  let preds = currentAnalysis.predictions || [];
  const n = preds.length;

  if (activeTimelinePreset === "half1" && n > 2) {
    preds = preds.slice(0, Math.floor(n / 2));
  } else if (activeTimelinePreset === "half2" && n > 2) {
    preds = preds.slice(Math.floor(n / 2));
  } else if (activeTimelinePreset === "shifts" && n > 2) {
    let minIdx = 0;
    let minVal = 999;
    preds.forEach((p, idx) => {
      if (p.polarity_score < minVal) {
        minVal = p.polarity_score;
        minIdx = idx;
      }
    });
    const s = Math.max(0, minIdx - 8);
    const e = Math.min(n, minIdx + 8);
    preds = preds.slice(s, e);
  }

  const data = downsampleTimeline(preds, 50);
  drawDualTimelineOnContext(ctx, data, w, h);
}

function drawDualTimelineOnContext(ctx, data, w, h) {
  ctx.clearRect(0, 0, w, h);

  const pad = { top: 16, bottom: 30, left: 34, right: 16 };
  const plotW = w - pad.left - pad.right;
  const plotH = h - pad.top - pad.bottom;
  const lineH = plotH * 0.70;
  const barH = plotH * 0.25;
  const barBaseY = pad.top + plotH;

  const n = data.length;
  if (n === 0) return;

  // Zero axis line
  const zeroY = pad.top + lineH / 2;
  ctx.strokeStyle = "#CBD5E1";
  ctx.lineWidth = 1;
  ctx.setLineDash([4, 4]);
  ctx.beginPath();
  ctx.moveTo(pad.left, zeroY);
  ctx.lineTo(pad.left + plotW, zeroY);
  ctx.stroke();
  ctx.setLineDash([]);

  // Axis Labels
  ctx.fillStyle = "#64748B";
  ctx.font = "9px sans-serif";
  ctx.textAlign = "right";
  ctx.fillText("+1.0", pad.left - 6, pad.top + 10);
  ctx.fillText(" 0.0", pad.left - 6, zeroY + 3);
  ctx.fillText("-1.0", pad.left - 6, pad.top + lineH);

  // Volatility Envelope (Shaded min-max band in calm neutral blue)
  ctx.fillStyle = "rgba(37, 99, 235, 0.10)";
  ctx.beginPath();
  data.forEach((d, i) => {
    const x = pad.left + (i / Math.max(1, n - 1)) * plotW;
    const yMax = pad.top + (1 - (d.max_score + 1) / 2) * lineH;
    if (i === 0) ctx.moveTo(x, yMax);
    else ctx.lineTo(x, yMax);
  });
  for (let i = n - 1; i >= 0; i--) {
    const x = pad.left + (i / Math.max(1, n - 1)) * plotW;
    const yMin = pad.top + (1 - (data[i].min_score + 1) / 2) * lineH;
    ctx.lineTo(x, yMin);
  }
  ctx.closePath();
  ctx.fill();

  // Primary Tone Trajectory Curve (Action Blue #2563EB)
  ctx.strokeStyle = "#2563EB";
  ctx.lineWidth = 2.0;
  ctx.beginPath();
  data.forEach((d, i) => {
    const x = pad.left + (i / Math.max(1, n - 1)) * plotW;
    const y = pad.top + (1 - (d.mean_score + 1) / 2) * lineH;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  // Points (Color-coded by tone: Green positive, Red negative)
  data.forEach((d, i) => {
    const x = pad.left + (i / Math.max(1, n - 1)) * plotW;
    const y = pad.top + (1 - (d.mean_score + 1) / 2) * lineH;
    ctx.fillStyle = d.mean_score > 0.15 ? "#059669" : (d.mean_score < -0.15 ? "#DC2626" : "#D97706");
    ctx.beginPath();
    ctx.arc(x, y, 3.2, 0, Math.PI * 2);
    ctx.fill();
  });

  // Message Volume Bars at bottom
  const maxVol = Math.max(...data.map(d => d.volume), 1);
  const barW = Math.max(2, (plotW / n) * 0.7);

  data.forEach((d, i) => {
    const x = pad.left + (i / Math.max(1, n - 1)) * plotW;
    const bHeight = (d.volume / maxVol) * barH;
    ctx.fillStyle = "rgba(100, 116, 139, 0.55)";
    ctx.fillRect(x - barW / 2, barBaseY - bHeight, barW, bHeight);
  });

  // X-axis turn progress labels
  ctx.fillStyle = "#64748B";
  ctx.font = "9px sans-serif";
  ctx.textAlign = "left";
  ctx.fillText(`Turn ${data[0].turn_start}`, pad.left, h - 8);
  ctx.textAlign = "right";
  ctx.fillText(`Turn ${data[n - 1].turn_end}`, pad.left + plotW, h - 8);
}

function setupTimelineControls() {
  const pills = document.querySelectorAll("[data-preset]");
  pills.forEach(pill => {
    pill.addEventListener("click", () => {
      pills.forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      activeTimelinePreset = pill.dataset.preset;
      renderDeepTimeline();
    });
  });

  const toggleBtn = document.getElementById("toggleTableModeBtn");
  if (toggleBtn) {
    toggleBtn.addEventListener("click", () => {
      isTableMode = !isTableMode;
      toggleBtn.textContent = isTableMode ? "📈 Visual Mode" : "📋 Table Mode";
      document.getElementById("timelineVisualMode").classList.toggle("hidden", isTableMode);
      document.getElementById("timelineTableMode").classList.toggle("hidden", !isTableMode);
      if (isTableMode) {
        renderAccessibleTimelineTable();
      } else {
        renderDeepTimeline();
      }
    });
  }
}

function renderAccessibleTimelineTable() {
  const tbody = document.getElementById("accessibleTimelineTbody");
  if (!tbody || !currentAnalysis) return;

  const preds = currentAnalysis.predictions || [];
  const down = downsampleTimeline(preds, 30);

  tbody.innerHTML = "";
  down.forEach(d => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>Turns ${d.turn_start}–${d.turn_end}</td>
      <td class="${d.mean_score >= 0 ? 'text-green' : 'text-red'}">${d.mean_score >= 0 ? '+' : ''}${d.mean_score.toFixed(2)}</td>
      <td>[${d.min_score.toFixed(2)}, ${d.max_score.toFixed(2)}]</td>
      <td>${d.volume}</td>
    `;
    tbody.appendChild(tr);
  });
}

// ---------------------------------------------------------------------------
// 5. PEOPLE & PARTICIPATION
// ---------------------------------------------------------------------------
function renderSpeakersView() {
  const grid = document.getElementById("speakersCardsGrid");
  if (!grid || !currentAnalysis) return;

  const preds = currentAnalysis.predictions || [];
  const total = preds.length;
  if (total === 0) return;

  const spkStats = {};
  preds.forEach(p => {
    const s = p.speaker || "Unknown";
    if (!spkStats[s]) {
      spkStats[s] = { count: 0, scores: [] };
    }
    spkStats[s].count++;
    spkStats[s].scores.push(p.polarity_score);
  });

  grid.innerHTML = "";
  Object.keys(spkStats).forEach(s => {
    const obj = spkStats[s];
    const avg = obj.scores.reduce((a, b) => a + b, 0) / obj.count;
    const min = Math.min(...obj.scores);
    const max = Math.max(...obj.scores);
    const pct = ((obj.count / total) * 100).toFixed(1);

    const card = document.createElement("div");
    card.className = "speaker-card";
    card.innerHTML = `
      <div class="speaker-top-row">
        <strong>${escapeHtml(s)}</strong>
        <span class="speaker-share">${pct}% (${obj.count} messages)</span>
      </div>
      <div class="speaker-stats-row">
        <span>Average Tone: <strong class="${avg >= 0 ? 'text-green' : 'text-red'}">${avg >= 0 ? '+' : ''}${avg.toFixed(2)}</strong></span>
        <span class="text-muted">Observed Range: [${min.toFixed(2)}, ${max.toFixed(2)}]</span>
      </div>
      <button class="btn-xs-filter" onclick="filterBySpeakerAndOpenMessages('${escapeHtml(s)}')">Filter Messages by ${escapeHtml(s)} →</button>
    `;
    grid.appendChild(card);
  });

  renderSpeakerAlternationCanvas(preds, spkStats);
}

function filterBySpeakerAndOpenMessages(speakerName) {
  filterSpeaker = speakerName;
  const sel = document.getElementById("mobileSpeakerSelect");
  if (sel) sel.value = speakerName;
  applyFilters();
  const msgBtn = document.querySelector("[data-target='sec-messages']");
  if (msgBtn) msgBtn.click();
}

function renderSpeakerAlternationCanvas(preds, spkStats) {
  const canvas = document.getElementById("speakerAlternationCanvas");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  const w = rect.width || 340;
  const h = 140;

  canvas.width = w * dpr;
  canvas.height = h * dpr;
  ctx.scale(dpr, dpr);

  ctx.clearRect(0, 0, w, h);
  const speakers = Object.keys(spkStats);
  const spkCount = speakers.length;
  if (spkCount === 0) return;

  const rowH = (h - 20) / spkCount;

  speakers.forEach((s, idx) => {
    const y = 10 + idx * rowH + rowH / 2;
    ctx.fillStyle = "#E2E8F0";
    ctx.fillRect(80, y - 1, w - 90, 2);

    ctx.fillStyle = "#0F172A";
    ctx.font = "bold 9px sans-serif";
    ctx.textAlign = "left";
    ctx.fillText(s, 6, y + 3);
  });

  const n = preds.length;
  preds.forEach(p => {
    const spkIdx = speakers.indexOf(p.speaker);
    if (spkIdx !== -1) {
      const y = 10 + spkIdx * rowH + rowH / 2;
      const x = 80 + (p.turn_id / Math.max(1, n - 1)) * (w - 96);
      ctx.fillStyle = p.polarity_score > 0.15 ? "#059669" : (p.polarity_score < -0.15 ? "#DC2626" : "#D97706");
      ctx.beginPath();
      ctx.arc(x, y, 3, 0, Math.PI * 2);
      ctx.fill();
    }
  });
}

// ---------------------------------------------------------------------------
// 6. MESSAGES & SEARCH (WINDOWED)
// ---------------------------------------------------------------------------
function setupMessageSearchAndFilters() {
  const searchInput = document.getElementById("mobileSearchInput");
  const speakerSel = document.getElementById("mobileSpeakerSelect");
  const sentimentSel = document.getElementById("mobileSentimentSelect");
  const loadMoreBtn = document.getElementById("loadMoreMessagesBtn");
  const clearBtn = document.getElementById("clearAllFiltersBtn");

  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      searchQuery = e.target.value.toLowerCase().trim();
      visibleMessageCount = 25;
      applyFilters();
      renderMessagesList();
    });
  }

  if (speakerSel) {
    speakerSel.addEventListener("change", (e) => {
      filterSpeaker = e.target.value;
      visibleMessageCount = 25;
      applyFilters();
      renderMessagesList();
    });
  }

  if (sentimentSel) {
    sentimentSel.addEventListener("change", (e) => {
      filterSentiment = e.target.value;
      visibleMessageCount = 25;
      applyFilters();
      renderMessagesList();
    });
  }

  if (loadMoreBtn) {
    loadMoreBtn.addEventListener("click", () => {
      visibleMessageCount += MESSAGE_PAGE_CHUNK;
      renderMessagesList();
    });
  }

  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      searchQuery = "";
      filterSpeaker = "all";
      filterSentiment = "all";
      if (searchInput) searchInput.value = "";
      if (speakerSel) speakerSel.value = "all";
      if (sentimentSel) sentimentSel.value = "all";
      visibleMessageCount = 25;
      applyFilters();
      renderMessagesList();
    });
  }
}

function populateSpeakerFilterDropdown() {
  const sel = document.getElementById("mobileSpeakerSelect");
  if (!sel || !currentAnalysis) return;

  const preds = currentAnalysis.predictions || [];
  const speakers = Array.from(new Set(preds.map(p => p.speaker)));

  sel.innerHTML = `<option value="all">All Participants</option>`;
  speakers.forEach(s => {
    const opt = document.createElement("option");
    opt.value = s;
    opt.textContent = s;
    sel.appendChild(opt);
  });
}

function applyFilters() {
  if (!currentAnalysis) {
    filteredPredictions = [];
    return;
  }

  const preds = currentAnalysis.predictions || [];
  filteredPredictions = preds.filter(p => {
    const matchSearch = !searchQuery ||
      p.text.toLowerCase().includes(searchQuery) ||
      p.speaker.toLowerCase().includes(searchQuery);

    const matchSpeaker = filterSpeaker === "all" || p.speaker === filterSpeaker;
    const matchSentiment = filterSentiment === "all" || p.pred_sentiment === filterSentiment;

    return matchSearch && matchSpeaker && matchSentiment;
  });

  const ribbon = document.getElementById("activeFilterRibbon");
  const txt = document.getElementById("activeFilterText");
  const activeCount = (searchQuery ? 1 : 0) + (filterSpeaker !== "all" ? 1 : 0) + (filterSentiment !== "all" ? 1 : 0);

  if (ribbon && txt) {
    if (activeCount > 0) {
      ribbon.classList.remove("hidden");
      txt.textContent = `Active Filters: ${activeCount} applied (${filteredPredictions.length} matching)`;
    } else {
      ribbon.classList.add("hidden");
    }
  }
}

function renderMessagesList() {
  const container = document.getElementById("messagesList");
  const countLabel = document.getElementById("messagesCountLabel");
  const loadMoreBtn = document.getElementById("loadMoreMessagesBtn");
  if (!container) return;

  container.innerHTML = "";
  const total = filteredPredictions.length;
  const toShow = filteredPredictions.slice(0, visibleMessageCount);

  if (countLabel) {
    countLabel.textContent = `Showing ${toShow.length} of ${total} messages`;
  }

  if (loadMoreBtn) {
    loadMoreBtn.style.display = toShow.length < total ? "block" : "none";
  }

  if (toShow.length === 0) {
    container.innerHTML = `<div class="empty-card"><p>No messages match the current search or filters.</p></div>`;
    return;
  }

  toShow.forEach(p => {
    const card = document.createElement("div");
    card.className = "message-bubble clickable";
    const isPos = p.polarity_score > 0.15;
    const isNeg = p.polarity_score < -0.15;
    const tagClass = isPos ? "badge-pos" : (isNeg ? "badge-neg" : "badge-neu");

    card.innerHTML = `
      <div class="bubble-header">
        <span class="bubble-speaker">${escapeHtml(p.speaker)}</span>
        <span class="bubble-tag ${tagClass}">Turn #${p.turn_id} • ${p.pred_sentiment.toUpperCase()} (${p.polarity_score >= 0 ? '+' : ''}${p.polarity_score.toFixed(2)})</span>
      </div>
      <p class="bubble-text">${highlightSearch(escapeHtml(p.text), searchQuery)}</p>
    `;
    card.addEventListener("click", () => {
      openDetailDrawer(p.turn_id);
    });
    container.appendChild(card);
  });
}

function highlightSearch(text, query) {
  if (!query) return text;
  const re = new RegExp(`(${query})`, "gi");
  return text.replace(re, `<mark class="search-highlight">$1</mark>`);
}

// ---------------------------------------------------------------------------
// 7. DETAIL CONTEXT DRAWER (MODAL BOTTOM SHEET)
// ---------------------------------------------------------------------------
function setupDrawerControls() {
  const drawer = document.getElementById("detailContextDrawer");
  const closeBtn = document.getElementById("closeDrawerBtn");
  if (closeBtn && drawer) {
    closeBtn.addEventListener("click", () => {
      drawer.classList.add("hidden");
    });
  }
}

function openDetailDrawer(turnId) {
  if (!currentAnalysis) return;
  const drawer = document.getElementById("detailContextDrawer");
  const preds = currentAnalysis.predictions || [];
  const target = preds.find(p => p.turn_id === turnId);
  if (!target || !drawer) return;

  document.getElementById("drawerTurnTitle").textContent = `Turn #${target.turn_id} Evidence`;
  document.getElementById("drawerSpeakerBadge").textContent = target.speaker;
  document.getElementById("drawerUtteranceText").textContent = `"${target.text}"`;
  document.getElementById("drawerPolarityVal").textContent = `Polarity: ${target.polarity_score >= 0 ? '+' : ''}${target.polarity_score.toFixed(2)}`;

  const sentTag = document.getElementById("drawerSentimentTag");
  sentTag.textContent = target.pred_sentiment.toUpperCase();
  sentTag.className = `sentiment-pill ${target.polarity_score > 0 ? 'pos' : (target.polarity_score < 0 ? 'neg' : 'neu')}`;

  const probBox = document.getElementById("drawerProbabilities");
  probBox.innerHTML = `
    <span>Pos: ${(target.prob_positive * 100).toFixed(0)}%</span>
    <span>Neu: ${(target.prob_neutral * 100).toFixed(0)}%</span>
    <span>Neg: ${(target.prob_negative * 100).toFixed(0)}%</span>
  `;

  const ctxBox = document.getElementById("drawerContextTurns");
  ctxBox.innerHTML = "";
  const idx = preds.indexOf(target);
  const start = Math.max(0, idx - 3);
  const preceding = preds.slice(start, idx);

  if (preceding.length === 0) {
    ctxBox.innerHTML = `<span class="text-muted">Initial turn of conversation (no prior context).</span>`;
  } else {
    preceding.forEach(ctxTurn => {
      const pTurn = document.createElement("div");
      pTurn.className = "ctx-turn-row";
      pTurn.innerHTML = `<strong>[Turn ${ctxTurn.turn_id}] ${escapeHtml(ctxTurn.speaker)}:</strong> ${escapeHtml(ctxTurn.text)}`;
      ctxBox.appendChild(pTurn);
    });
  }

  drawer.classList.remove("hidden");
}

// ---------------------------------------------------------------------------
// 8. EXPORTS & DATA SETTINGS
// ---------------------------------------------------------------------------
function setupExportActions() {
  const csvBtn = document.getElementById("btnExportCsv");
  const jsonBtn = document.getElementById("btnExportJson");
  const purgeBtn = document.getElementById("btnPurgeData");

  if (csvBtn) {
    csvBtn.addEventListener("click", () => {
      if (!currentAnalysis) return;
      const csv = generateSanitizedCsv(currentAnalysis.predictions);
      downloadFile("conversation_tone_sanitized.csv", csv, "text/csv");
    });
  }

  if (jsonBtn) {
    jsonBtn.addEventListener("click", () => {
      if (!currentAnalysis) return;
      const json = JSON.stringify(currentAnalysis, null, 2);
      downloadFile("conversation_tone_analysis.json", json, "application/json");
    });
  }

  if (purgeBtn) {
    purgeBtn.addEventListener("click", () => {
      if (confirm("Permanently discard conversation data from device memory?")) {
        currentAnalysis = null;
        updateOverviewKpis();
        showToast("Conversation data purged from local memory.");
      }
    });
  }
}

function generateSanitizedCsv(preds) {
  let csv = "turn_id,speaker,pred_sentiment,polarity_score,text\n";
  preds.forEach(p => {
    // Risk #87 formula injection defense
    const safeTxt = p.text.startsWith("=") || p.text.startsWith("+") || p.text.startsWith("-") || p.text.startsWith("@") ? `'${p.text}` : p.text;
    const safeSpk = p.speaker.startsWith("=") || p.speaker.startsWith("+") || p.speaker.startsWith("-") || p.speaker.startsWith("@") ? `'${p.speaker}` : p.speaker;
    csv += `${p.turn_id},"${safeSpk}","${p.pred_sentiment}",${p.polarity_score},"${safeTxt.replace(/"/g, '""')}"\n`;
  });
  return csv;
}

function downloadFile(name, content, mime) {
  const blob = new Blob([content], { type: mime });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = name;
  a.click();
  showToast(`Downloaded ${name}`);
}

// ---------------------------------------------------------------------------
// 9. LOCAL STANDALONE SENTIMENT ENGINE
// ---------------------------------------------------------------------------
function runStandaloneAnalysis(rawText, tau) {
  const lines = rawText.split("\n").map(l => l.trim()).filter(l => l.length > 0);
  const posWords = [
    "thank", "thanks", "appreciate", "helpful", "good", "great", "awesome", "relief", "love", "apologize", "sorry", "glad", "happy", "yes", "fixed", "patch",
    "shukriya", "dhanyawad", "badhiya", "mast", "shandar", "zabardast", "theek", "thik", "accha", "achha", "acha", "sahi", "khush",
    "धन्यवाद", "आभार", "बढ़िया", "शानदार", "खुशी", "मदद", "सराहनीय", "सुचारू", "सुरक्षित"
  ];
  const negWords = [
    "why", "terrible", "bad", "ruined", "fault", "panic", "devastated", "rough", "overwhelmed", "cancel", "hate", "issue", "exhausted", "late", "error", "bug",
    "bekar", "bakwas", "kharab", "gussa", "pareshan", "mushkil", "bura", "barbad", "delay", "fraud", "dhoka", "chinta",
    "खराब", "गुस्सा", "परेशानी", "मुश्किल", "घटिया", "शिकायत", "असुविधा", "तनाव", "चिंता"
  ];

  const predictions = [];
  const scores = [];

  lines.forEach((line, idx) => {
    let speaker = `Participant ${(idx % 2) + 1}`;
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

    // Collapse character elongations (e.g. boooohot -> bohot, achhaaaa -> achha)
    const collapsed = text.replace(/([a-zA-Z\u0900-\u097F])\1{2,}/g, "$1$1");
    const lower = collapsed.toLowerCase();
    let posCount = 0;
    let negCount = 0;
    posWords.forEach(w => { if (lower.includes(w)) posCount++; });
    negWords.forEach(w => { if (lower.includes(w)) negCount++; });

    let pNeg = 0.15;
    let pNeu = 0.70;
    let pPos = 0.15;

    if (posCount > negCount) {
      pPos = Math.min(0.92, 0.45 + posCount * 0.15);
      pNeg = 0.04;
      pNeu = 1.0 - pPos - pNeg;
    } else if (negCount > posCount) {
      pNeg = Math.min(0.92, 0.45 + negCount * 0.15);
      pPos = 0.04;
      pNeu = 1.0 - pPos - pNeg;
    }

    const polarity = parseFloat((pPos - pNeg).toFixed(4));
    const sentiment = polarity > 0.15 ? "positive" : (polarity < -0.15 ? "negative" : "neutral");

    scores.push(polarity);
    predictions.push({
      turn_id: idx + 1,
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
        turn_index: i + 1,
        speaker: predictions[i].speaker,
        text: predictions[i].text,
        score_before: scores[i - 1],
        score_after: scores[i],
        delta: d
      });
    }
  }

  const meanP = scores.reduce((a, b) => a + b, 0) / Math.max(1, n);
  const drift = n > 1 ? scores[n - 1] - scores[0] : 0;
  const vol = Math.sqrt(deltas.slice(1).map(d => d * d).reduce((a, b) => a + b, 0) / Math.max(1, n - 1));

  return {
    success: true,
    predictions: predictions,
    trajectory_stats: {
      num_turns: n,
      mean_polarity: meanP,
      net_change: drift,
      volatility: vol,
      turning_points: tps
    }
  };
}

function escapeHtml(str) {
  return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function showToast(msg) {
  if (window.AndroidApp && window.AndroidApp.showToast) {
    window.AndroidApp.showToast(msg);
  } else {
    const el = document.createElement("div");
    el.className = "app-toast";
    el.textContent = msg;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 2500);
  }
}
