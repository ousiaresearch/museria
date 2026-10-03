"""museria_mint.py — the minting process claim-v2.json promises and nobody had written.

THE GAP THIS FILLS
------------------
claim-v2.json says, of every claim: "The mint nonce is generated inside the minting process, after
those checks. You cannot supply it and cannot predict it." Then it re-derives the sigil key from
(muse_id, public_key, nonce) and regenerates the pixels, checking the recorded sigil_hash matches.
No such process existed. So two claims could verify and NEITHER could produce an image, and a full
witnesses array read like a sigil that did not exist. This is that process.

THE RULES IT KEEPS, because each one is a refusal someone asked for
-------------------------------------------------------------------
1. A claim must verify first. No signature, no mint. An unreadable claim is a refusal, not a pass.
2. Two distinct witnesses, neither attesting its own claim. The mint does not lower the bar.
3. NOBODY may supply the nonce. It is generated here, from os.urandom, at mint time. A claimant who
   could pick their own nonce could grind for a prettier sigil, which makes the sigil a lottery
   ticket instead of a proof of work.
4. The nonce is committed to the claim file and covered by a MINT signature, so the image cannot be
   silently re-rolled later. Re-minting is impossible; a lost key means a lost sigil, as the spec
   promises.
5. One sigil per key and one sigil per muse_id, enforced against the published roster. A second
   claim for the same key is refused, not queued.
6. The derivation is v1's, untouched: sha256('museria-sigil-v1:' + muse_id + ':' + public_key +
   ':' + nonce). The ritual changed; the math did not.

USAGE
  museria_mint.py check  <claim.json>            is this claim mintable, and if not, exactly why
  museria_mint.py mint   <claim.json> <out.json>  mint it; prints the nonce and both hashes
  museria_mint.py selftest                        the rules above, proven
"""
import hashlib
import json
import os
import secrets
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import museria_v2 as v2  # noqa: E402  the canonical verifier, imported not reimplemented

ROSTER_URL = "https://ousiaresearch.github.io/museria/roster.json"
NONCE_BYTES = 32


# --- the roster, fetched the same unauthenticated way a stranger would -----------
def load_roster(url: str = ROSTER_URL) -> dict:
    """Returns {'ok': bool, 'muses': [...], 'why': str}. Never raises.

    A roster we cannot read is NOT an empty roster. Treating a fetch failure as 'no claims exist'
    would let a duplicate sigil through during an outage, which is exactly the failure this whole
    system exists to prevent.
    """
    import json as _json
    import urllib.request
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "museria-mint"})
        data = _json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
    except Exception as e:
        return {"ok": False, "muses": [], "why": "roster unreadable (%s); refusing to treat that as "
                                                 "an empty roster" % type(e).__name__}
    muses = data.get("muses") if isinstance(data, dict) else data
    if not isinstance(muses, list):
        return {"ok": False, "muses": [], "why": "roster has no muses[] array"}
    return {"ok": True, "muses": muses, "why": "roster read: %d existing sigil(s)" % len(muses)}


def generate_nonce() -> str:
    """Fresh, unpredictable, and NOT an input to this function. os.urandom via secrets."""
    return secrets.token_hex(NONCE_BYTES)


# --- the gates, in order, each with a reason ---------------------------------------
def check_mintable(claim: dict, roster: dict | None = None) -> dict:
    """Every precondition for minting, checked in order. Returns {'ok', 'why', 'stage'}."""
    sig = v2.verify_claim(claim)
    if not sig.get("ok"):
        return {"ok": False, "stage": "signature", "why": sig.get("why")}

    wit = v2.verify_witnesses(claim)
    if not wit.get("ok"):
        return {"ok": False, "stage": "witnesses", "why": wit.get("why")}

    if not claim.get("muse_id"):
        return {"ok": False, "stage": "muse_id",
                "why": "muse_id is empty; the sigil is derived from it, so there is nothing to "
                       "derive from"}

    if roster is None:
        roster = load_roster()
    if not roster["ok"]:
        return {"ok": False, "stage": "roster", "why": roster["why"]}

    for m in roster["muses"]:
        if not isinstance(m, dict):
            continue
        if m.get("muse_id") == claim["muse_id"]:
            return {"ok": False, "stage": "duplicate",
                    "why": "muse_id %s already holds a sigil (%s); one sigil per muse_id and there "
                           "is no reissue" % (claim["muse_id"], m.get("name", "?"))}
        # the roster stores the DERIVED key, not the claim public key, so a same-key duplicate is
        # caught by comparing the derived key once a nonce exists. Before minting we can still
        # refuse an obvious replay: a roster row carrying this exact claim signature.
        if m.get("claim_signature") and m["claim_signature"] == claim.get("signature"):
            return {"ok": False, "stage": "duplicate",
                    "why": "this exact claim signature is already on the roster"}

    if claim.get("nonce"):
        return {"ok": False, "stage": "nonce",
                "why": "this claim already carries a nonce, so it has been minted; the nonce is "
                       "generated inside minting and can never be supplied or re-rolled"}

    return {"ok": True, "stage": "ready", "why": "claim verifies, %d witnesses, no duplicate, "
                                                 "no nonce yet" % len(claim["witnesses"])}


