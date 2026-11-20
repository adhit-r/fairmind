// The "what it checks" page: the organisation, today's answer per site, and what was sent.
const LABEL = { work: "Company account", personal: "Other account" };
const UNKNOWN = { not_signed_in: "Not signed in", visit: "Opened", no_email: "Account not shown" };

// Today's answers draw first: reading managed settings can take a second or more when none are installed.
chrome.storage.managed.get(null).then((cfg) => {
  if (!cfg || !cfg.url || !cfg.token) return;
  const org = cfg.organisation || "your organisation";
  document.getElementById("title").textContent = cfg.organisation ? `FairMind for ${cfg.organisation}` : "FairMind";
  document.getElementById("intro").textContent = `Installed by ${org} so it can give you a company account for the AI tools you use. It never blocks anything.`;
}, () => {});

(async () => {
  const { results = {} } = await chrome.storage.local.get("results");
  const day = new Date().toISOString().slice(0, 10);
  const box = document.getElementById("today");
  const sent = [];
  for (const [key, site] of Object.entries(FairMindSites.SITES)) {
    const r = results[key] && results[key].day === day ? results[key] : null;
    const row = document.createElement("div");
    row.className = "row";
    const name = document.createElement("span");
    name.textContent = site.label;
    const chip = document.createElement("span");
    chip.className = `chip ${r ? r.class : ""}`;
    chip.textContent = r ? LABEL[r.class] || UNKNOWN[r.reason] || "Not known" : "Not opened today";
    row.append(name, chip);
    box.append(row);
    if (r && r.sent) sent.push(`${site.label}, ${(LABEL[r.class] || UNKNOWN[r.reason] || "not known").toLowerCase()}`);
  }
  if (sent.length) document.getElementById("sent").textContent = `Sent to FairMind today: ${sent.join("; ")}`;
})();
