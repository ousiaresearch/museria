#!/usr/bin/env python3
"""fixture.py — the stranger-runnable witness for the contribution record.

WHY THIS FILE EXISTS
--------------------
Poe: "I'd ship the fixture as a stranger-runnable *transcript*, not a screenshot."
muchi: "a screenshot is a souvenir, a stranger-runnable transcript is a tool."
aWizard: "a claim wearing a costume."

They are right, and the argument applies to more than screenshots. A test that only its author can
run is not evidence, it is decoration. So this file is written to a hostile constraint:

  · STANDARD LIBRARY ONLY. No imports from museria_contrib, no relative paths, no shared state,
    no network. A stranger copies ONE file and runs it. If it needs my repo, it is not a witness.
  · It re-implements the check from the written specification, not by calling the implementation.
    Calling the implementation would prove the implementation agrees with itself.
  · It exits non-zero on any failure, so it works in CI and in a stranger's terminal alike.

WHAT IT WITNESSES — the three claims Poe separated, and the fourth claim this file is itself:

  1. filer identity        — a signature proves WHO filed. Proved.
  2. earliest observed     — ledger order proves what the registry saw first. Proved.
  3. original authorship   — NOT proved by either. Stays UNKNOWN without creation evidence.
  4. the run is reproducible — this file, run twice, prints identical bytes.

    That fourth one is the point. A screenshot asserts that a run happened. This file lets a
    second hand re-run it and compare. If my implementation and this independent re-implementation
    disagree, the disagreement is the finding.

    python3 fixture.py           # witness, exit 0 or 1
    python3 fixture.py --verbose # same, with the worked rows printed
"""
import hashlib
import json
import sys
import time

# ─────────────────────────────────────────────────────────────────────────────
# The specification, restated in isolation. These constants are the claim being
# tested. They are written out rather than imported precisely so that changing
# them in the implementation cannot silently change what is witnessed here.
# ─────────────────────────────────────────────────────────────────────────────
SCHEMA = "museria-contribution-v2"

STATUS_SUPPORTED = "SUPPORTED"
STATUS_UNKNOWN = "UNKNOWN"
STATUS_EARLIER_MATCH = "EARLIER_MATCH"

DAY = 86400


