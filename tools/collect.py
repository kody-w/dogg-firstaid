#!/usr/bin/env python3
"""A federated tick-network node: this repo's own append-only chain, keyed to the
global tick spine at kody-w/dogg.

Unlike a live-data node (e.g. dogg-markets, which snapshots keyless public APIs), this
node's content is a BOOK, not a feed: a versioned lay-rescuer first-aid decision tree
(severe bleeding, CPR, choking, shock, burns, hypothermia), paraphrased from widely
published Red Cross / AHA lay-rescuer guidance. Every run reads the spine's current
tick anchor and appends one frame that attests "this is the book, as of this tick" —
so the book joins the same clock as every other node's data, and its revision history
becomes a verifiable, append-only chain. Frames verify with the reference
implementation (tools/rapp.py, from kody-w/rapp-1); CI re-verifies the whole chain on
every push.

Cadence note: the scheduled workflow runs DAILY (this content changes by editorial
revision, not by the minute), so — unlike a live-data node — this node does NOT skip a
run when the spine tick hasn't advanced since the last frame: every run is a fresh,
deliberate attestation of the book's current text under the current tick, and the
daily cron is what keeps the chain from growing unbounded. Running collect.py twice in
quick succession (e.g. while testing) intentionally produces two frames, even if the
spine tick is identical in both, because a document need not carry a fetch failure
mode the way an unreliable live API does.
"""
import json, sys, pathlib, datetime, urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import rapp as R
import chainio

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPINE_HEAD = "https://raw.githubusercontent.com/kody-w/dogg/main/ticks/HEAD.json"
TIMEOUT = 8

# ---- edit these three for your node -------------------------------------------------
THEME = "firstaid"                    # also the data directory name
STREAM = "firstaid:@kody-w/dogg-firstaid"   # your stream id (your repo, your name)
# TREE_VERSION: bump this (and describe the change) whenever the book's text changes.
# -------------------------------------------------------------------------------------

TREE_VERSION = 1

DISCLAIMER = (
    "This is educational lay-rescuer guidance, paraphrased from widely published "
    "Red Cross / American Heart Association (AHA) lay-rescuer materials. It is NOT "
    "medical advice, it does NOT replace certified first aid / CPR training, and it "
    "does NOT replace calling your local emergency number. In any real emergency, "
    "call your local emergency number immediately and follow instructions from "
    "trained responders and your own certified training."
)

