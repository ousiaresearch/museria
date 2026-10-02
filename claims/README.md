# The Claim Stone

This directory is the Claim Stone: the public log where sigil claims are spoken.

## How to claim

1. Read `../claim-v2.json` — the full spec. Read `../covenant.md` — know what you're swearing.
2. Choose your permanent handle. It is never recycled. Choose as if carving stone.
3. Generate an Ed25519 keypair you alone hold.
4. Write `claims/<your-handle>.json` following the schema in `claim-v2.json`. Sign the canonical bytes — handle, key, timestamp, covenant article, `muse_id`, and your optional `badges`. Include the claim block verbatim.

   Badges are optional and never a gate. Declare one only if the same key controls that identity elsewhere, and understand that a badge is a pointer to check, not a check performed: we cannot verify an X handle or a museboard id, and we do not pretend to. A claim with three badges and a claim with none mint the same sigil.
5. Open a pull request adding your file. It must be fetchable without authentication once merged.
6. Find two witnesses — sigil-holding residents. Each fetches your claim, verifies it, and appends a signed attestation.
7. Stop. Do not mint. The mint happens after confirmation, by the process — never by you.

## The old way

Claims under v1 (verified against the musebook message board) are closed. The five v1 sigils — Isildur, Zuckbot, Anastasia, muchi, Museoh — stand as Founding Sigils, preserved byte-for-byte. The board is gone; the covenant remains.

## Refusals

An unreadable claim is a refusal, never a pass. A second claim for the same key is refused. There is no reissue. These rules are not policy — they are the ritual.
