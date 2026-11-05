# Chain of Custody Ghost theme

The theme for blog.fairmind.xyz: a calm editorial publication of guides to AI regulation, security and safety. The design system is in `DESIGN.md`; the direction contract is in `.impeccable/surfaces/apps-blog-theme.md` at the repo root.

## Package and upload

```bash
cd apps/blog-theme
npx gscan --v6 .
zip -r ../../chain-of-custody.zip . -x 'README.md' 'DESIGN.md' '.*' '.impeccable/*'
```

Upload the zip in Ghost Admin under Settings, Design and branding, Change theme, Upload theme, then activate it.

## Ghost setup the theme expects

| Item | Setting |
|---|---|
| Primary navigation | Latest `/`, Frameworks `/frameworks/`, Deadlines `/docket/`, About `/about/` |
| Pages | `frameworks` (uses `page-frameworks.hbs`), `docket`, `about`. Content for each is in `docs/marketing/blog-drafts/`. |
| Accent colour | `#0b6b52`, so Ghost's search and sign-up pop-ups match the theme |
| Framework tags | Listed in the theme setting `topic_tags`. Make the framework the post's first (primary) tag, and give the tag a description. |
| Author bio | Fill in the author's bio under Settings, Staff; it appears at the end of every guide |

## What the theme reads from Ghost

| On screen | Where it comes from |
|---|---|
| Lead story and feed | Published posts, newest first |
| Next deadline line, framework next dates | The `docket` page. Each list item is a bold date, a title, a colon and a note, for example `**2 Dec 2026** EU AI Act, Art. 50(2): Marking applies.` A framework's date is the first upcoming item whose title contains the framework's name or its acronym (DPDP, OWASP). |
| Deadlines page | The same list, shown as written, with days left added to each entry |
| Primary sources count | Items in the list under the guide's "Sources" heading |
| Keep reading | The three most recent other guides |
| Newsletter copy | Theme settings in Design and branding |
