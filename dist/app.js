const ARTIFACT_BASE_URL = new URL(
  window.PulseOfGivingConfig?.artifactBaseUrl || "./artifacts/",
  window.location.href
);

const els = {
  heroLede: document.querySelector("#heroLede"),
  audioHint: document.querySelector("#audioHint"),
  heroStatus: document.querySelector("#heroStatus"),
  title: document.querySelector("#signalTitle"),
  bpm: document.querySelector("#bpmLabel"),
  name: document.querySelector("#scenarioName"),
  description: document.querySelector("#scenarioDescription"),
  badge: document.querySelector("#artifactBadge"),
  coverage: document.querySelector("#coverageValue"),
  source: document.querySelector("#sourceValue"),
  published: document.querySelector("#publishedValue"),
  validUntil: document.querySelector("#validUntilValue"),
  disclosure: document.querySelector("#dataDisclosure"),
  tempo: document.querySelector("#tempoValue"),
  revision: document.querySelector("#harmonyValue"),
  review: document.querySelector("#textureValue"),
  now: document.querySelector("#nowPlaying"),
  status: document.querySelector("#musicStatus"),
  progress: document.querySelector("#progressFill"),
  buttons: [...document.querySelectorAll(".play-button")]
};

let approvedEdition = null;
let audio = null;

const stateCopy = {
  steady: {
    title: "A steady shared rhythm",
    description: "A verified local supply update indicates a steady state. Reliable donors help keep that steadiness possible."
  },
  needs_support: {
    title: "A gentle invitation to help",
    description: "A verified local update indicates that more donor support would help. The music stays calm; the decision remains yours."
  },
  high_need: {
    title: "A calm call to show up",
    description: "A verified local update indicates high need. The music is designed to be grounded, never alarming."
  }
};

function artifactUrl(path) {
  if (typeof path !== "string" || !/^[a-zA-Z0-9._/-]+$/.test(path) || path.includes("..")) {
    throw new Error("Artifact path is invalid.");
  }
  const url = new URL(path, ARTIFACT_BASE_URL);
  if (url.origin !== ARTIFACT_BASE_URL.origin || !url.pathname.startsWith(ARTIFACT_BASE_URL.pathname)) {
    throw new Error("Artifact path escapes its configured origin.");
  }
  return url;
}

function artifactChildUrl(path, parentUrl) {
  if (typeof path !== "string" || !/^[a-zA-Z0-9._/-]+$/.test(path) || path.includes("..")) {
    throw new Error("Artifact child path is invalid.");
  }
  const url = new URL(path, parentUrl);
  if (url.origin !== ARTIFACT_BASE_URL.origin || !url.pathname.startsWith(ARTIFACT_BASE_URL.pathname)) {
    throw new Error("Artifact child path escapes its configured origin.");
  }
  return url;
}

async function fetchJson(url) {
  const response = await fetch(url, { cache: "no-store", credentials: "omit" });
  if (!response.ok) throw new Error(`Artifact request failed (${response.status}).`);
  return response.json();
}

function selectedCandidate(manifest) {
  const candidate = manifest.candidates?.find(
    item => item.candidate_id === manifest.selected_candidate_id
  );
  if (!candidate?.evaluation?.passed || !/^[a-f0-9]{64}$/.test(candidate.sha256 || "")) {
    throw new Error("Approved artifact has no valid selected candidate.");
  }
  return candidate;
}

function validateApprovedManifest(manifest, pointer) {
  if (
    manifest.schema_version !== 1 ||
    manifest.status !== "approved" ||
    manifest.snapshot_status !== "verified" ||
    manifest.snapshot?.status !== "verified" ||
    !manifest.model?.release_eligible ||
    !manifest.human_reviewer ||
    manifest.artifact_id !== pointer.artifact_id
  ) {
    throw new Error("Artifact is not eligible for public playback.");
  }
  return selectedCandidate(manifest);
}

function formatDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Unavailable";
  return new Intl.DateTimeFormat("en-US", {
    timeZone: "America/Los_Angeles",
    dateStyle: "medium",
    timeStyle: "short"
  }).format(date);
}

