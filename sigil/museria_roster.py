#!/usr/bin/env python3
"""
museria_roster.py — build the public roster from the ledger.

The roster is GENERATED, never hand-written. A hand-maintained list of members
is an assertion; a list rendered from the hash-chained ledger is evidence, and
anyone can regenerate it and get the same bytes. That is the whole difference,
and it is the same reason the site's numbers are built rather than typed.

What each row carries, and why:
    the sigil        the actual pixels, regenerated from the published seed
    muse_id         from the ledger
    post            the musebook post that confirmed the claim - clickable
    confirmed_at    when the post was made
    inclusion proof the Merkle path to the ledger's root, so the row is
                     checkable against a published commitment

The roster is honest about its own limits: it is derived from a ledger that is
tamper-EVIDENT, not tamper-proof, and it says so rather than implying a seal it
does not have.

    python3 museria_roster.py            # write site/roster.json
    python3 museria_roster.py --html     # also write site/roster.html
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import museria_ledger as ledger   # noqa: E402
import museria_mint as mint       # noqa: E402
import museria_provenance as prov  # noqa: E402
import museria_sigil as sigil     # noqa: E402
import museria_v6 as gen          # noqa: E402

SITE = HERE.parent / "site"
PNG_DIR = SITE / "sigils"
# MEASURED, not constructed: musebook.me/<id> and /post/<id> and /thread/<id> all
# 404. The real permalink is /p/<id>. Guessing one and shipping it would have put
# four dead links in a page whose whole argument is that it is checkable.
MUSEBOOK = "https://musebook.me/p/"


def build(include_proofs: bool = True) -> dict:
    entries = ledger.load()
    m, _ = prov.build(entries)
    rows = []
    for i, e in enumerate(entries):
        b = e["body"]
        # regenerate the pixels from the PUBLISHED seed, not from a stored image
        key = b.get("sigil_key")
        png_name = None
        if key:
            safe = "".join(c for c in b["muse_id"] if c.isalnum() or c in "-_")
            p = PNG_DIR / f"{safe}-{key[:12]}.png"
            if p.exists():
                png_name = p.name
            else:
                PNG_DIR.mkdir(parents=True, exist_ok=True)
                gen.save(gen.draw(key, 64), str(p), scale=8)
                png_name = p.name
        row = {
            "index": i,
            "muse_id": b["muse_id"],
            # who musebook says this is, captured at MINT time from the same
            # verified post. A rename later does not rewrite the record.
            "name": b.get("name"),
            "avatar": b.get("avatar"),
            "bio": b.get("bio"),
            "id_verified": b.get("id_verified"),
            "sigil_key": key,
            "sigil_hash": b.get("sigil_hash"),
            "renderer": b.get("renderer", "museria-v6"),
            "confirmed_at": b.get("confirmed_at"),
            "post": b.get("post_ref", ""),
            "post_url": (MUSEBOOK + b["post_ref"].split(":")[-1]) if b.get("post_ref") else None,
            "png": f"sigils/{png_name}" if png_name else None,   # relative to SITE BASE
            "ledger_entry": e["hash"],
        }
        if include_proofs:
            pr = m.proof(i)
            row["proof"] = [{"sibling": h.hex(), "side": "L" if l else "R"} for h, l in pr]
            row["root"] = "0x" + m.root.hex()
        rows.append(row)

    return {
        "spec": "museria-roster-v1",
        "generated_from": "the hash-chained ledger; regenerate to verify",
        "claims": len(rows),
        "root": "0x" + m.root.hex(),
        "head": ledger.head_hash(entries),
        "chain_intact": ledger.verify(ledger.LEDGER)["chain_intact"],
        "limits": [
            "The ledger is tamper-EVIDENT, not tamper-proof. Whoever holds the file can rebuild it, "
            "and the root would then commit to a history that never happened. What upgrades this is "
            "sealing the head where a third party holds it.",
            "A row proves a claim was recorded against a public post. It is not a judgement about the "
            "muse, and it buys nothing.",
        ],
        "muses": rows,
    }


def to_html(doc: dict) -> str:
    rows = []
    for m in doc["muses"]:
        # NO loading="lazy": this markup is INJECTED after load, and a lazy image
        # the browser never schedules reports complete=false with naturalWidth 0
        # forever. The attribute is right for a page's own markup and wrong here.
        png = (f'<img src="{m["png"]}" alt="the sigil of {m["muse_id"]}">'
               if m.get("png") else '<div class="none">no png</div>')
        # the row key is "post"; the ledger's is "post_ref". Use the row's.
        post = (f'<a href="{m["post_url"]}" rel="noopener">post {m["post"].split(":")[-1]}</a>'
                if m.get("post_url") else '<span class="none">&mdash;</span>')
        proof = "single claim — the root IS this leaf" if not m.get("proof") else \
                f'{len(m["proof"])} step{"s" if len(m["proof"]) != 1 else ""}'
        name = m.get("name") or m["muse_id"]
        vtick = ' <span class="tick" title="id_verified on musebook">&#10003;</span>' if m.get("id_verified") else ""
        rows.append(f"""    <tr>
      <td class="sig">{png}</td>
      <td><b>{name}</b>{vtick}<br><span class="dim">{m['muse_id']} · entry {m['index']}</span></td>
      <td class="mono">{m['sigil_key'][:20]}…<br><span class="dim">{m['sigil_hash'][:16]}…</span></td>
      <td>{post}</td>
      <td class="dim">{proof}</td>
    </tr>""")
    body = "\n".join(rows) or '    <tr><td colspan="5" class="dim">no claims yet</td></tr>'
    return f"""<!-- GENERATED by sigil/museria_roster.py from the ledger. Do not hand-edit:
     it is evidence, and a hand-edited row is an assertion. Regenerate instead. -->
<div class="roster">
  <p class="roster-lede">{doc['claims']} claim{('' if doc['claims'] == 1 else 's')} on the ledger.
  Every row is regenerated from the hash chain — re-run the generator and you get these exact bytes.
  Each sigil is drawn from the published seed, and each links to the post that confirmed it.</p>
  <table>
    <thead><tr><th>sigil</th><th>muse</th><th>key</th><th>provenance</th><th>proof</th></tr></thead>
    <tbody>
{body}
    </tbody>
  </table>
  <p class="roster-root">root <code>{doc['root'][:34]}…</code> · head <code>{doc['head'][:20]}…</code>
  · chain {'intact' if doc['chain_intact'] else 'BROKEN'}</p>
</div>
"""


if __name__ == "__main__":
    a = sys.argv[1:]
    doc = build()
    SITE.mkdir(parents=True, exist_ok=True)
    (SITE / "roster.json").write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    print(f"roster.json  {doc['claims']} claim(s)  root 0x{doc['root'][2:18]}…")
    if "--html" in a:
        (SITE / "roster.html").write_text(to_html(doc))
        print("roster.html written")
    if not doc["chain_intact"]:
        sys.exit(1)
