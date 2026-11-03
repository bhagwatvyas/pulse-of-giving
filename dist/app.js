const snapshot = {
  id: "illustrative-pnw-snapshot-001",
  status: "illustrative",
  coverage: "Pacific Northwest prototype"
};

const scenarios = {
  steady: {
    name: "Steady supply",
    description: "A calm local supply picture: enough room to breathe, with a reminder that reliable donors keep it that way.",
    bpm: 68, harmony: "Open", texture: "Warm", title: "A steady shared rhythm",
    chords: [220, 277.18, 329.63], pattern: [0, 2, 1, 2, 0, 2, 1, 2],
    path: "M0,80 C25,80 30,80 45,80 C65,80 65,32 83,32 C101,32 101,113 121,113 C139,113 139,57 158,57 C178,57 181,80 205,80 C228,80 238,80 250,80 C271,80 271,43 289,43 C307,43 307,101 327,101 C345,101 345,65 363,65 C382,65 383,80 410,80 L500,80"
  },
  tight: {
    name: "Needs support",
    description: "A smaller buffer creates a little more motion, while the music stays grounded and restful. This remains an illustrative scenario, not a current local alert.",
    bpm: 72, harmony: "Grounded", texture: "Flowing", title: "A gentle call to show up",
    chords: [196, 246.94, 293.66], pattern: [0, 1, 2, 1, 0, 2, 1, 2],
    path: "M0,80 C25,80 33,67 45,67 C65,67 65,42 83,42 C101,42 101,105 121,105 C139,105 139,60 158,60 C178,60 181,80 205,80 C228,80 238,80 250,80 C271,80 271,48 289,48 C307,48 307,96 327,96 C345,96 345,66 363,66 C382,66 383,80 410,80 L500,80"
  },
  urgent: {
    name: "High need",
    description: "When a community needs extra help, the pulse becomes gently active—not anxious. It is an illustrative invitation to participate, not a live shortage notice.",
    bpm: 76, harmony: "Attentive", texture: "Present", title: "A calm invitation to help",
    chords: [185, 220, 277.18], pattern: [0, 2, 1, 0, 2, 1, 2, 1],
    path: "M0,80 C22,80 28,64 43,64 C60,64 66,36 82,36 C100,36 103,109 121,109 C139,109 140,55 158,55 C177,55 181,80 205,80 C228,80 236,80 250,80 C271,80 271,42 289,42 C307,42 307,101 327,101 C345,101 345,61 363,61 C382,61 383,80 410,80 L500,80"
  }
};

let current = "steady";
let audioContext;
let playing = false;
let scheduled = [];
let endTimer;

const els = {
  name: document.querySelector("#scenarioName"),
  description: document.querySelector("#scenarioDescription"),
  tempo: document.querySelector("#tempoValue"),
  harmony: document.querySelector("#harmonyValue"),
  texture: document.querySelector("#textureValue"),
  title: document.querySelector("#signalTitle"),
  bpm: document.querySelector("#bpmLabel"),
  path: document.querySelector("#signalPath"),
  now: document.querySelector("#nowPlaying"),
  status: document.querySelector("#musicStatus"),
  heroStatus: document.querySelector("#heroStatus"),
  progress: document.querySelector("#progressFill"),
  dailyTitle: document.querySelector("#dailyVariationTitle"),
  dailyDetail: document.querySelector("#dailyVariationDetail"),
  buttons: [...document.querySelectorAll(".play-button")]
};

function pacificDateKey() {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/Los_Angeles", year: "numeric", month: "2-digit", day: "2-digit"
  }).format(new Date());
}

function pacificDateLabel() {
  return new Intl.DateTimeFormat("en-US", {
    timeZone: "America/Los_Angeles", month: "long", day: "numeric", year: "numeric"
  }).format(new Date());
}

function hashSeed(input) {
  let value = 2166136261;
  for (const char of input) {
    value ^= char.charCodeAt(0);
    value = Math.imul(value, 16777619);
  }
  return value >>> 0;
}

function seededRandom(input) {
  let state = hashSeed(input);
  return () => {
    state += 0x6D2B79F5;
    let value = state;
    value = Math.imul(value ^ (value >>> 15), value | 1);
    value ^= value + Math.imul(value ^ (value >>> 7), value | 61);
    return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
  };
}

function musicalPlan(scenario) {
  const date = pacificDateKey();
  const random = seededRandom(`${snapshot.id}:${scenario.name}:${date}`);
  const timbres = ["sine", "triangle", "sine"];
  return {
    date,
    label: pacificDateLabel(),
    bpm: scenario.bpm + Math.floor(random() * 3),
    patternShift: Math.floor(random() * scenario.pattern.length),
    octave: random() > .62 ? 2 : 1,
    timbre: timbres[Math.floor(random() * timbres.length)],
    melodicGain: .024 + random() * .012
  };
}

