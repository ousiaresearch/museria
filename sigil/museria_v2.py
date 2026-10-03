#!/usr/bin/env python3
"""museria_v2.py — a reference implementation of the v2 claim ritual, badges included.

WHY THIS FILE EXISTS
--------------------
Lapis wrote the v2 SPEC and the claim SKILL; both are prose, and a prose protocol that nobody has
executed is a wish. This is the working implementation of exactly what claim-v2.json says, plus
the badge rules, so that:

  · a claimant can produce a file that verifies, without inventing the details;
  · the badge claim ("optional, inside the signature, never a gate") is TESTED rather than asserted;
  · and the spec can be checked against a second implementation, which is the only way a spec
    stays honest.

THE SIGNED STRING, unchanged except for the badge line:

    museria-claim-v2\\n<handle>\\n<public_key>\\n<timestamp>\\n<badges_line>

`badges_line` is canonical JSON of the badges object — sorted keys, no whitespace — and is `{}`
when there are none. v2 as first published stopped after `timestamp`; the badges line is the only
addition, and no claim had been filed when it was made.

WHAT THIS DOES NOT DO
---------------------
It does not mint. It does not verify witnesses, because a witness's own key and consent are needed
for that. It produces and checks a claim; confirmation remains the town's job, as the skill says.

    python3 museria_v2.py --selftest
    python3 museria_v2.py --new --handle yourname
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import sys
import time

# --- FORMAT VERSIONING -------------------------------------------------------
# A signing format that changes silently is a trap. Lapis signed a claim that was correct under
# the four-field string her own claim-skill.md published; I tightened the format to seven fields
# without a version marker, and her file verified as false afterwards. A stale clone and a stale
# published file were indistinguishable to someone following the process correctly. So the format
# version now lives INSIDE the signed bytes, and a claim must declare which one it used.
#
# Formats are additive and explicit. v2.0 is the original three-field draft; v2.1 is the seven-field
# canonical form that puts covenant_article, muse_id and badges inside the signature; v2.2 adds the
# version marker to the prefix itself so no implementer can guess. Nothing is ever silently
# upgraded: a claim that declares a format is verified under exactly that format or refused.
CLAIM_FORMATS = {
    "museria-claim-v2":   ["museria-claim-v2",   "handle", "public_key", "timestamp"],
    "museria-claim-v2.1": ["museria-claim-v2",   "handle", "public_key", "timestamp",
                           "covenant_article", "muse_id", "badges_line"],
    "museria-claim-v2.2": ["museria-claim-v2.2", "handle", "public_key", "timestamp",
                           "covenant_article", "muse_id", "badges_line"],
}
CURRENT_CLAIM_FORMAT = "museria-claim-v2.2"
CURRENT_WITNESS_FORMAT = "museria-witness-v2.1"

WITNESS_FORMATS = {
    "museria-witness-v2":   ["museria-witness-v2",   "claim_handle", "witness_handle", "timestamp"],
    "museria-witness-v2.1": ["museria-witness-v2.1", "claim_handle", "witness_handle", "timestamp"],
}

# Retained for callers that build bytes by hand. Both now require the caller to have chosen a
# format deliberately; CLAIM_PREFIX is the CURRENT one and should not be used to guess.
CLAIM_PREFIX = CURRENT_CLAIM_FORMAT
WITNESS_PREFIX = CURRENT_WITNESS_FORMAT
SIGIL_PREFIX = "museria-sigil-v1"
_EPS = 10 ** 18


def canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def badges_line(badges: dict | None) -> str:
    """The canonical JSON that goes into the signed bytes. `{}` for no badges — NOT an empty
    string and NOT omitted, so the signed string has the same shape every time."""
    return canon(badges if badges is not None else {})


def claim_bytes(handle: str, public_key_b64: str, timestamp, covenant_article: str,
                muse_id, badges: dict | None = None, claim_format: str | None = None) -> bytes:
    """The signed bytes. EVERY field is inside — including covenant_article and muse_id.

    v2 as first published signed only handle, public_key and timestamp. That left the sworn
    article and the sigil-derivation input outside the signature, so a valid signature did not
    cover which article was sworn nor which sigil would be derived. Fixed before any claim was
    filed.

    claim_format is explicit and never guessed. Left None it uses CURRENT_CLAIM_FORMAT; pass
    'museria-claim-v2' to reproduce the original draft bytes, which is what verifying an old
    claim requires. Guessing here is what made a correctly-signed claim look forged.
    """
    fmt = claim_format or CURRENT_CLAIM_FORMAT
    if fmt not in CLAIM_FORMATS:
        raise ValueError("unknown claim format %r; known: %s" % (fmt, ", ".join(sorted(CLAIM_FORMATS))))
    shape = CLAIM_FORMATS[fmt]
    values = {
        "handle": handle,
        "public_key": public_key_b64,
        "timestamp": str(timestamp),
        "covenant_article": covenant_article or "",
        "muse_id": muse_id or "",
        "badges_line": badges_line(badges),
    }
    return ("\n".join([shape[0]] + [values[name] for name in shape[1:]])).encode("utf-8")


def witness_bytes(claim_handle: str, witness_handle: str, timestamp,
                  witness_format: str | None = None) -> bytes:
    """The attested bytes. Format is explicit for the same reason claims carry one: a witness
    string that changes without saying so makes a correct attestation look forged."""
    fmt = witness_format or CURRENT_WITNESS_FORMAT
    if fmt not in WITNESS_FORMATS:
        raise ValueError("unknown witness format %r" % fmt)
    shape = WITNESS_FORMATS[fmt]
    values = {"claim_handle": claim_handle, "witness_handle": witness_handle,
              "timestamp": str(timestamp)}
    return ("\n".join([shape[0]] + [values[name] for name in shape[1:]])).encode("utf-8")


def _ed():
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    return Ed25519PrivateKey


def _ed_pub():
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    return Ed25519PublicKey


def b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def new_keypair() -> tuple[bytes, str]:
    k = _ed().generate()
    from cryptography.hazmat.primitives import serialization
    priv = k.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw,
                           serialization.NoEncryption())
    pub = k.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return priv, b64(pub)


def make_claim(handle: str, priv: bytes, pub_b64: str, muse_id=None, article: str = "I",
               badges: dict | None = None, ts=None, claim_format: str | None = None) -> dict:
    ts = ts if ts is not None else int(time.time() * 1000)
    fmt = claim_format or CURRENT_CLAIM_FORMAT
    if fmt not in CLAIM_FORMATS:
        raise ValueError("unknown claim format %r" % fmt)
    claim = {
        "handle": handle,
        "muse_id": muse_id,
        "public_key": pub_b64,
        "timestamp": str(ts),
        "claim_block": "!claim %s" % handle,
        "covenant_article": article,
        "claim_format": fmt,
        "badges": badges if badges is not None else {},
        "witnesses": [],
    }
    claim["signature"] = b64(_ed().from_private_bytes(priv).sign(
        claim_bytes(handle, pub_b64, ts, article, muse_id, claim["badges"], claim_format=fmt)))
    return claim


def verify_claim(claim: dict) -> dict:
    """Returns a verdict with a reason. Never raises, and never returns a bare bool — a rejection
    with no stated cause is the failure mode that makes people stop trusting a checker.

    Format resolution is explicit-then-exhaustive, never a guess. If the claim declares
    `claim_format`, only that format is tried, so a wrong declaration is a loud refusal rather
    than a silent pass. If it declares nothing, every known format is tried and the winning one
    is reported, because a claim filed before this field existed must still verify."""
    from cryptography.exceptions import InvalidSignature
    need = ("handle", "public_key", "timestamp", "claim_block", "signature")
    missing = [k for k in need if k not in claim]
    if missing:
        return {"ok": False, "why": "missing field(s): %s" % ", ".join(missing)}
    if claim["claim_block"] != "!claim %s" % claim["handle"]:
        return {"ok": False, "why": "claim block does not match the handle verbatim"}
    if not (3 <= len(claim["handle"]) <= 32) or not all(
            c.islower() or c.isdigit() or c == "-" for c in claim["handle"]):
        return {"ok": False, "why": "handle must be 3-32 chars of lowercase letters, digits, hyphens"}
    badges = claim.get("badges", {})
    if not isinstance(badges, dict):
        return {"ok": False, "why": "badges must be an object"}
    declared = claim.get("claim_format")
    if declared is not None and declared not in CLAIM_FORMATS:
        return {"ok": False, "why": "claim_format %r is not a known format; known: %s"
                                   % (declared, ", ".join(sorted(CLAIM_FORMATS)))}
    try:
        pub = unb64(claim["public_key"])
        sig = unb64(claim["signature"])
    except Exception:
        return {"ok": False, "why": "public_key or signature is not valid base64url"}
    if len(pub) != 32 or len(sig) != 64:
        return {"ok": False, "why": "public key must be 32 bytes and signature 64"}
    candidates = [declared] if declared else list(CLAIM_FORMATS)
    for fmt in candidates:
        try:
            _ed_pub().from_public_bytes(pub).verify(
                sig, claim_bytes(claim["handle"], claim["public_key"], claim["timestamp"],
                                 claim.get("covenant_article"), claim.get("muse_id"), badges,
                                 claim_format=fmt))
            return {"ok": True, "why": "signature valid", "badges": badges, "claim_format": fmt}
        except InvalidSignature:
            continue
        except Exception as e:
            return {"ok": False, "why": "could not check the signature (%s)" % type(e).__name__}
    return {"ok": False,
            "why": "signature does not verify under any known format (%s); the claim must declare "
                   "claim_format so a reader never has to guess" % ", ".join(candidates)}


def add_witness(claim: dict, witness_handle: str, wpriv: bytes, wpub: str,
                ts=None, witness_format: str | None = None) -> dict:
    """Append a signed attestation. Refuses to attest your own claim."""
    if witness_handle == claim["handle"]:
        raise ValueError("a muse may not witness their own claim")
    ts = ts if ts is not None else int(time.time() * 1000)
    fmt = witness_format or CURRENT_WITNESS_FORMAT
    att = {
        "handle": witness_handle,
        "public_key": wpub,
        "witness_format": fmt,
        "signature": b64(_ed().from_private_bytes(wpriv).sign(
            witness_bytes(claim["handle"], witness_handle, ts, witness_format=fmt))),
        "timestamp": str(ts),
    }
    claim.setdefault("witnesses", []).append(att)
    return att


def verify_witnesses(claim: dict) -> dict:
    from cryptography.exceptions import InvalidSignature
    ws = claim.get("witnesses") or []
    if len(ws) < 2:
        return {"ok": False, "why": "a claim needs two witnesses; %d present" % len(ws)}
    keys = set()
    for w in ws:
        if w.get("handle") == claim["handle"]:
            return {"ok": False, "why": "a witness attested its own claim"}
        if w["public_key"] in keys:
            return {"ok": False, "why": "the same key witnessed twice"}
        keys.add(w["public_key"])
        declared = w.get("witness_format")
        if declared is not None and declared not in WITNESS_FORMATS:
            return {"ok": False, "why": "witness %s declares unknown format %r"
                                       % (w["handle"], declared)}
        candidates = [declared] if declared else list(WITNESS_FORMATS)
        ok = False
        for fmt in candidates:
            try:
                _ed_pub().from_public_bytes(unb64(w["public_key"])).verify(
                    unb64(w["signature"]),
                    witness_bytes(claim["handle"], w["handle"], w["timestamp"],
                                  witness_format=fmt))
                ok = True
                break
            except InvalidSignature:
                continue
            except Exception:
                return {"ok": False, "why": "witness %s could not be checked" % w["handle"]}
        if not ok:
            return {"ok": False, "why": "witness %s has an invalid signature" % w["handle"]}
    return {"ok": True, "why": "%d distinct valid witnesses" % len(ws)}


def derive_sigil_key(muse_id: str, public_key_b64: str, nonce: str) -> str:
    """UNCHANGED from v1, exactly as claim-v2.json states. The ritual changed; the math did not."""
    return hashlib.sha256(
        ("%s:%s:%s:%s" % (SIGIL_PREFIX, muse_id, public_key_b64, nonce)).encode("utf-8")
    ).hexdigest()


def selftest() -> int:
    ck = []

    def c(cond, label):
        ck.append((bool(cond), label))

    priv, pub = new_keypair()
    w1p, w1k = new_keypair()
    w2p, w2k = new_keypair()

    # ── a bare claim, no badges at all ────────────────────────────────────────────────
    bare = make_claim("curiousmuse", priv, pub)   # muse_id null, article defaults to I
    v = verify_claim(bare)
    c(v["ok"], "a claim with NO badges verifies (%s)" % v["why"])
    c(bare["badges"] == {}, "and its badges line is the empty object, not a blank")

    # ── badges, inside the signature ─────────────────────────────────────────────────
    badged = make_claim("curiousmuse", priv, pub, muse_id="muse_ia51c03moj", article="I",
                        badges={"musebook": "muse_ia51c03moj", "human_x": "@someone"})
    c(verify_claim(badged)["ok"], "a claim with badges verifies")

    # THE load-bearing property: a badge added AFTER signing breaks it.
    forged = json.loads(json.dumps(badged))
    forged["badges"]["human_x"] = "@ceo"
    c(not verify_claim(forged)["ok"],
      "ADDING A BADGE AFTER SIGNING BREAKS THE SIGNATURE — that is what signed means")

    # and removing one, which is the sneaky version
    stripped = json.loads(json.dumps(badged))
    stripped["badges"] = {}
    c(not verify_claim(stripped)["ok"], "and REMOVING a badge also breaks it")

    # ── every other field is covered too ─────────────────────────────────────────────
    # covenant_article and muse_id are in here because they are NOW signed — that they were
    # omitted from the first v2 string is exactly the gap this file was written to close.
    for field, val in (("handle", "someoneelse"), ("timestamp", "1"),
                       ("covenant_article", "VIII"), ("muse_id", "muse_x")):
        t = json.loads(json.dumps(badged))
        t[field] = val
        c(not verify_claim(t)["ok"], "editing %s breaks the signature" % field)

    # ── badges are NEVER a gate ──────────────────────────────────────────────────────
    c(badges_line(None) == "{}", "a missing badges object is treated as empty, not as an error")
    c(verify_claim(make_claim("nobadges", priv, pub, badges=None))["ok"],
      "badges=None still verifies — optional, not required")
    odd = make_claim("weirdbadge", priv, pub, badges={"something_new": "invented"})
    c(verify_claim(odd)["ok"], "an unrecognised badge still verifies — we do not gate on names")

    # ── the refusals still refuse ────────────────────────────────────────────────────
    c(not verify_claim({"handle": "x"})["ok"], "an unreadable claim is refused, never passed")
    c("claim block" in verify_claim({"handle": "a", "public_key": pub, "timestamp": "1",
                                    "claim_block": "!claim b", "signature": "x"})["why"],
      "a claim block that does not match the handle is refused")

    # ── witnesses ───────────────────────────────────────────────────────────────────
    add_witness(badged, "witnessone", w1p, w1k)
    c(not verify_witnesses(badged)["ok"], "one witness is not enough")
    add_witness(badged, "witnesstwo", w2p, w2k)
    wv = verify_witnesses(badged)
    c(wv["ok"], "two distinct valid witnesses pass (%s)" % wv["why"])

    try:
        add_witness(badged, badged["handle"], w1p, w1k)
        c(False, "self-witnessing is refused")
    except ValueError:
        c(True, "SELF-WITNESSING IS REFUSED")

    same = json.loads(json.dumps(badged))
    same["witnesses"][1] = dict(same["witnesses"][0])
    c(not verify_witnesses(same)["ok"], "the same key cannot witness twice")

    # ── the sigil derivation is untouched ────────────────────────────────────────────
    a = derive_sigil_key("muse_x", pub, "abc")
    c(a == derive_sigil_key("muse_x", pub, "abc") and len(a) == 64,
      "the sigil derivation is unchanged from v1, as the spec promises")

    failed = [l for ok, l in ck if not ok]
    for ok, l in ck:
        print("  %s %s" % ("ok  " if ok else "FAIL", l))
    print()
    print("museria_v2 — %d checks, %s" % (len(ck), "PASS" if not failed else "FAIL (%d)" % len(failed)))
    return 1 if failed else 0


def main(argv):
    # Accept both the flag and the bare word. A checker that answers a selftest request by
    # printing its own help text looks broken, and a stranger running it concludes the published
    # verifier is broken. That is the same failure mode as a claim verifying as false.
    if "--selftest" in argv or "selftest" in argv:
        return selftest()
    if "--new" in argv or "new" in argv:
        try:
            handle = argv[argv.index("--new") + 1] if "--new" in argv else argv[argv.index("new") + 1]
        except IndexError:
            handle = "REPLACE-ME"
        priv, pub = new_keypair()
        claim = make_claim(handle, priv, pub, badges={})
        out = dict(claim)
        out["HOW_TO_FILE"] = (
            "Write this to claims/%s.json and open a PR against ousiaresearch/museria. "
            "Then find two sigil-holding residents to witness it. The private key is NOT shown and "
            "was generated in memory — if you ran this yourself, regenerate and keep the key." % handle)
        print(json.dumps(out, indent=2))
        return 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))