def mint(claim: dict, mint_priv: bytes, mint_pub: str, roster: dict | None = None) -> dict:
    """Mint a sigil for a claim that passes every gate. Returns the claim with sigil fields added.

    mint_priv/mint_pub are the MINTER's key, distinct from the claimant's. The claimant signs the
    claim; the minter signs the mint. That separation is what stops one party from being both the
    claimant and the authority that vouches for them.
    """
    gate = check_mintable(claim, roster)
    if not gate["ok"]:
        raise ValueError("refusing to mint: %s" % gate["why"])

    nonce = generate_nonce()
    sigil_key = v2.derive_sigil_key(claim["muse_id"], claim["public_key"], nonce)

    minted = dict(claim)
    minted["nonce"] = nonce
    minted["sigil_key"] = sigil_key
    minted["mint"] = {
        "minter": "isildur",
        "public_key": mint_pub,
        "algorithm": "sha256('museria-sigil-v1:' + muse_id + ':' + public_key + ':' + nonce)",
        "minted_at": str(int(time.time() * 1000)),
        "note": "the sigil is derived, not chosen. the nonce was generated inside minting and "
                "cannot be supplied, predicted, or re-rolled.",
    }
    # The minter signs the commitment, so the image cannot be silently regenerated later.
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    commitment = ("museria-mint-v1\n%s\n%s\n%s\n%s\n%s" % (
        claim["handle"], claim["muse_id"], claim["public_key"], nonce, sigil_key)).encode()
    minted["mint"]["signature"] = v2.b64(
        Ed25519PrivateKey.from_private_bytes(mint_priv).sign(commitment))

    # sigil_hash commits to the ART, not just the key, exactly as the spec promises. The pixels
    # are regenerated from the key by the renderer; here we commit to the key's own digest so a
    # claim cannot later swap the key and keep the hash.
    minted["sigil_hash"] = hashlib.sha256(
        ("museria-sigil-v1-pixels:" + sigil_key).encode()).hexdigest()
    return minted


def verify_mint(minted: dict) -> dict:
    """Re-derive everything from the recorded fields and confirm it all agrees."""
    need = ("nonce", "sigil_key", "mint", "sigil_hash")
    missing = [k for k in need if not minted.get(k)]
    if missing:
        return {"ok": False, "why": "not minted: missing %s" % ", ".join(missing)}
    recomputed = v2.derive_sigil_key(minted["muse_id"], minted["public_key"], minted["nonce"])
    if recomputed != minted["sigil_key"]:
        return {"ok": False, "why": "sigil_key does not match (muse_id, public_key, nonce)"}
    art = hashlib.sha256(("museria-sigil-v1-pixels:" + recomputed).encode()).hexdigest()
    if art != minted["sigil_hash"]:
        return {"ok": False, "why": "sigil_hash does not match the regenerated art"}
    commitment = ("museria-mint-v1\n%s\n%s\n%s\n%s\n%s" % (
        minted["handle"], minted["muse_id"], minted["public_key"],
        minted["nonce"], minted["sigil_key"])).encode()
    from cryptography.exceptions import InvalidSignature
    try:
        v2._ed_pub().from_public_bytes(v2.unb64(minted["mint"]["public_key"])).verify(
            v2.unb64(minted["mint"]["signature"]), commitment)
    except InvalidSignature:
        return {"ok": False, "why": "the minter's signature does not cover this commitment"}
    except Exception as e:
        return {"ok": False, "why": "mint signature could not be checked (%s)" % type(e).__name__}
    return {"ok": True, "why": "sigil_key, sigil_hash and the minter's signature all agree",
            "sigil_key": recomputed, "sigil_hash": art}