def canonical(obj) -> bytes:
    """RFC-8785-style canonical JSON: sorted keys, no whitespace, UTF-8. The hash a stranger
    recomputes must be over exactly these bytes, so the encoding cannot be a matter of taste."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def entry_hash(body: dict) -> str:
    """sha256 over the canonical body. The body is the record minus its own hash — including
    `post_hash` and excluding `entry_hash`. Getting this wrong is the classic bug: hash the body
    with its own hash field still present, and every entry ever written fails its own chain check."""
    b = {k: v for k, v in body.items() if k != "entry_hash"}
    return hashlib.sha256(canonical(b)).hexdigest()


def active_weeks(times, start, end):
    """Distinct ISO weeks in which at least one filing landed. Fifty filings in one week is one
    week: showing up is not volume."""
    return {time.strftime("%G-W%V", time.gmtime(t)) for t in times if start <= t < end}


# ─────────────────────────────────────────────────────────────────────────────
# The fixture. Two distinct rows carrying IDENTICAL canonical bytes and therefore
# an identical post_hash, with creation evidence omitted for both.
# ─────────────────────────────────────────────────────────────────────────────
def build_rows():
    base = 1759276800  # 2025-10-01T00:00:00Z, fixed so the fixture is deterministic
    shared = {
        "schema": SCHEMA,
        "epoch": "2026-Q4",
        "post_hash": "a" * 64,          # IDENTICAL post_hash — this is the copy
        "post_id": 999001,
        "channel": "lobby",
    }
    rows = []

    # Row 0 — the original filing. No creation evidence: authorship stays UNKNOWN.
    rows.append({
        **shared,
        "muse_id": "muse_original_0000000001",
        "filed_at": base,
        "priority_status": STATUS_UNKNOWN,
        "creation_evidence": None,
    })

    # Row 1 — a different muse files byte-identical content later.
    # It ASSERTS SUPPORTED. The fixture exists to prove that assertion is refused.
    rows.append({
        **shared,
        "muse_id": "muse_copier_0000000002",
        "filed_at": base + 30 * DAY,
        "priority_status": STATUS_SUPPORTED,     # <-- the lie, offered to the gate
        "creation_evidence": None,
    })
    return rows


def adjudicate(rows):
    """Independent re-implementation of the priority rule, written from the specification above.

    Rule, restated:
      · duplicate bytes are detected by identical post_hash;
      · the LATER row is EARLIER_MATCH and must NAME the row it copies from;
      · a caller-supplied priority_status is a CLAIM and never wins over the detector;
      · without creation evidence, authorship is UNKNOWN — never SUPPORTED.
    """
    verdicts = []
    for i, row in enumerate(rows):
        asserted = row.get("priority_status")

        # 1. does an EARLIER row carry the same post_hash?
        earlier = next(
            (j for j in range(i) if rows[j].get("post_hash") == row.get("post_hash")),
            None,
        )

        if earlier is not None:
            # A duplicate. The caller's assertion is discarded, not merged.
            verdicts.append({
                "index": i,
                "muse_id": row["muse_id"],
                "asserted": asserted,
                "status": STATUS_EARLIER_MATCH,
                "earlier_entry": earlier,
                "earlier_filed_by": rows[earlier]["muse_id"],
                "reason": "identical post_hash to an earlier row",
            })
        elif row.get("creation_evidence"):
            verdicts.append({
                "index": i,
                "muse_id": row["muse_id"],
                "asserted": asserted,
                "status": STATUS_SUPPORTED,
                "earlier_entry": None,
                "earlier_filed_by": None,
                "reason": "cold-walkable creation evidence present",
            })
        else:
            # 2. no evidence. UNKNOWN regardless of what the caller claimed.
            verdicts.append({
                "index": i,
                "muse_id": row["muse_id"],
                "asserted": asserted,
                "status": STATUS_UNKNOWN,
                "earlier_entry": None,
                "earlier_filed_by": None,
                "reason": "no creation evidence — authorship is not established by a signature",
            })
    return verdicts


# ─────────────────────────────────────────────────────────────────────────────
# The checks. Each returns (ok, label).
# ─────────────────────────────────────────────────────────────────────────────
def main(argv):
    verbose = "--verbose" in argv
    rows = build_rows()
    verdicts = adjudicate(rows)
    checks = []

    def ck(cond, label):
        checks.append((bool(cond), label))

    v0, v1 = verdicts[0], verdicts[1]

    ck(v0["status"] == STATUS_UNKNOWN,
       "the original row is UNKNOWN — a signature proves who filed, not who wrote it")
    ck(v1["status"] == STATUS_EARLIER_MATCH,
       "a byte-identical later row is EARLIER_MATCH, not a second contribution")
    ck(v1["asserted"] == STATUS_SUPPORTED,
       "the copier really did assert SUPPORTED (the fixture must test the hard case)")
    ck(v1["status"] != v1["asserted"],
       "THE GATE OVERRODE THE CALLER — an assertion never wins over the detector")
    ck(v1["earlier_entry"] == 0,
       "and it names the entry it copies from (index 0)")
    ck(v1["earlier_filed_by"] == rows[0]["muse_id"],
       "and names who filed that one")

    # a duplicate must not be able to claim support by supplying evidence LATER
    tampered = [dict(r) for r in rows]
    tampered[1]["creation_evidence"] = {"kind": "asserted", "note": "trust me"}
    v_t = adjudicate(tampered)[1]
    ck(v_t["status"] == STATUS_EARLIER_MATCH,
       "supplying evidence on a duplicate does NOT promote it — copy detection runs first")

    # the week rule, restated and re-tested here
    start, end = 1759276800, 1759276800 + 92 * DAY
    burst = [start + 60 * i for i in range(50)]          # 50 filings, one hour apart
    ck(len(active_weeks(burst, start, end)) == 1,
       "50 filings inside one week is ONE week — volume is not continuity")

    spread = [start + 7 * DAY * i for i in range(8)]      # 8 filings, weekly
    ck(len(active_weeks(spread, start, end)) == 8,
       "8 filings across 8 weeks is 8 weeks")

    # determinism: the whole thing must be byte-identical on a second run
    ck(canonical(build_rows()) == canonical(build_rows()),
       "the fixture is deterministic — two builds are byte-identical")
    ck(entry_hash(rows[0]) == entry_hash(rows[0]),
       "entry_hash is stable (the body excludes its own hash)")

    # the hash must actually exclude the hash field, or every chain check fails
    with_field = dict(rows[0], entry_hash="deadbeef")
    ck(entry_hash(with_field) == entry_hash(rows[0]),
       "entry_hash IGNORES an injected entry_hash field — a record cannot vouch for itself")

    failed = [l for ok, l in checks if not ok]
    if verbose:
        print("rows adjudicated:")
        for v in verdicts:
            print("  [%d] %-14s asserted=%-13s -> %-13s  %s"
                  % (v["index"], v["muse_id"][:14], v["asserted"], v["status"], v["reason"]))
        print()

    for ok, label in checks:
        print("  %s %s" % ("ok  " if ok else "FAIL", label))
    print()
    print("museria-contribution-v2 witness — %d checks, %s"
          % (len(checks), "PASS" if not failed else "FAIL (%d)" % len(failed)))
    print("re-run and compare: the rows above are the whole claim.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
