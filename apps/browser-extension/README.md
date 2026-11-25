# FairMind browser extension

For Chrome and Edge, force-installed by device management. On the AI sites in `manifest.json` it checks whether
the signed-in account is a company one, compares the address with the company's domains and workspaces in the
browser, and sends FairMind only "work", "personal" or "unknown" per site, at most once a day. It never reads
prompts, other sites, passwords, cookies or sign-in tokens.

- `sites.js`: where each site shows the signed-in account, and the work or personal decision
- `content.js`: runs on those sites only; reads the account and shows the optional banner
- `background.js`: holds the settings and the token, and sends the answers
- `popup.html`, `popup.js`: what it checks, today's answer per site, and what was sent
- `schema.json`: the settings device management installs (Shadow AI > Laptops > Browser extension creates them)

Settings: `url`, `token`, `organisation`, `domains`, `workspaces` (`chatgpt`, `claude`), `banner`, and `person`,
which device management fills in per person. Without `person`, the browser profile's account is used, then a
company account seen on one of the AI sites. With no settings installed the extension does nothing.

```
npm test
```

To try it, load the folder unpacked (`edge://extensions` or `chrome://extensions`, Developer mode). Branded
Chrome no longer loads unpacked extensions from the command line; Edge and Chromium do.
