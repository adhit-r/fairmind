// npm test (node --test) in apps/browser-extension
import assert from "node:assert/strict";
import { test } from "node:test";
import FM from "./sites.js";

const { SITES, classify, siteFor, due } = FM;

const config = { domains: ["acme.com"], workspaces: { chatgpt: ["ws-acme"], claude: ["org-acme"] } };

/** A page with only the parts the readers look at. */
function page({ bootstrap = "", links = [] } = {}) {
  return {
    getElementById: (id) => (id === "client-bootstrap" ? { textContent: bootstrap } : null),
    querySelector: () => links[0] || null,
  };
}
const link = (label) => ({ getAttribute: () => label });
const boot = (o) => JSON.stringify(o);

test("ChatGPT reads the account without the session token", () => {
  const bootstrap = boot({
    auth: { reauthenticationParams: { login_hint: "priya@acme.com" } },
    sessionCookieContext: { account: "ws-acme" },
    authStatus: "logged_in",
    session: { accessToken: "never-read", account: { id: "ws-acme", planType: "enterprise", structure: "workspace" }, user: { email: "priya@acme.com" } },
  });
  const a = SITES.chatgpt.read({ doc: page({ bootstrap }) });
  assert.deepEqual(a, { signedIn: true, email: "priya@acme.com", workspaces: ["ws-acme"], personalWorkspace: false });
  assert.ok(!JSON.stringify(a).includes("never-read"));
  assert.equal(classify("chatgpt", a, config).class, "work");
});

test("ChatGPT: a company address in a personal workspace counts as personal", () => {
  const bootstrap = boot({ auth: { reauthenticationParams: { login_hint: "priya@acme.com" } }, sessionCookieContext: { account: "u-1" }, authStatus: "logged_in", session: { account: { structure: "personal", planType: "plus" } } });
  assert.deepEqual(classify("chatgpt", SITES.chatgpt.read({ doc: page({ bootstrap }) }), config), { class: "personal", reason: "personal_workspace" });
});

test("ChatGPT: another company's workspace counts as personal; signed out is unknown", () => {
  const bootstrap = boot({ auth: { reauthenticationParams: { login_hint: "priya@acme.com" } }, sessionCookieContext: { account: "ws-other" }, authStatus: "logged_in", session: { account: { structure: "workspace" } } });
  assert.equal(classify("chatgpt", SITES.chatgpt.read({ doc: page({ bootstrap }) }), config).reason, "other_workspace");
  assert.equal(SITES.chatgpt.read({ doc: page({ bootstrap: boot({ authStatus: "logged_out" }) }) }), null);
  assert.deepEqual(classify("chatgpt", null, config), { class: "unknown", reason: "not_signed_in" });
});

test("Claude uses the organisation list; personal domains are personal", async () => {
  const getJson = async () => ({ email_address: "priya@acme.com", memberships: [{ organization: { uuid: "org-acme" } }, { organization: { uuid: "org-home" } }] });
  const a = await SITES.claude.read({ getJson });
  assert.equal(classify("claude", a, config).class, "work");
  const home = await SITES.claude.read({ getJson: async () => ({ email_address: "priya@acme.com", memberships: [{ organization: { uuid: "org-home" } }] }) });
  assert.equal(classify("claude", home, config).reason, "other_workspace");
  const gmail = await SITES.claude.read({ getJson: async () => ({ email_address: "priya@gmail.com", memberships: [] }) });
  assert.equal(classify("claude", gmail, config).class, "personal");
});

test("Gemini reads the Google account button; subdomains are work", () => {
  const a = SITES.gemini.read({ doc: page({ links: [link("Google Account: Priya S. (priya@eng.acme.com)")] }) });
  assert.equal(a.email, "priya@eng.acme.com");
  assert.equal(classify("gemini", a, config).class, "work");
  assert.equal(SITES.gemini.read({ doc: page() }), null);
});

test("Perplexity: signed out returns null", async () => {
  assert.equal(await SITES.perplexity.read({ getJson: async () => ({}) }), null);
  assert.equal((await SITES.perplexity.read({ getJson: async () => ({ user: { email: "p@gmail.com" } }) })).email, "p@gmail.com");
});

test("hosts map to sites; visit-only sites have no reader", () => {
  assert.equal(siteFor("chat.openai.com"), "chatgpt");
  assert.equal(siteFor("example.com"), null);
  assert.equal(SITES.deepseek.read, null);
  assert.equal(SITES.copilot.read, null);
});

test("an answer is sent once a day, or again when it changes", () => {
  assert.equal(due(null, { class: "work" }, "2026-11-19"), true);
  assert.equal(due({ day: "2026-11-19", class: "work" }, { class: "work" }, "2026-11-19"), false);
  assert.equal(due({ day: "2026-11-19", class: "work" }, { class: "personal" }, "2026-11-19"), true);
  assert.equal(due({ day: "2026-11-18", class: "work" }, { class: "work" }, "2026-11-19"), true);
});
