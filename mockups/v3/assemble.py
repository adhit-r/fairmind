import json, pathlib
here = pathlib.Path(__file__).parent
svg = (here / "lock/lock.svg").read_text()
anchors = json.loads((here / "lock/lock.json").read_text())
W, H = anchors["width"], anchors["height"]
pins = "".join(
    f'<a class="lockpin" href="#needs-title" style="left:{a["at"][0]/W*100:.2f}%;top:{a["at"][1]/H*100:.2f}%" aria-label="Chamber {a["chamber"]}: needs you, item {a["pin"]}"><b>{a["pin"]}</b><i></i></a>'
    for a in anchors["anchors"] if a["pin"]
)
iso_css = pathlib.Path("/Users/adhi/.claude/skills/anatomy/kit/iso.css").read_text()
lock_css = (here / "lock/lock.css").read_text()
page = (here / "page.template.html").read_text()
page = page.replace("{{LOCK_SVG}}", f'<div class="iso" data-theme="light" style="position:relative">{svg}</div>')
page = page.replace("{{LOCK_PINS}}", "")
# pins sit inside the iso wrapper so percentages track the drawing
page = page.replace(f'{svg}</div>', f'{svg}{pins}</div>')
page = page.replace("</style>", iso_css + "\n" + lock_css + "\n</style>", 1)
(here / "system-decision.html").write_text(page)
print("ok", len(page))
