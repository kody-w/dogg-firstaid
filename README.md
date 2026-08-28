# dogg-firstaid — a federated node of the global tick network

**First aid as a book: a versioned lay-rescuer decision tree for severe bleeding, CPR, choking, shock, burns, and hypothermia — one verifiable frame per publication, anchored to the global tick.**

This repo keeps its own append-only chain of rapp/1 frames in `firstaid/`. Once a day
a GitHub Action reads the current tick anchor from the spine at
[kody-w/dogg](https://github.com/kody-w/dogg) and appends one frame attesting "this is
the first-aid book's current text, as of this tick" — so this chain joins every other
node's data on the same clock. Unlike a live-data node, nothing here is fetched from a
sensor or a market: the payload is a small, hand-maintained decision tree, paraphrased
from widely published Red Cross / American Heart Association (AHA) lay-rescuer
guidance, with a version number that only advances when the text itself changes.

**⚠️ Not medical advice.** Every frame carries an explicit `disclaimer` field. This is
educational, general lay-rescuer information — it is not a substitute for certified
first aid / CPR training, and it is not a substitute for calling your local emergency
number. In any real emergency, call your local emergency number immediately and follow
instructions from trained responders and your own certified training.

## Why this exists

Most first-aid text lives on websites that can change silently, go down, or vanish.
This node makes the six most time-critical lay-rescuer procedures into a small,
append-only, content-addressed chain: every past revision stays readable and every
frame's hash is independently checkable, so an offline copy (a phone with no signal, a
downloaded repo, a printed HEAD.json + frame) is provably the same text someone else
is looking at — useful for an heirloom binder, a go-bag, or an agent that needs a
citable, tamper-evident source for "what do I do right now" instead of a possibly-
hallucinated answer.

## What's in a frame

- `tree_version` / `branches` / `cpr_rate_per_min` / `compression_depth_mm` — the
  book's numeric spine (rapp/1 canonical JSON forbids floats, so these ride as ints).
- `tree` — six branches (`severe_bleeding`, `cpr`, `choking`, `shock`, `burns`,
  `hypothermia`), each an ordered list of short steps.
- `disclaimer` — the not-medical-advice notice, on every frame, verbatim.
- `tick` / `tick_frame` / `spine` — this frame's anchor into the global tick network.

## Precision and limits

- **Coverage is deliberately narrow**: six common, high-stakes lay-rescuer scenarios,
  not a full first-aid manual. It omits pediatric/infant variants, allergic reaction
  (EpiPen), poisoning, seizures, and dozens of other real scenarios.
- **Numbers are the commonly published lay-rescuer midpoints** (e.g. 100–120
  compressions/min → published here as 110; ~2 in / 5 cm depth → published here as 50
  mm), not a substitute for a certified course, which will teach the full range and
  the judgment calls a single number can't carry.
- **No first-hand verification**: this is paraphrased from public, widely republished
  guidance, not reviewed by a medical professional as part of this pipeline. Treat it
  as a starting point, not a clinical source.
- **Cadence is daily**, not per-tick like a live-data node — the book changes by
  editorial revision (bump `TREE_VERSION` in `tools/collect.py`), so unlike a
  volatile-data node this collector does not skip a run just because the spine tick
  hasn't advanced since the last frame; every run is a deliberate attestation.

**Verify it yourself:** `python3 tools/verify_thread.py` re-checks every frame with the
reference implementation from [kody-w/rapp-1](https://github.com/kody-w/rapp-1). CI runs
the same oracle on every push.

**Start your own node:** fork this repo, edit `THEME` / `STREAM` / the tree content at
the top of `tools/collect.py`, and enable the scheduled workflow. Your chain, your
outlook, same clock — announce it on the spine's registry
([kody-w/dogg](https://github.com/kody-w/dogg) issues) so agents can find it.

## Trust

<!--trust-->
No ratings yet — used this chain? [Rate it](../../issues/new?template=rate.yml): valid ratings publish automatically as verifiable frames.
<!--/trust-->

## Summon this node

A MISSION chant — 14 words — carries the `firstaid:@kody-w/dogg-firstaid` dimension's identity, its tick, a hash prefix that pins the exact frame, and a quantized snapshot of tree_version, branches, cpr_rate_per_min.

```
KNELL CAST FRISK FORGE FORGE PLEDGE ICECAP ANVIL ELIXIR SCROLL NEXUS ELM THUNDER DUB
```

`dogg:1:14:BIALoYAAAfm6wB0klSoYgQGY`

Tap to decode: [https://kody-w.github.io/dogg/recite.html#dogg:1:14:BIALoYAAAfm6wB0klSoYgQGY](https://kody-w.github.io/dogg/recite.html#dogg:1:14:BIALoYAAAfm6wB0klSoYgQGY)

This chant carries three things: which dimension it names (`firstaid:@kody-w/dogg-firstaid`), which tick and frame it was cut from (tick 1, hash prefix `3e6eb`), and the field values above, quantized (log-quantized, ~0.3% relative (1e-6 … 1e15)) — enough to recognize the node and sanity-check a claim about it without touching the network.

This is a snapshot of one tick (tick 1) — the numbers move as the stream advances, so re-mint with `python3 tools/dogg.py mission firstaid:@kody-w/dogg-firstaid` for the latest.