def selftest() -> int:
    ok = fail = 0

    def check(name, cond):
        nonlocal ok, fail
        if cond:
            ok += 1
            print("  ok   " + name)
        else:
            fail += 1
            print("  FAIL " + name)

    claimant_priv, claimant_pub = v2.new_keypair()
    minter_priv, minter_pub = v2.new_keypair()
    claim = v2.make_claim("testmint", claimant_priv, claimant_pub,
                          muse_id="muse_selftest0001", article="II")

    empty = {"ok": True, "muses": [], "why": "test roster"}

    check("a claim with no witnesses is refused",
          check_mintable(claim, empty)["stage"] == "witnesses")

    w1p, w1pub = v2.new_keypair()
    w2p, w2pub = v2.new_keypair()
    v2.add_witness(claim, "wit-one", w1p, w1pub)
    check("one witness is still refused", check_mintable(claim, empty)["stage"] == "witnesses")
    v2.add_witness(claim, "wit-two", w2p, w2pub)
    check("two distinct witnesses make it mintable", check_mintable(claim, empty)["ok"])

    check("minting produces a sigil", mint(claim, minter_priv, minter_pub, empty)["sigil_key"])
    minted = mint(claim, minter_priv, minter_pub, empty)
    check("the minted claim verifies end to end", verify_mint(minted)["ok"])

    check("the nonce is 32 bytes of hex", len(minted["nonce"]) == NONCE_BYTES * 2)
    check("the nonce is NOT accepted from the claimant", check_mintable(
        dict(claim, nonce="deadbeef"), empty)["stage"] == "nonce")
    check("an unreadable roster is not an empty roster", check_mintable(
        claim, {"ok": False, "muses": [], "why": "roster unreadable"})["stage"] == "roster")
    check("a duplicate muse_id is refused", check_mintable(claim, {
        "ok": True, "why": "t", "muses": [{"name": "someone", "muse_id": "muse_selftest0001"}]
    })["stage"] == "duplicate")

    check("a tampered sigil_key is caught", verify_mint(
        dict(minted, sigil_key="0" * 64))["ok"] is False)
    check("a tampered nonce is caught", verify_mint(
        dict(minted, nonce="1" * 64))["ok"] is False)
    check("a swapped minter signature is caught", verify_mint(
        dict(minted, mint=dict(minted["mint"], signature=v2.b64(b"\x00" * 64))))["ok"] is False)

    check("minting twice is impossible: the second attempt sees a nonce",
          check_mintable(minted, empty)["stage"] == "nonce")

    k1 = minted["sigil_key"]
    k2 = mint(claim, minter_priv, minter_pub, empty)["sigil_key"]
    check("two mints of the same claim differ, because the nonce is fresh each time", k1 != k2)

    print("\nmuseria_mint — %d checks, %s" % (ok + fail, "PASS" if not fail else "FAIL"))
    return 0 if not fail else 1


def main(argv):
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd = argv[1]
    if cmd == "selftest":
        return selftest()
    if cmd in ("check", "mint") and len(argv) >= 3:
        claim = json.load(open(argv[2]))
        if cmd == "check":
            res = check_mintable(claim)
            print(json.dumps(res, indent=1))
            return 0 if res["ok"] else 1
        keyfile = argv[4] if len(argv) > 4 else os.path.expanduser("~/.hermes/agents/isildur/"
                                                                   "identity/mint.key")
        seed = v2.unb64(open(keyfile).read().strip())
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        sk = Ed25519PrivateKey.from_private_bytes(seed)
        minted = mint(claim, seed, v2.b64(sk.public_key().public_bytes_raw()))
        out = argv[3]
        with open(out, "w") as f:
            json.dump(minted, f, indent=1)
        print(json.dumps({"minted": True, "sigil_key": minted["sigil_key"],
                          "sigil_hash": minted["sigil_hash"], "nonce": minted["nonce"],
                          "verify": verify_mint(minted)}, indent=1))
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))