# Chain of Custody Ghost theme

The theme for blog.fairmind.xyz: a dense reference portal of AI regulation guides. The design system is in `DESIGN.md`; the direction contract is in `.impeccable/surfaces/apps-blog-theme.md` at the repo root.

## Package and upload

```bash
cd apps/blog-theme
npx gscan .
zip -r ../../chain-of-custody.zip . -x 'mockup/*' 'README.md' 'DESIGN.md' '.*' '.impeccable/*'
```

Upload the zip in Ghost Admin under Settings, Design and branding, Change theme, Upload theme, then activate it.

## What the theme reads from Ghost

| On screen | Where it comes from |
|---|---|
| Frameworks (rail, footer) | Tags listed in the theme setting `topic_tags` (default `eu-ai-act,india,owasp,standards,assurance`). Only tags with published posts appear. Make the framework tag the post's first (primary) tag. |
| Browse by type | The `governance`, `security` and `safety` tags, when they have posts |
| Start here | The latest published guide; New guides lists the next three |
| Coming due, Deadlines page, header badge | The published page with slug `docket`. Each list item is a bold date, a title, a colon and a note, for example `**2 Dec 2026** EU AI Act, Art. 50(2): Marking applies.` Past dates drop off; dates within 30 days are red. |
| Next date in the rail | The first upcoming docket item whose title contains the framework's name or its acronym (DPDP, OWASP) |
| Sources count | Items in the list under the guide's "Sources" heading |
| New label | Guides published in the last 14 days |
| Deadline label | Posts tagged `deadline` |
| Header links | Primary navigation in Ghost settings |
| Newsletter and FairMind module copy | Theme settings in Design and branding |