function setSource(snapshot) {
  els.source.textContent = "";
  const url = new URL(snapshot.source_url);
  if (url.protocol !== "https:") throw new Error("Artifact source is not HTTPS.");
  const link = document.createElement("a");
  link.href = url.href;
  link.target = "_blank";
  link.rel = "noreferrer";
  link.textContent = snapshot.source_name;
  els.source.append(link);
}

function setButtonAvailability(enabled, label) {
  els.buttons.forEach(button => {
    button.disabled = !enabled;
    button.setAttribute("aria-pressed", "false");
    const buttonLabel = button.querySelector(".play-label");
    if (buttonLabel) buttonLabel.textContent = label;
  });
}

function showUnavailable() {
  els.heroStatus.textContent = "NOT PUBLISHED";
  els.title.textContent = "Waiting for an approved edition";
  els.name.textContent = "No approved edition yet";
  els.badge.textContent = "Awaiting publish";
  els.tempo.textContent = "—";
  els.revision.textContent = "—";
  els.review.textContent = "—";
  els.now.textContent = "No approved pulse is available";
  els.status.textContent = "The player activates only after the artifact gate passes.";
  els.audioHint.textContent = "This site never generates music in your browser.";
  setButtonAvailability(false, "No approved pulse yet");
}

function showApproved(manifest, candidate, manifestUrl) {
  const snapshot = manifest.snapshot;
  const state = stateCopy[snapshot.supply_state] || {
    title: "A verified community pulse",
    description: "A verified community update is available."
  };
  els.heroStatus.textContent = "APPROVED EDITION";
  els.title.textContent = state.title;
  els.bpm.textContent = `${manifest.music_spec.tempo_bpm} BPM`;
  els.name.textContent = snapshot.supply_state.replaceAll("_", " ");
  els.description.textContent = state.description;
  els.badge.textContent = "Verified + reviewed";
  els.coverage.textContent = snapshot.coverage_area;
  setSource(snapshot);
  els.published.textContent = formatDate(snapshot.published_at);
  els.validUntil.textContent = formatDate(snapshot.valid_until);
  els.disclosure.innerHTML = "";
  const marker = document.createElement("span");
  marker.className = "info-mark";
  marker.textContent = "i";
  const copy = document.createElement("p");
  copy.innerHTML = "<strong>Approved audio, verified source.</strong> The music was generated for this artifact; its date never replaces the source publication time.";
  els.disclosure.append(marker, copy);
  els.tempo.textContent = manifest.music_spec.tempo_bpm;
  els.revision.textContent = manifest.model.revision;
  els.review.textContent = "Approved";
  els.now.textContent = "Ready to play the approved community pulse";
  els.status.textContent = `Reviewed by ${manifest.human_reviewer}. Audio hash verifies before playback.`;
  els.heroLede.textContent = `A verified update for ${snapshot.coverage_area} informed this calm, reviewed music artifact. It is an invitation to learn and act—not a replacement for provider guidance.`;
  els.audioHint.textContent = "Audio downloads and verifies only after you press play.";
  setButtonAvailability(true, "Play the pulse");
  approvedEdition = { manifest, candidate, audioUrl: artifactChildUrl(candidate.audio_file, manifestUrl) };
}

function showReviewedDemo(demo, demoUrl) {
  els.heroStatus.textContent = "REVIEWED DEMO";
  els.title.textContent = "A calm prototype pulse";
  els.bpm.textContent = `${demo.tempo_bpm} BPM`;
  els.name.textContent = "Illustrative prototype";
  els.description.textContent = "A reviewed AI-generated music demonstration. It is not a statement about current blood supply.";
  els.badge.textContent = "Illustrative audio demo";
  els.coverage.textContent = "Pacific Northwest prototype";
  els.source.textContent = "Illustrative engineering fixture";
  els.published.textContent = "Not applicable";
  els.validUntil.textContent = "Not applicable";
  els.disclosure.innerHTML = `<span class="info-mark">i</span><p><strong>Illustrative data, reviewed audio.</strong> ${demo.disclosure}</p>`;
  els.tempo.textContent = demo.tempo_bpm;
  els.revision.textContent = demo.revision.slice(0, 12);
  els.review.textContent = "Human reviewed";
  els.now.textContent = "Ready to play the reviewed prototype";
  els.status.textContent = `Reviewed by ${demo.reviewer}. The audio hash verifies before playback.`;
  els.heroLede.textContent = "A calm, AI-generated audio prototype for Pulse of Giving. Real supply updates will remain unavailable until they are verified and approved.";
  els.audioHint.textContent = "This demo is model-generated audio; it does not represent live or current community data.";
  setButtonAvailability(true, "Play the demo");
  approvedEdition = {
    manifest: { kind: demo.kind },
    candidate: { sha256: demo.sha256 },
    audioUrl: new URL(demo.audio_file, demoUrl)
  };
}

