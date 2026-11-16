# FairMind notifier

A small app in the person's session that shows the FairMind agent's messages, for example that Cursor is signed in
with a personal account, and on request a page listing what the agent checks on this laptop, what it never does, and
every message it has shown. It reads nothing on the laptop beyond the serial number and the account name.

## How it works

1. Device management installs the binary, the start-at-login entry (`deploy/`) and `notifier.json` with FairMind's
   address and the organisation's notifier secret (Shadow AI > Laptops > FairMind agent).
   - macOS: `/Library/Application Support/FairMind/notifier.json`
   - Windows: `C:\ProgramData\FairMind\notifier.json`
2. On first run it enrols with the laptop's serial number and keeps its own key in the person's config folder (owner
   read-only). FairMind matches it to the agent on the same serial number.
3. Every minute it fetches new messages for this laptop, shows each as a system notification, and confirms it was
   shown so it never repeats. A message for someone else's account on a shared laptop is not shown.

`fairmind-notifier --once` runs one round without the menu bar icon, for device management checks.

## Build

```
cargo build --release
cargo test
```

## Before release

Release builds must be signed: an Apple Developer ID with notarisation for macOS, and a code-signing certificate for
Windows. Every person who installs it sees the signer's name. Who signs is still to be decided; development builds
are unsigned.
