// Where each AI site shows the signed-in account, and how the extension reads it without touching a sign-in
// token, a password or a cookie. Checked by hand in Chrome on 2026-11-19 (see the notes per site).
//
// Loaded as a classic script by the content script and the background worker, and as CommonJS by the tests.
//
// A reader gets { doc, getJson } and returns { signedIn, email, workspaces } or null when the page shows no
// account. Only the email's domain and workspace ids are used afterwards; the address never leaves the browser.

const EMAIL = /[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+/;

/** First capture of re in text, or null. */
function pick(text, re) {
  const m = re.exec(text);
  return m ? m[1] : null;
}

// ChatGPT: the page's startup data, <script id="client-bootstrap">. The same block holds the session's sign-in
// token (session.accessToken), so the block is never parsed: named fields are cut out of the text instead.
//   auth.reauthenticationParams.login_hint   the account email (outside the session object)
//   sessionCookieContext.account             the active workspace id
//   session.account.structure / planType     "personal" or "workspace"; free, plus, team, enterprise ...
//   authStatus                               "logged_in" when signed in
function chatgpt({ doc }) {
  const t = doc.getElementById("client-bootstrap")?.textContent || "";
  if (!/"authStatus":"logged_in"/.test(t)) return null;
  const email = pick(t, /"login_hint":"([^"]+@[^"]+)"/) || pick(t, /"user":\{[^{}]*?"email":"([^"]+@[^"]+)"/);
  const workspace = pick(t, /"sessionCookieContext":\{[^{}]*?"account":"([^"]+)"/);
  const structure = pick(t, /"structure":"([a-z_]+)"/);
  return { signedIn: true, email, workspaces: workspace ? [workspace] : [], personalWorkspace: structure === "personal" };
}

// Claude: GET /api/account (the page's own session) returns email_address and every organisation the person
// belongs to, with no token in it. Which organisation is active is only in a cookie, so it is not read: the check
// is whether the person belongs to the company's organisation at all.
async function claude({ getJson }) {
  const a = await getJson("/api/account");
  if (!a || !a.email_address) return null;
  return { signedIn: true, email: a.email_address, workspaces: (a.memberships || []).map((m) => m.organization && m.organization.uuid).filter(Boolean) };
}

// Gemini: the Google account button, a link to accounts.google.com/SignOutOptions whose label names the account,
// "Google Account: <name> (<email>)". No request is made.
function gemini({ doc }) {
  const a = doc.querySelector('a[href^="https://accounts.google.com/SignOutOptions"][aria-label*="@"]');
  const email = a && pick(a.getAttribute("aria-label"), new RegExp(`(${EMAIL.source})`));
  return email ? { signedIn: true, email, workspaces: [] } : null;
}

// Perplexity: GET /api/auth/session, the page's own session endpoint; it returns {} when signed out and
// { user: { email } } when signed in. Only the signed-out answer has been seen so far.
async function perplexity({ getJson }) {
  const s = await getJson("/api/auth/session");
  const email = s && s.user && s.user.email;
  return email ? { signedIn: true, email, workspaces: [] } : null;
}

// Consumer Microsoft Copilot and DeepSeek: the visit is reported, the account is not. Copilot's signed-in page has
// not been seen yet (signed out, it shows a remembered account to sign in with, which is not a sign-in). DeepSeek
// fetches the account only with a token kept in the page, so it is never read.
const SITES = {
  chatgpt: { label: "ChatGPT", hosts: ["chatgpt.com", "chat.openai.com"], read: chatgpt },
  claude: { label: "Claude", hosts: ["claude.ai"], read: claude },
  gemini: { label: "Gemini", hosts: ["gemini.google.com"], read: gemini },
  perplexity: { label: "Perplexity", hosts: ["www.perplexity.ai", "perplexity.ai"], read: perplexity },
  copilot: { label: "Microsoft Copilot", hosts: ["copilot.microsoft.com", "copilot.com"], read: null },
  deepseek: { label: "DeepSeek", hosts: ["chat.deepseek.com"], read: null },
};

/** The site key for a host name, or null. */
function siteFor(host) {
  const h = String(host || "").toLowerCase();
  return Object.keys(SITES).find((k) => SITES[k].hosts.includes(h)) || null;
}

/** "work" when the domain is a company domain or one of its subdomains, "personal" otherwise, null for no email. */
function domainClass(email, domains) {
  const m = /^[^@\s]+@([^@\s]+)$/.exec(String(email || "").trim().toLowerCase());
  if (!m) return null;
  return domains.some((d) => m[1] === d || m[1].endsWith("." + d)) ? "work" : "personal";
}

/**
 * The answer sent to FairMind for one site: "work", "personal" or "unknown", and why. A company address on a
 * workspace that is not the company's counts as personal. Nothing else from the account leaves the browser.
 */
function classify(site, account, config) {
  if (!account) return { class: "unknown", reason: "not_signed_in" };
  const byDomain = domainClass(account.email, config.domains || []);
  if (!byDomain) return { class: "unknown", reason: "no_email" };
  const company = (config.workspaces || {})[site] || [];
  if (byDomain === "work" && site === "chatgpt" && account.personalWorkspace) return { class: "personal", reason: "personal_workspace" };
  if (byDomain === "work" && company.length && account.workspaces.length && !account.workspaces.some((w) => company.includes(w))) return { class: "personal", reason: "other_workspace" };
  return { class: byDomain, reason: "domain" };
}

/** Whether to send a site's answer now: the first answer of the day, or a changed one. */
function due(last, answer, today) {
  return !last || last.day !== today || last.class !== answer.class;
}

const FairMindSites = { SITES, siteFor, domainClass, classify, due };
if (typeof module !== "undefined") module.exports = FairMindSites;
