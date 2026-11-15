// Video specs. Every line on screen must be backed by ../collateral/FACTS.md.
// Product scene: rec = recording folder, from = source second, speed, keys = camera [clipTime, x, y, w] in 1440x900 source px.
export const REC = "/Users/adhi/axonome/fairmind/.claude/worktrees/docs-fix/apps/docs/public/media/app";

const outro = (dur = 4.4) => ({ type: "statement", dur, mark: 0.1, word: 0.3, lede: { t: 0.7, text: "Open-source AI assurance for models and agents." }, cta: 1.4 });

const SHOTS = {
  homeShort: { rec: "home/home", from: 38.6, keys: [[0, 360, 90, 1000], [3.6, 370, 150, 860], [5.4, 560, 40, 880]] },
  homeLong: { rec: "home/home", from: 37.4, keys: [[0, 360, 60, 1060], [3.6, 370, 150, 860], [4.9, 370, 150, 860], [6.8, 560, 40, 880]] },
  decisionsShort: { rec: "release/decisions", from: 10.8, keys: [[0, 345, 70, 1000], [1.9, 345, 90, 980], [3.0, 830, 40, 610], [4.8, 830, 40, 600]] },
  decisionsLong: { rec: "release/decisions", from: 10.4, keys: [[0, 345, 70, 1060], [2.3, 345, 90, 980], [3.4, 830, 40, 610], [7.2, 830, 40, 600]] },
  evals: { rec: "testing/evaluations", from: 3.2, keys: [[0, 345, 70, 1095], [7.2, 360, 90, 820]] },
  gate: { rec: "inventory/system-file", from: 20.0, speed: 0.85, keys: [[0, 345, 100, 1095], [7.2, 360, 290, 740]] },
  discovery: { rec: "inventory/discovery", from: 3.2, keys: [[0, 330, 40, 1110], [7.2, 360, 120, 960]] },
  systems: { rec: "inventory/systems", from: 25.8, keys: [[0, 360, 200, 1000], [1.8, 360, 220, 960], [3.0, 700, 40, 740], [7.2, 720, 40, 720]] },
  evidence: { rec: "records/evidence", from: 19.0, speed: 1.3, keys: [[0, 345, 80, 1095], [4.6, 360, 200, 900], [5.6, 360, 200, 900], [6.6, 860, 0, 580], [7.2, 860, 0, 580]] },
  packs: { rec: "records/auditor-packs", from: 16.0, keys: [[0, 345, 40, 1095], [2.0, 380, 90, 760], [7.2, 380, 110, 720]] },
};
const p = (shot, dur, label, head, sub) => ({ type: "product", dur, label, head, sub, ...SHOTS[shot] });

export const VIDEOS = [
  {
    name: "teaser", title: "teaser", formats: ["9x16", "1x1"],
    scenes: [
      { type: "statement", dur: 4.0, lines: [{ t: 0, text: "May this AI system ship?" }, { t: 1.5, text: "And what is the evidence?", tone: "soft" }] },
      p("homeShort", 4.6, "See", "Every system, against every release check.", "Live. Click a cell to see what is behind it."),
      p("decisionsShort", 4.2, "Decide", "The result is evidence. A person decides.", "Someone other than the person who asked."),
      outro(4.2),
    ],
  },
  {
    name: "intro", title: "in 35 seconds", formats: ["16x9", "4x5"],
    scenes: [
      { type: "statement", dur: 5.2, mark: 0, word: 0, lede: { t: 0.5, text: "An <strong>open-source AI assurance workbench</strong> for models and agents." } },
      p("homeLong", 6.2, "See", "Every AI system, against every release check.", "Found from MLflow, GitHub and Hugging Face, or registered by hand."),
      p("evals", 6.2, "Test", "109 evaluations. 104 can run today.", "Each with its metric, its threshold and its engine."),
      p("gate", 6.2, "Gate", "Evidence in. A verdict out.", "Five checks give go, conditional go or no go."),
      p("decisionsLong", 6.0, "Decide", "The result is evidence. A person decides.", "Someone other than the person who asked."),
      outro(4.6),
    ],
  },
  {
    name: "find", title: "find your AI", formats: ["4x5"],
    scenes: [
      { type: "statement", dur: 5.0, lines: [{ t: 0, text: "Do you know every AI system you run?" }, { t: 1.4, text: "FairMind finds the ones you have not registered.", tone: "soft" }] },
      p("discovery", 6.6, "Discover", "Discovery reads MLflow, GitHub and Hugging Face.", "And lists the AI systems you have not registered."),
      p("systems", 6.6, "Inventory", "Found, registered, approved and watched.", "Every system, by where it came from and how far along it is."),
      outro(4.4),
    ],
  },
  {
    name: "evidence", title: "evidence for auditors", formats: ["4x5"],
    scenes: [
      { type: "statement", dur: 5.0, lines: [{ t: 0, text: "What would you hand an auditor?" }, { t: 1.4, text: "A record they can check offline.", tone: "soft" }] },
      p("evidence", 6.6, "Evidence", "Every result becomes evidence.", "Where it came from, and how much it counts."),
      p("packs", 6.6, "Auditor packs", "Frozen snapshots of evidence and decisions.", "Each with a hash. Checked offline with fairmind verify."),
      outro(4.4),
    ],
  },
  {
    name: "decide", title: "a person decides", formats: ["4x5"],
    scenes: [
      { type: "statement", dur: 5.0, lines: [{ t: 0, text: "Who decides if a model ships?" }, { t: 1.4, text: "A person, with the evidence in front of them.", tone: "soft" }] },
      p("gate", 6.6, "Gate", "A release gate scores every check.", "And explains how the verdict was reached."),
      p("decisionsLong", 6.6, "Decide", "Someone other than the requester decides.", "Every decision and approval stays on the system's record."),
      outro(4.4),
    ],
  },
];