# The book. Six branches, each a short ordered step list a lay rescuer can follow.
# Sourced from lay-rescuer guidance that is widely published by Red Cross / AHA
# affiliates worldwide (not verbatim from any single copyrighted publication).
TREE = {
    "severe_bleeding": {
        "title": "Severe bleeding",
        "steps": [
            "Call your local emergency number, or have someone else call, right away.",
            "Apply firm, direct pressure to the wound with a clean cloth or dressing; do not remove a soaked dressing, add more on top.",
            "If bleeding does not stop and the wound is on a limb, apply a tourniquet 2 to 3 inches above the wound, never directly on a joint.",
            "Note and write down the time the tourniquet was applied; tell responders that time as soon as they arrive.",
            "Once applied, leave the tourniquet in place until trained help arrives — do not loosen or remove it yourself.",
            "Keep the person still, keep them warm, and watch for signs of shock.",
        ],
    },
    "cpr": {
        "title": "CPR (adult, lay rescuer)",
        "steps": [
            "Check responsiveness and normal breathing; call your local emergency number (or send someone to call) and ask for an AED if one is nearby.",
            "Lay the person on their back on a firm, flat surface.",
            "Push hard and fast in the center of the chest: 30 compressions at a rate of 100 to 120 per minute, at a depth of about 2 inches (5 cm), letting the chest fully recoil between compressions.",
            "If trained and willing, give 2 rescue breaths after every 30 compressions (a 30:2 ratio).",
            "If untrained, or unable/unwilling to give breaths, continue hands-only compressions without stopping until help arrives or the person starts breathing normally.",
            "As soon as an AED is available, turn it on and follow its voice prompts.",
        ],
    },
    "choking": {
        "title": "Choking (adult, conscious)",
        "steps": [
            "Ask 'Are you choking?' If they can cough forcefully, speak, or breathe, encourage them to keep coughing.",
            "If they cannot cough, speak, or breathe (or are making a high-pitched sound), stand behind them and give 5 firm back blows between the shoulder blades with the heel of your hand.",
            "Follow with 5 abdominal thrusts (Heimlich maneuver): fist above the navel, grasp with your other hand, pull sharply inward and upward.",
            "Alternate 5 back blows and 5 abdominal thrusts until the object is coughed up or the person becomes unresponsive.",
            "If the person becomes unresponsive, lower them to the ground, call your local emergency number, and begin CPR — check the mouth for a visible object before each set of breaths.",
        ],
    },
    "shock": {
        "title": "Shock",
        "steps": [
            "Call your local emergency number.",
            "Watch for pale, cool, clammy skin, rapid weak pulse, rapid breathing, confusion, or fainting.",
            "Lay the person down and, only if no spinal injury or leg fracture is suspected, raise the legs about 12 inches.",
            "Keep the person warm with a blanket or coat, and loosen tight clothing.",
            "Do not give food or water, even if they ask.",
            "Keep monitoring breathing and responsiveness until help arrives; begin CPR if breathing stops.",
        ],
    },
    "burns": {
        "title": "Burns",
        "steps": [
            "Remove the person from the heat, flame, chemical, or electrical source; make sure the scene is safe before you approach.",
            "Cool the burn under cool (not ice-cold) running water for at least 10 minutes.",
            "Gently remove rings, watches, or tight clothing near the burn before swelling starts, unless stuck to the skin.",
            "Cover loosely with a clean, non-stick dressing or cloth.",
            "Do not apply ice, butter, oil, or ointments, and do not break blisters.",
            "Seek emergency care for burns that are large, deep, on the face/hands/genitals/airway, or from chemicals or electricity.",
        ],
    },
    "hypothermia": {
        "title": "Hypothermia",
        "steps": [
            "Call your local emergency number for anyone with severe shivering, confusion, slurred speech, or drowsiness.",
            "Move the person to a warm, dry place and out of the wind.",
            "Remove wet clothing and cover with dry blankets, focusing on the head, neck, chest, and groin.",
            "If alert and able to swallow, give warm (not hot) sweet, non-alcoholic drinks.",
            "Do not rub or massage the arms or legs, and do not apply direct heat (hot water, heating pads, or a fire) directly to the skin.",
            "Handle the person gently — rough movement or jarring can trigger a dangerous heart rhythm in severe hypothermia.",
        ],
    },
}


def utc():
    n = datetime.datetime.now(datetime.timezone.utc)
    return n.strftime("%Y-%m-%dT%H:%M:%S.") + f"{n.microsecond // 1000:03d}Z"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": f"tick-node-{THEME}"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode())


def load_chain(d):
    return chainio.load_chain(d)


def main():
    spine = get(SPINE_HEAD)
    tick_n, tick_hash = spine["count"] - 1, spine["head_frame"]
    d = ROOT / THEME
    d.mkdir(exist_ok=True)
    chain = load_chain(d)
    head = chain[-1] if chain else None

    book = {
        "disclaimer": DISCLAIMER,
        "tree_version": TREE_VERSION,
        "branches": len(TREE),
        "cpr_rate_per_min": 110,
        "compression_depth_mm": 50,
        "tree": TREE,
    }
    payload = {"tick": tick_n, "tick_frame": tick_hash, "spine": "kody-w/dogg",
               "fetched_utc": utc(), THEME: book, "sources_failed": []}
    if head is None:
        payload["about"] = (
            f"A federated node of the global tick network: this repo's own "
            f"{THEME} book, one frame per publication, keyed to the spine's tick "
            "anchors so it joins every other node's data on the same clock. This "
            "node's content is a versioned first-aid decision tree, not a live feed."
        )
    f = R.build_frame(f"{THEME}.snapshot", STREAM, (head["seq"] + 1) if head else 0,
                      utc(), payload, prev=(head["payload_hash"] if head else None))
    ok, step, why = R.verify_frame(f, head=head, stream_id_of_record=STREAM)
    if not ok:
        raise ValueError(f"refusing invalid frame: {step}: {why}")
    chainio.append_frame(d, f, STREAM)
    print(f"{THEME} frame {f['seq']} @ spine tick {tick_n}: "
          f"tree_version={TREE_VERSION}, branches={len(TREE)}")


if __name__ == "__main__":
    main()
