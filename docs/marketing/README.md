# FairMind marketing assets

All claims come from [collateral/FACTS.md](collateral/FACTS.md). Update that file first when the product changes, then rebuild.

| Folder | What | Rebuild |
|---|---|---|
| [promo-video/](promo-video/) | 63s launch promo, 4:5 and 16:9, SRT, post copy | `npx hyperframes render` in `composition/` and `composition-16x9/` |
| [videos/](videos/) | Teaser (9:16, 1:1), intro (16:9, 4:5), three feature shorts (find, evidence, decide; 4:5), post copy | edit `specs.mjs`, then `node build.mjs && ./render-all.sh` |
| [collateral/social/](collateral/social/) | Feed posters, square posts, banners (LinkedIn, X, YouTube), link card, A3 event poster | `node kit/render.mjs <page>.html <out>.png W H` from `collateral/` |
| [collateral/sheets/](collateral/sheets/) | Spec sheet (A4, 2pp), data sheet (A4), comparison (A4 landscape) | `node kit/render.mjs sheets/<x>.html sheets/<x>.pdf A4` |
| [collateral/kit/](collateral/kit/) | Brand tokens, Figtree, mark, renderer | |

Product footage is cut from the docs tour recordings (`apps/docs/public/media/app/`, Git LFS). Music is synthesised by `compose.py`, no samples.
