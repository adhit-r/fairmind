// Holds the organisation's settings and sends each site's answer to FairMind, at most once a day per site.
// The token stays here; content scripts get only what they compare with.
importScripts("sites.js");

const today = () => new Date().toISOString().slice(0, 10);
const browserName = () => (navigator.userAgent.includes("Edg/") ? "edge" : "chrome");

/** The settings device management installed, or null when the extension was not set up by an organisation. */
async function settings() {
  const m = await chrome.storage.managed.get(null).catch(() => null);
  return m && m.url && m.token ? m : null;
}

/** Who this browser belongs to: the address device management filled in, the browser profile, or a company account seen here. */
async function person(cfg) {
  if (cfg.person) return cfg.person;
  try {
    const p = await chrome.identity.getProfileUserInfo({ accountStatus: "ANY" });
    if (p && p.email) return p.email;
  } catch (e) {
    // Edge and signed-out profiles have none
  }
  return (await chrome.storage.local.get("workEmail")).workEmail || null;
}

async function send(cfg, site, answer) {
  const who = await person(cfg);
  if (!who) return false;
  const body = { token: cfg.token, person: who, browser: browserName(), version: chrome.runtime.getManifest().version, sites: [{ site, class: answer.class, reason: answer.reason }] };
  // A plain-text POST needs no CORS preflight and no access to FairMind's host; the response is never read.
  return fetch(cfg.url, { method: "POST", mode: "no-cors", headers: { "Content-Type": "text/plain" }, body: JSON.stringify(body) }).then(
    () => true,
    () => false,
  );
}

async function handle(msg) {
  const cfg = await settings();
  if (!cfg || !FairMindSites.SITES[msg.site]) return null;
  const { results = {} } = await chrome.storage.local.get("results");
  const last = results[msg.site];
  const day = today();
  if (msg.type === "config") {
    if (last && last.day === day && last.sent) return { skip: true };
    return { domains: cfg.domains || [], workspaces: cfg.workspaces || {} };
  }
  if (msg.type !== "answer") return null;
  const answer = { class: msg.answer.class, reason: msg.answer.reason };
  if (msg.workEmail && FairMindSites.domainClass(msg.workEmail, cfg.domains || []) === "work") {
    await chrome.storage.local.set({ workEmail: msg.workEmail }); // kept in this browser, to name the person when nothing else does
  }
  const sent = FairMindSites.due(last && last.sent ? last : null, answer, day) ? await send(cfg, msg.site, answer) : true;
  const banner = !!cfg.banner && answer.class === "personal" && !(last && last.bannerDay === day);
  results[msg.site] = { day, class: answer.class, reason: answer.reason, sent, bannerDay: banner ? day : last && last.bannerDay };
  await chrome.storage.local.set({ results });
  return banner ? { banner: { site: FairMindSites.SITES[msg.site].label, organisation: cfg.organisation || null, domains: cfg.domains || [] } } : {};
}

chrome.runtime.onMessage.addListener((msg, _sender, reply) => {
  handle(msg).then(reply, () => reply(null));
  return true;
});
