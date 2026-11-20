// Runs on the AI sites in the manifest only. Reads who is signed in (sites.js), compares it with the company's
// domains and workspaces here, and hands the background worker only "work", "personal" or "unknown".
(async () => {
  const site = FairMindSites.siteFor(location.hostname);
  if (!site) return;
  const cfg = await chrome.runtime.sendMessage({ type: "config", site });
  if (!cfg || cfg.skip) return;

  const read = FairMindSites.SITES[site].read;
  let account = null;
  let answer = { class: "unknown", reason: "visit" };
  if (read) {
    const getJson = (path) => fetch(path, { credentials: "include" }).then((r) => (r.ok ? r.json() : null), () => null);
    // Pages that draw the account after loading get a few seconds; endpoints are asked once.
    const tries = site === "chatgpt" || site === "gemini" ? 10 : 1;
    for (let i = 0; i < tries && !account; i++) {
      account = await read({ doc: document, getJson });
      if (!account && i < tries - 1) await new Promise((r) => setTimeout(r, 1000));
    }
    answer = FairMindSites.classify(site, account, cfg);
  }
  const workEmail = answer.class === "work" && account ? account.email : null;
  const res = await chrome.runtime.sendMessage({ type: "answer", site, answer, workEmail });
  if (res && res.banner) showBanner(res.banner);
})();

/** A note at the top of the page, once a day, when the organisation turned it on. */
function showBanner({ site, organisation, domains }) {
  const host = document.createElement("div");
  host.style.cssText = "position:fixed;top:0;left:0;right:0;z-index:2147483647";
  const root = host.attachShadow({ mode: "closed" });
  const bar = document.createElement("div");
  bar.setAttribute("role", "status");
  bar.style.cssText =
    "display:flex;align-items:center;gap:14px;padding:12px 18px;background:#fff6ec;border-bottom:1px solid #f1dcc4;color:#15171a;font:14px/1.45 system-ui,sans-serif";
  const text = document.createElement("span");
  text.style.flex = "1";
  const who = organisation ? `${organisation}'s` : "your organisation's";
  const where = domains.length ? ` with your ${domains[0]} address` : " with your company account";
  text.textContent = `You are signed in to ${site} with an account that is not ${who}. Sign in${where} instead.`;
  const close = document.createElement("button");
  close.type = "button";
  close.textContent = "Not today";
  close.style.cssText = "min-height:40px;padding:0 16px;border-radius:999px;border:1px solid #dcdcd6;background:#fff;color:#15171a;font:600 13px system-ui,sans-serif;cursor:pointer";
  close.addEventListener("click", () => host.remove());
  bar.append(text, close);
  root.append(bar);
  document.documentElement.append(host);
}