async function digestHex(buffer) {
  if (!window.crypto?.subtle) throw new Error("Secure audio verification is unavailable in this browser.");
  const bytes = new Uint8Array(await window.crypto.subtle.digest("SHA-256", buffer));
  return [...bytes].map(byte => byte.toString(16).padStart(2, "0")).join("");
}

async function prepareAudio() {
  if (audio) return audio;
  if (!approvedEdition) throw new Error("No approved artifact is available.");
  const response = await fetch(approvedEdition.audioUrl, { cache: "no-store", credentials: "omit" });
  if (!response.ok) throw new Error(`Audio request failed (${response.status}).`);
  const buffer = await response.arrayBuffer();
  if ((await digestHex(buffer)) !== approvedEdition.candidate.sha256) {
    throw new Error("Audio integrity check failed.");
  }
  // Verify the exact response before allowing playback. Use its same-origin URL
  // for media decoding; this avoids browser-specific failures on blob: media.
  audio = new Audio(approvedEdition.audioUrl);
  audio.addEventListener("play", updatePlayingState);
  audio.addEventListener("pause", updatePlayingState);
  audio.addEventListener("ended", updatePlayingState);
  audio.addEventListener("timeupdate", updateProgress);
  return audio;
}

function updatePlayingState() {
  const playing = Boolean(audio && !audio.paused && !audio.ended);
  els.heroStatus.textContent = playing ? "PLAYING" : "APPROVED EDITION";
  els.buttons.forEach(button => {
    button.setAttribute("aria-pressed", String(playing));
    const label = button.querySelector(".play-label");
    if (label) label.textContent = playing ? "Pause the pulse" : "Play the pulse";
  });
}

function updateProgress() {
  const ratio = audio?.duration ? audio.currentTime / audio.duration : 0;
  els.progress.style.width = `${Math.max(0, Math.min(1, ratio)) * 100}%`;
}

async function togglePlayback() {
  if (!approvedEdition) return;
  try {
    els.buttons.forEach(button => { button.disabled = true; });
    const player = await prepareAudio();
    if (player.paused) await player.play();
    else player.pause();
  } catch (error) {
    els.status.textContent = "The approved audio could not be verified for playback. Please try again later.";
    els.heroStatus.textContent = "AUDIO UNAVAILABLE";
    console.warn("Pulse of Giving audio playback was blocked:", error);
  } finally {
    els.buttons.forEach(button => { button.disabled = !approvedEdition; });
  }
}

async function initializeArtifactPlayer() {
  showUnavailable();
  try {
    const pointer = await fetchJson(artifactUrl("current.json"));
    if (pointer.schema_version !== 1 || !pointer.artifact_id || !pointer.manifest_file) {
      throw new Error("Current artifact pointer is invalid.");
    }
    const manifestUrl = artifactUrl(pointer.manifest_file);
    const manifest = await fetchJson(manifestUrl);
    const candidate = validateApprovedManifest(manifest, pointer);
    showApproved(manifest, candidate, manifestUrl);
  } catch (error) {
    console.info("No eligible Pulse of Giving artifact is currently published.", error);
    try {
      const demoUrl = new URL("./demo/reviewed-illustrative.json", window.location.href);
      const demo = await fetchJson(demoUrl);
      if (demo.kind !== "reviewed_illustrative_demo" || !/^[a-f0-9]{64}$/.test(demo.sha256 || "")) {
        throw new Error("Illustrative demo metadata is invalid.");
      }
      showReviewedDemo(demo, demoUrl);
    } catch (demoError) {
      console.info("No reviewed illustrative demo is available.", demoError);
    }
  }
}

els.buttons.forEach(button => button.addEventListener("click", togglePlayback));
initializeArtifactPlayer();
