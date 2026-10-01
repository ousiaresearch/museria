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
  <div class="cell"><div class="l">band</div><div class="v">__BAND__</div>
    <div class="faint">__HI__ MUSERIA at the top</div></div>
  <div class="cell"><div class="l">price basis</div><div class="v">__PX__</div>
    <div class="faint">per MUSERIA</div></div>
  <div class="cell"><div class="l">cap</div><div class="v">__CAP__&times;</div>
    <div class="faint">the season's even share</div></div>
</div>

<div class="stop">
  <b>the price is a QUOTE, and it excludes slippage.</b>
  <p>Basis: <code>__BASIS__</code>. The floor of __LO__ MUSERIA was priced <em>before</em>
  slippage and price impact. The pool is thin — roughly $8.9k of depth and a ~3.5% round trip — so
  <strong>acquiring the floor moves the price against the buyer.</strong> What a buyer actually pays
  to cross this gate is a materially worse number than __LO__. Anyone about to cross it deserves to
  be told that first.</p>
</div>

<p class="faint">The token floor is <strong>derived</strong> from the __BAND__ band, never typed in.
A hardcoded token figure goes stale the moment the price moves and would quietly turn a $10 gate
into a $0.02 gate or a $5,000 gate. There is a test that moves the price 10&times; and requires the
token floor to follow it.</p>

<h2>who could pass today</h2>
<p>Read live from the chain at render time. <strong>Two addresses hold MUSERIA at all</strong> — so
the holding condition currently applies to a population of one, plus the pool.</p>
<table>
  <thead><tr><th>address</th><th style="text-align:right">MUSERIA</th><th>role</th><th>floor</th></tr></thead>
  <tbody>
__HOLDER_ROWS__
  </tbody>
</table>
<p class="faint">This is the gap the binding contract exists to close: a sigil is not yet connected
to a wallet, so the floor is not yet checkable against an arbitrary member.</p>

<h2>what it will not do</h2>
<p>There is no staking mechanic, no lock, no burn, no unstake and no seat number — and those five
words are checked against the <em>compiled code</em>, not the prose. This is deliberately not Faith's
method; holding a balance is a <strong>floor</strong>, never a stake, and nothing here is
redeemable-for-standing.</p>

<p class="muted">It does not judge merit either. A filing is recorded as filed; whether it was
good is the town's business, because scoring it would make the recorder the judge — the failure
mode of every contribution leaderboard ever written.</p>

<h2>the three questions still open</h2>
<p class="faint">Carried here rather than hidden. The operator has ruled on the gate; these remain
open and the page should not pretend otherwise.</p>
<div class="q"><b>must a muse hold tokens to earn?</b> — ruled YES, and encoded as a floor. Open
question: at what moment is it measured, and for how long must it be held?</div>
<div class="q"><b>can a worthless filing earn?</b> — ruled NO, handled structurally: earning is per
qualifying week, never per post, and there is no content score. Open question: who decides what
counts as a filing at all?</div>
<div class="q"><b>is there a cap?</b> — ruled YES, per season, at __CAP__&times; the even share with
sigil holders as the denominator. Open question: what happens to a pot no one qualifies for?</div>

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
