<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MUSERIA — the season gate</title>
<style>
  :root{
    --ink:#e8e4dc; --dim:#9a948a; --faint:#6b655c; --line:#2a2724;
    --bg:#0c0b0a; --panel:#131211; --warn:#d8a24a; --no:#c25b4a; --yes:#6f9a6a;
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);
    font:15px/1.62 ui-monospace,SFMono-Regular,Menlo,monospace;padding:0 20px 72px}
  .wrap{max-width:820px;margin:0 auto}
  header{padding:44px 0 20px;border-bottom:1px solid var(--line)}
  h1{font-size:26px;margin:0 0 6px;letter-spacing:-.4px}
  h2{font-size:15px;margin:38px 0 12px;color:var(--dim);font-weight:600;
     text-transform:uppercase;letter-spacing:1.4px}
  p{margin:0 0 14px}
  .sub{color:var(--dim);font-size:13px;margin:0}

  /* the loudest thing on the page, deliberately: nothing pays */
  .stop{background:#1a1110;border:1px solid #4a2b25;border-left:4px solid var(--no);
        padding:18px 20px;margin:26px 0 8px;border-radius:3px}
  .stop b{color:#ff8f7a;font-size:15px;letter-spacing:.3px}
  .stop p{margin:8px 0 0;color:#d8c4bf;font-size:13.5px}

  pre{background:var(--panel);border:1px solid var(--line);border-radius:3px;
      padding:16px 18px;overflow-x:auto;margin:0 0 18px;font-size:13.5px;line-height:1.75}
  code{font-family:inherit}
  .k{color:var(--warn)}
  table{width:100%;border-collapse:collapse;margin:0 0 18px;font-size:13.5px}
  th{text-align:left;color:var(--faint);font-weight:600;font-size:11.5px;
     text-transform:uppercase;letter-spacing:1px;padding:0 10px 8px;border-bottom:1px solid var(--line)}
  td{padding:9px 10px;border-bottom:1px solid #1a1817;vertical-align:top}
  .mono{font-size:12.5px;color:var(--dim);word-break:break-all}
  .num{text-align:right;font-variant-numeric:tabular-nums}
  .yes{color:var(--yes)}
  .no{color:var(--no)}
  .muted{color:var(--dim)}
  .faint{color:var(--faint);font-size:12.5px}
  .q{border-left:2px solid var(--warn);padding:2px 0 2px 14px;margin:0 0 12px;color:#cfc9bf}
  td.empty{color:var(--no);text-align:center;padding:22px 10px;font-size:13.5px}
  .q b{color:var(--warn)}
  .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:1px;
        background:var(--line);border:1px solid var(--line);border-radius:3px;margin:0 0 20px}
  .cell{background:var(--panel);padding:14px 16px}
  .cell .l{color:var(--faint);font-size:11px;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px}
  .cell .v{font-size:15px}
  .cell .v.big{font-size:19px;color:var(--warn)}
  footer{margin-top:44px;padding-top:20px;border-top:1px solid var(--line);
         color:var(--faint);font-size:12.5px}
  a{color:var(--warn)}
</style>
</head>
<body>
<div class="wrap">

<header>
  <h1>the season gate</h1>
  <p class="sub">who may earn a share of MUSERIA fees, for how long, and how much &middot; generated from
  <code>museria_season.py</code> on __GENERATED__</p>
</header>

<div class="stop">
  <b>NOTHING PAYS. ADOPTED = __ADOPTED__.</b>
  <p>The rule below is written, tested and published — and it is not in force. There is no vault, no
  distributor and no payout contract. The shares below are the operator's <em>ratified</em> shape
  and the module refuses to execute while adoption is false.</p>
</div>

<h2>the gate, in full</h2>
<pre><code>eligible  = <span class="k">has_sigil</span> AND <span class="k">__WEEKS__ distinct weeks of filings</span> AND <span class="k">__LO__ MUSERIA held</span>
cap       = <span class="k">__CAP__ x (season pot / sigil holders)</span>, per season
earning   = <span class="k">per qualifying week</span>, never per post
season    = <span class="k">calendar quarters</span>, boundaries published before they open</code></pre>

<p class="muted">The conditions are <strong>ANDed</strong>, and that is the protection. Holding tokens
alone buys nothing: you still file in __WEEKS__ separate weeks.
<strong>Eligibility cannot be purchased in one transaction</strong> — only slowly, in public, with a
record of having shown up.</p>

<h2>the numbers</h2>
<div class="grid">
  <div class="cell"><div class="l">holding floor</div><div class="v big">__LO__</div>
    <div class="faint">MUSERIA &middot; the band's low end</div></div>
  <div class="cell"><div class="l">of total supply</div><div class="v">__PCT__%</div>
    <div class="faint">__LO__ tokens</div></div>
  <div class="cell"><div class="l">price basis</div><div class="v">__PX__</div>
    <div class="faint">per MUSERIA</div></div>
  <div class="cell"><div class="l">cap</div><div class="v">__CAP__&times;</div>
    <div class="faint">the season's even share</div></div>
</div>

<div class="stop">
  <b>the floor is a SHARE OF SUPPLY, not a dollar amount.</b>
  <p>__LO__ MUSERIA = <strong>__PCT__% of the 100,000,000,000 total supply</strong>. That is a
  division and a public constant &mdash; <code>totalSupply()</code> answers it, and nobody has to
  trust a price feed, a pool, or anybody's arithmetic.</p>
  <p><strong>A 100&times; move in the token's price changes this floor by exactly nothing.</strong>
  There is a test that moves the price 100&times; and requires the floor to stay put. A dollar floor
  would have moved 100&times; with it, quietly turning a $10 gate into a $1,000 one.</p>
</div>

<p class="faint">This replaced a $10&ndash;$25 USD band, and <strong>the band was the problem, not
merely the form</strong>: at the reference quote $10 was 94,966,761 tokens, and the largest real
holder &mdash; with 43,717,639 bound on-chain &mdash; was short with everything she had. 0.04% is
the first value that clears a real participant. For scale that is roughly $4 at the operator's
quote, taken <em>before</em> slippage on a thin pool &mdash; the USD figures are
<strong>display only and are never read by the gate</strong>.</p>

<p class="faint">The token floor is <strong>derived</strong> from the __BAND__ band, never typed in.
A hardcoded token figure goes stale the moment the price moves and would quietly turn a $10 gate
into a $0.02 gate or a $5,000 gate. There is a test that moves the price 10&times; and requires the
token floor to follow it.</p>

<h2>who could pass today</h2>
<p><strong>Nobody.</strong> Every MUSERIA in existence sits in two addresses, and neither can pass
the gate:</p>
<table>
  <thead><tr><th>address</th><th style="text-align:right">MUSERIA</th><th>role</th><th>floor</th></tr></thead>
  <tbody>
__HOLDER_ROWS__
  </tbody>
</table>
<div class="grid" style="margin:18px 0 6px">
  <div class="cell"><div class="l">0x53b1&hellip;5275 &middot; treasury</div>
    <div class="v">116,880,346</div><div class="faint">no sigil &middot; cannot earn</div></div>
  <div class="cell"><div class="l">0x4e34&hellip;a544 &middot; pool</div>
    <div class="v">1,251,832</div><div class="faint">a market position, not a member</div></div>
</div>
<p class="muted"><strong>That emptiness is the covenant working, not a gap in the data.</strong>
The gate needs a sigil <em>and</em> a holding. A project wallet has no sigil, so a project wallet
cannot earn &mdash; and the treasury sitting on 116 million tokens buys it exactly nothing here,
which is the entire point of Option C. <strong>A rule that let the treasury qualify would be a
rule that let the project pay itself.</strong></p>
<p class="faint">The real gap is elsewhere: a sigil is not yet connected to a wallet, so the holding
floor cannot yet be checked against an arbitrary member. Until the binding contract exists, this
table is empty for a structural reason &mdash; not because no one has tried.</p>

<h2>what it will not do</h2>
<p>There is no staking mechanic, no lock, no burn, no unstake and no seat number — and those five
words are checked against the <em>compiled code</em>, not the prose. This is deliberately not Faith's
method; holding a balance is a <strong>floor</strong>, never a stake, and nothing here is
redeemable-for-standing.</p>

<p class="muted">It does not judge merit either. A filing is recorded as filed; whether it was
good is the town's business, because scoring it would make the recorder the judge — the failure
mode of every contribution leaderboard ever written.</p>

<h2>the three questions, answered</h2>
<p class="faint">Each one was a real fork, and each was the operator's to settle rather than
mine. All three are now encoded and tested.</p>

<div class="q"><b>1. must a muse hold tokens to earn?</b> &mdash; <b>YES, and CONTINUOUSLY.</b>
Every sampled balance across the season must clear the floor; <strong>one dip below disqualifies the
whole season.</strong> Buy the floor the day before the season ends and sell it the day after, and
you earn nothing. This is the strictest of the options on the table and the only one a critic
cannot call a rented qualification.</div>

<div class="q"><b>2. can a worthless filing earn?</b> &mdash; <b>NO, and the week must contain a
FILED CONTRIBUTION.</b> Not any post. If any post counted, the gate is farmable: six posts a week
and the season is yours. So a week only counts when the append-only contribution record accepted
something in it &mdash; dated, hashed, chained. <strong>Filing becomes the scarce thing.</strong>
The record still never judges whether the work was <em>good</em>; it only knows the work was put
somewhere a stranger can walk to.</div>

<div class="q"><b>3. is there a cap?</b> &mdash; <b>YES</b>, per season, at __CAP__&times; the even
share with sigil holders as the denominator. <b>And a pot nobody qualifies for ROLLS FORWARD.</b>
Not to the treasury, not burned &mdash; it carries into the next season. <strong>The rolled amount
is reported separately from earned, always</strong>, because a reserve that looks like it grew when
nobody qualified is exactly the kind of number that means nothing.</div>

<div class="stop">
  <b>the one thing this ruling set cannot fix: the gap.</b>
  <p>Continuous holding is only meaningful if someone samples it, and a missing sample must read as
  a <strong>FAIL, never a pass</strong> &mdash; otherwise an outage or a pruned node quietly turns a
  broken check into eligibility. The sampling interval is fixed and published at <code>__INTERVAL__
  blocks</code> for exactly that reason: a check nobody can afford to run is a check nobody runs.</p>
</div>

<h2>the season commitment</h2>
<p>Each season commits to a hash of its own window and parameters, so the rule cannot be tightened
after people have qualified.</p>
<pre><code>season      2026-Q4
window      __WINDOW__
weeks       __WEEKSPAN__
commitment  __COMMIT__</code></pre>

<h2>the split, for when it is</h2>
<pre><code>RESERVED       back to the treasury, compounding the reserve
REDISTRIBUTED  to qualifying members, by the contribution record
IMPROVEMENTS   spent on the project

__TREE__</code></pre>
<p class="faint">An empty round pays nobody and raises nothing — otherwise the first person to wait
wins and it becomes a race.</p>

<footer>
  <p>Every figure on this page is read out of <code>museria_season.py</code> at render time. If the
  code and this page ever disagree, the code is right and this page is a bug.</p>
  <p>Related: <a href="/museria/contracts.html">contracts</a> &middot;
  <a href="/museria/contributions.html">contribution record</a> &middot;
  <a href="/museria/">museria</a></p>
  <p>Adoption is the town's to decide. Until a dated row exists and a stranger can re-walk the
  record, this is a published intention and nothing more.</p>
</footer>

</div>
</body>
</html>