function updateDailyCopy() {
  const plan = musicalPlan(scenarios[current]);
  els.dailyTitle.textContent = `Pacific-day variation · ${plan.label}`;
  els.dailyDetail.textContent = `Same ${snapshot.status} supply scenario; a new reproducible arrangement appears each Pacific day.`;
  return plan;
}

function setScenario(key) {
  current = key;
  const scenario = scenarios[key];
  const plan = updateDailyCopy();
  els.name.textContent = scenario.name;
  els.description.textContent = scenario.description;
  els.tempo.textContent = plan.bpm;
  els.harmony.textContent = scenario.harmony;
  els.texture.textContent = scenario.texture;
  els.title.textContent = scenario.title;
  els.bpm.textContent = `${plan.bpm} BPM`;
  els.path.setAttribute("d", scenario.path);
  els.now.textContent = `Ready to hear today’s ${scenario.name.toLowerCase()} variation`;
  document.querySelectorAll(".scenario-choice").forEach(button => {
    const selected = button.dataset.scenario === key;
    button.classList.toggle("is-selected", selected);
    button.setAttribute("aria-pressed", String(selected));
  });
  if (playing) stopMusic();
}

function tone(ctx, frequency, start, duration, gain, type = "sine") {
  const oscillator = ctx.createOscillator();
  const volume = ctx.createGain();
  oscillator.type = type;
  oscillator.frequency.setValueAtTime(frequency, start);
  volume.gain.setValueAtTime(.0001, start);
  volume.gain.exponentialRampToValueAtTime(gain, start + .04);
  volume.gain.exponentialRampToValueAtTime(.0001, start + duration);
  oscillator.connect(volume).connect(ctx.destination);
  oscillator.start(start);
  oscillator.stop(start + duration + .04);
  scheduled.push(oscillator);
}

function playMusic() {
  if (playing) {
    stopMusic();
    return;
  }
  audioContext ||= new (window.AudioContext || window.webkitAudioContext)();
  audioContext.resume();

  const scenario = scenarios[current];
  const plan = musicalPlan(scenario);
  const beat = 60 / plan.bpm;
  const now = audioContext.currentTime + .06;
  const measures = 4;
  const duration = measures * 8 * beat;

  playing = true;
  els.status.textContent = `Playing the ${plan.label} variation from the same illustrative scenario.`;
  els.heroStatus.textContent = "PLAYING";
  els.buttons.forEach(button => {
    button.setAttribute("aria-pressed", "true");
    const label = button.querySelector(".play-label");
    if (label) label.textContent = "Pause the pulse";
  });

  for (let step = 0; step < measures * 8; step++) {
    const at = now + step * beat / 2;
    const patternIndex = (step + plan.patternShift) % scenario.pattern.length;
    const frequency = scenario.chords[scenario.pattern[patternIndex]] * plan.octave;
    tone(audioContext, frequency, at, beat * .78, plan.melodicGain, plan.timbre);
    if (step % 4 === 0) tone(audioContext, scenario.chords[0] / 2, at, beat * 1.55, .045, "sine");
    if (step % 8 === 5) tone(audioContext, scenario.chords[1] * 2, at, beat * .22, .008, "sine");
  }

  const started = performance.now();
  function paintProgress(nowMs) {
    if (!playing) return;
    const ratio = Math.min(1, (nowMs - started) / (duration * 1000));
    els.progress.style.width = `${ratio * 100}%`;
    if (ratio < 1) requestAnimationFrame(paintProgress);
  }
  requestAnimationFrame(paintProgress);
  endTimer = window.setTimeout(stopMusic, duration * 1000 + 180);
}

function stopMusic() {
  scheduled.forEach(node => {
    try { node.stop(); } catch (_) {}
  });
  scheduled = [];
  clearTimeout(endTimer);
  playing = false;
  els.status.textContent = "This Pacific-day variation stays the same for every visitor today.";
  els.heroStatus.textContent = "LISTENING MODE";
  els.progress.style.width = "0";
  els.buttons.forEach(button => {
    button.setAttribute("aria-pressed", "false");
    const label = button.querySelector(".play-label");
    if (label) label.textContent = "Play the pulse";
  });
}

document.querySelectorAll(".scenario-choice").forEach(button => {
  button.addEventListener("click", () => setScenario(button.dataset.scenario));
});
els.buttons.forEach(button => button.addEventListener("click", playMusic));
setScenario(current);
