/* ===========================================================================
   museria-sigil.js — a faithful JavaScript port of the accepted Python renderer.

   Ported from sigil/museria_v6.py (generator "museria-v6"), 2026-09-30, so the
   website draws the SAME sigils the Python renderer draws. A visitor typing
   their name gets the mark their identity would derive — same derivation, same
   silhouette, same field algorithm, same palette.

   Why a port and not images: the site must show that a sigil is DERIVED, not
   issued. Rendering it in the browser from the visitor's own input is the proof.

   The derivation:  sha256("museria-sigil-v1:" + muse_id + ":" + public_key)
   For the live demo the public key is the sha256 of the input, so anyone can
   reproduce a mark they see by pasting the same input.
   =========================================================================== */
(function (global) {
  "use strict";

  // Index order MUST match PAL_ORDER in museria_v6.py exactly. void is #000000.
  const PAL = ["#000000", "#1E181E", "#4A4250", "#685C6C", "#D6CABC", "#F6D69C",
               "#9ABAD6", "#E29EAC", "#A8CCA2", "#E8B06C", "#B6A0DC", "#92C8C4",
               "#3A2E3E", "#F0E8DC"];
  const NAME = ["void", "ink", "dim", "dim2", "line", "hot", "cool", "rose",
                "sage", "amber", "violet", "teal", "ink2", "pale"];
  const IDX = {}; NAME.forEach((n, i) => (IDX[n] = i));

  const TINTS = [4, 5, 6, 7, 8, 9, 10, 11];
  const FILLS = [2, 3];   // dim, dim2 — read from museria_v6.py, do not guess
  const TAU = Math.PI * 2;

  // Optimal contrast cycle over the tints, found by exhaustive search over all
  // 8! orderings to maximise the worst adjacent RGB distance. The greedy version
  // made it WORSE (24.2) because it maximised the step from the previous tint
  // and ignored the closing edge; this holds every adjacent pair at 68.5 or more.
  const CONTRAST_ORDER = [0, 5, 2, 1, 6, 4, 3, 7];

  // The measured pear silhouette. Fixed by operator ruling: the body layer may
  // not vary, so the abstract field still carries the mascot's shape.
  const PROFILE = [
    [0, 13], [2, 29], [5, 44], [8, 52], [10, 55], [13, 61], [16, 64],
    [20, 67], [25, 69], [30, 70], [33, 70], [36, 69], [40, 68], [42, 69],
    [46, 75], [50, 80], [54, 86], [58, 91], [62, 95], [66, 98], [70, 100],
    [74, 98], [77, 84], [80, 81], [83, 72], [84, 61], [88, 55], [92, 53],
    [96, 53], [98, 45], [99, 11],
  ];
  const LEG_START = 84.0;

  function profileWidth(rowPct) {
    const r = Math.max(0, Math.min(100, rowPct));
    for (let i = 0; i < PROFILE.length - 1; i++) {
      const [r0, w0] = PROFILE[i], [r1, w1] = PROFILE[i + 1];
      if (r0 <= r && r <= r1) {
        if (r1 === r0) return w1 / 100;
        return (w0 + (w1 - w0) * ((r - r0) / (r1 - r0))) / 100;
      }
    }
    return PROFILE[PROFILE.length - 1][1] / 100;
  }

  /* ---- sha256, so the browser derives rather than fakes ------------------
     Web Crypto's subtle.digest. The first version of this file carried a
     hand-rolled SHA-256 with hand-generated round constants; it was replaced
     because a hand-written hash is exactly the kind of thing that looks right
     and is silently wrong, and a wrong derivation means a visitor's sigil does
     not match the Python renderer's. This is async, so the public entry points
     below are async and awaited by the page. */
  async function sha256Hex(str) {
    const data = new TextEncoder().encode(str);
    const buf = await crypto.subtle.digest("SHA-256", data);
    return Array.from(new Uint8Array(buf))
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");
  }

  /* ---- the derivation ---------------------------------------------------- */
  async function sigilKey(museId, publicKeyB64) {
    return sha256Hex("museria-sigil-v1:" + museId + ":" + publicKeyB64);
  }

  /* ---- field parameters (a direct port of field_for) --------------------- */
  async function fieldFor(key) {
    const seed = "museria-v6:" + key;
    // BUG FOUND BY THE PORT VERIFICATION, not by reading: the first version did
    //   atob(sha256Hex(seed))
    // which passes a PROMISE to atob. It only worked because nothing had tested
    // the browser path at all. Await first, then decode.
    const hexA = await sha256Hex(seed);
    const hexB = await sha256Hex("2:" + seed);
    const b = [];
    for (const h of [hexA, hexB])
      for (let i = 0; i < h.length; i += 2) b.push(parseInt(h.slice(i, i + 2), 16));
    const u = (i, lo, hi) => lo + (b[i] / 255) * (hi - lo);
    return {
      mode: b[0] % 4,
      p1: 3 + (b[1] % 5), p2: 3 + (b[2] % 6),
      off: u(3, 3, 14), ang: u(4, 0, TAU),
      k1: 1 + (b[5] % 5), k2: 1 + (b[6] % 4),
      amp: u(7, 0.15, 1.15),
      nray: 5 + (b[8] % 26),
      phase: u(9, 0, TAU),
      duty: u(10, 0.34, 0.52),
      tint: b[11] % 8,
      mc_n: 1 + (b[16] % 4),
      mc_rule: b[17] % 3,
      cy: u(12, 0.40, 0.62),
      bias: u(13, -0.18, 0.18),
      ground: b[14] % 2,
      back: b[15] % 3,
    };
  }

  /* ---- the mask ---------------------------------------------------------- */
  function bodyMask(n) {
    const mask = [];
    for (let y = 0; y < n; y++) mask.push(new Uint8Array(n));
    const top = 1.0, span = ((100 - 2 - 4) / 100) * n;
    const maxHw = n / 2 - 2, cx = n / 2;
    for (let y = 0; y < n; y++) {
      const rp = span ? (100 * (y - top)) / span : -1;
      if (y < top || rp > 100) continue;
      const hw = maxHw * profileWidth(rp);
      if (hw <= 0.5) continue;
      const x0 = Math.max(0, Math.floor(cx - hw)), x1 = Math.min(n, Math.floor(cx + hw) + 1);
      const leg = rp >= LEG_START;
      for (let x = x0; x < x1; x++) {
        if (leg && Math.abs(x - cx) <= Math.max(1, hw * 0.22)) continue;
        mask[y][x] = 1;
      }
    }
    return { mask, top, span, maxHw, cx };
  }

  /* ---- the render -------------------------------------------------------- */
  async function drawDataURL(key, size) {
    size = size || 32;
    const p = await fieldFor(key);
    const n = size, s = n / 32;
    const voidI = IDX.void, ink = IDX.ink;
    const mc = [];
    for (let i = 0; i < p.mc_n; i++) mc.push(TINTS[(p.tint + CONTRAST_ORDER[i]) % TINTS.length]);
    const line = mc[0];

    const grid = [];
    for (let y = 0; y < n; y++) grid.push(new Array(n).fill(voidI));

    if (p.back !== 0) {
      const back = [voidI, IDX.ink2, IDX.dim2][p.back];
      for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) grid[y][x] = back;
    }

    const { mask, top, span, maxHw, cx } = bodyMask(n);
    const fill = FILLS[p.ground % FILLS.length];
    for (let y = 0; y < n; y++)
      for (let x = 0; x < n; x++) if (mask[y][x]) grid[y][x] = fill;

    const ox = p.off * Math.cos(p.ang) * s;
    const oy = p.off * Math.sin(p.ang) * s * 0.7;
    const c1 = [cx + p.bias * maxHw, top + span * p.cy];
    const c2 = [c1[0] + ox, c1[1] + oy];
    const p1 = Math.max(1, p.p1 * s), p2 = Math.max(1, p.p2 * s);
    const { duty, nray } = p;

    const pick = (r1, ang) => {
      if (p.mc_n === 1) return line;
      if (p.mc_rule === 0) return mc[Math.floor(r1 / p1) % p.mc_n];
      if (p.mc_rule === 1) return mc[Math.floor(((ang + TAU) / TAU) * 6) % p.mc_n];
      return mc[Math.floor(r1 / (p1 * 2)) % p.mc_n];
    };

    const isTint = (c) => TINTS.indexOf(c) !== -1;

    // The MAIN field pass. sweep here is computed from r (the average radius),
    // matching the first loop in museria_v6.py's draw().
    const computeMain = (x, y) => {
      const dx1 = x - c1[0], dy1 = y - c1[1], dx2 = x - c2[0], dy2 = y - c2[1];
      const r1 = Math.hypot(dx1, dy1), r2 = Math.hypot(dx2, dy2);
      const r = 0.5 * (r1 + r2);
      const ang = Math.atan2(dy1, dx1);
      const sweep = ang + p.amp * Math.sin(p.k1 * 0.16 * r) +
                    0.45 * Math.sin(p.k2 * 0.07 * r + p.phase);
      let v;
      if (p.mode === 0) v = (Math.floor(r1 / p1) + Math.floor(r2 / p2)) % 2;
      else if (p.mode === 1) {
        const uu = (sweep / TAU) * nray;
        v = Math.floor(uu) % 2;
        if ((uu - Math.floor(uu)) > duty * 1.6) v = 0;
      } else if (p.mode === 2) {
        const uu = (sweep / TAU) * nray;
        v = (Math.floor(r / p1) + Math.floor(uu)) % 2;
        if ((uu - Math.floor(uu)) > duty * 1.6) v = 0;
      } else {
        v = Math.floor(r1 / p1) % 2;
        if (Math.floor((sweep / TAU) * nray) % 2) v = 1 - v;
      }
      // Both of these live INSIDE `if (v)` in the Python. Hoisting the crest
      // guarantee out lights pixels the mode had already switched off.
      const frac = r1 / p1 - Math.floor(r1 / p1);
      let out = 0;
      if (v) {
        let w = v;
        if (frac > duty) w = 0;
        if (frac < 0.16) w = 1;
        out = w ? 1 : 0;
      }
      return out;
    };

    // The DENSITY-BOOST pass. This is NOT the same maths as the main pass:
    // sweep is computed from r1; the mode-2 index uses r, the average.
    // Python keeps them separate for exactly this reason; collapsing them into
    // one helper produced a field that disagreed with the renderer.
    const computeBoost = (x, y, thick) => {
      const dx1 = x - c1[0], dy1 = y - c1[1], dx2 = x - c2[0], dy2 = y - c2[1];
      const r1 = Math.hypot(dx1, dy1), r2 = Math.hypot(dx2, dy2);
      const r = 0.5 * (r1 + r2);
      const ang = Math.atan2(dy1, dx1);
      const sweep = ang + p.amp * Math.sin(p.k1 * 0.16 * r1) +
                    0.45 * Math.sin(p.k2 * 0.07 * r1 + p.phase);
      let v;
      if (p.mode === 0) v = (Math.floor(r1 / p1) + Math.floor(r2 / p2)) % 2;
      else if (p.mode === 1) {
        const uu = (sweep / TAU) * nray;
        v = Math.floor(uu) % 2;
      } else if (p.mode === 2) {
        const uu = (sweep / TAU) * nray;
        // r, the AVERAGE - matching Python's boost pass. An earlier version used
        // r1 here, which is what made the three mode-2 sigils disagree.
        v = (Math.floor(r / p1) + Math.floor(uu)) % 2;
      } else {
        v = Math.floor(r1 / p1) % 2;
        if (Math.floor((sweep / TAU) * nray) % 2) v = 1 - v;
      }
      const frac = r1 / p1 - Math.floor(r1 / p1);
      if (frac < thick) v = 1;
      return v ? 1 : 0;
    };

    for (let y = 0; y < n; y++) {
      for (let x = 0; x < n; x++) {
        if (!mask[y][x]) continue;
        const dx1 = x - c1[0], dy1 = y - c1[1];
        const r1 = Math.hypot(dx1, dy1), ang = Math.atan2(dy1, dx1);
        if (computeMain(x, y)) grid[y][x] = (x + y) % 11 ? pick(r1, ang) : ink;
      }
    }

    // Guarantee a field: modes can zero every pixel for some parameter set, and
    // a sigil with no field is a failed sigil.
    const count = () => {
      let c = 0;
      for (let y = 0; y < n; y++)
        for (let x = 0; x < n; x++) if (mask[y][x] && isTint(grid[y][x])) c++;
      return c;
    };
    let hasField = false;
    for (let y = 0; y < n && !hasField; y++)
      for (let x = 0; x < n && !hasField; x++)
        if (mask[y][x] && grid[y][x] !== voidI && grid[y][x] !== fill && grid[y][x] !== ink)
          hasField = true;
    if (!hasField) {
      const fb = TINTS[(p.tint + 1) % TINTS.length];
      const q1 = Math.max(2, 3 * s);
      for (let y = 0; y < n; y++)
        for (let x = 0; x < n; x++) {
          if (!mask[y][x]) continue;
          const r1 = Math.hypot(x - c1[0], y - c1[1]);
          const ang = Math.atan2(y - c1[1], x - c1[0]);
          if (Math.floor(r1 / q1) % 2 === 0 || Math.floor((ang / TAU) * 12) % 2 === 0)
            grid[y][x] = fb;
        }
    }

    // Two-sided density control: too few lit pixels reads as noise, too many
    // closes the pattern into a solid mass. Operator ruling: fix automatically.
    let bodyTotal = 0;
    for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) if (mask[y][x]) bodyTotal++;
    const MIN_FIELD = Math.max(24, Math.floor(0.11 * bodyTotal));
    const MAX_FIELD = Math.floor(0.62 * bodyTotal);

    const body = [];
    for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) if (mask[y][x]) body.push([x, y]);

    if (count() < MIN_FIELD || count() > MAX_FIELD) {
      if (count() > MAX_FIELD) {
        for (const [x, y] of body) {
          const r1 = Math.hypot(x - c1[0], y - c1[1]);
          const frac = r1 / p1 - Math.floor(r1 / p1);
          if (isTint(grid[y][x]) && frac > 0.5 * duty) grid[y][x] = fill;
        }
      }
      for (let boost = 1; boost <= 6; boost++) {
        const thick = 0.16 + 0.1 * boost;
        for (const [x, y] of body) {
          const dx1 = x - c1[0], dy1 = y - c1[1];
          const r1 = Math.hypot(dx1, dy1), ang = Math.atan2(dy1, dx1);
          if (computeBoost(x, y, thick)) grid[y][x] = pick(r1, ang);
        }
        if (count() >= MIN_FIELD) break;
      }
    }

    // outline
    const ow = Math.max(1, Math.round(1 * s));
    let grown = mask.map((r) => r.slice());
    for (let it = 0; it < ow; it++) {
      const nxt = grown.map((r) => r.slice());
      for (let y = 0; y < n; y++)
        for (let x = 0; x < n; x++) {
          if (grown[y][x]) continue;
          for (let dx = -1; dx <= 1 && !nxt[y][x]; dx++)
            for (let dy = -1; dy <= 1 && !nxt[y][x]; dy++) {
              const nx = x + dx, ny = y + dy;
              if (nx >= 0 && ny >= 0 && nx < n && ny < n && grown[ny][nx]) { nxt[y][x] = 1; break; }
            }
        }
      grown = nxt;
    }
    for (let y = 0; y < n; y++)
      for (let x = 0; x < n; x++) if (grown[y][x] && !mask[y][x]) grid[y][x] = ink;

    // paint to a canvas at 1:1, then scale up with nearest-neighbour
    const cv = document.createElement("canvas");
    cv.width = n; cv.height = n;
    const ctx = cv.getContext("2d");
    const img = ctx.createImageData(n, n);
    for (let y = 0; y < n; y++)
      for (let x = 0; x < n; x++) {
        const hex = PAL[grid[y][x]];
        const o = (y * n + x) * 4;
        img.data[o] = parseInt(hex.slice(1, 3), 16);
        img.data[o + 1] = parseInt(hex.slice(3, 5), 16);
        img.data[o + 2] = parseInt(hex.slice(5, 7), 16);
        img.data[o + 3] = 255;
      }
    ctx.putImageData(img, 0, 0);
    return { url: cv.toDataURL(), n };
  }

  async function drawTo(canvas, key, size) {
    const { url, n } = await drawDataURL(key, size);
    const img = new Image();
    img.onload = () => {
      canvas.width = n; canvas.height = n;
      canvas.getContext("2d").imageSmoothingEnabled = false;
      canvas.getContext("2d").drawImage(img, 0, 0);
    };
    img.src = url;
  }

  global.MuseriaSigil = { sigilKey, fieldFor, drawDataURL, drawTo, sha256Hex,
                          PAL, NAME, IDX, profileWidth };
})(window);
