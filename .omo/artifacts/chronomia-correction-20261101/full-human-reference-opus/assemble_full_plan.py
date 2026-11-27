#!/usr/bin/env python3
"""Assemble the Opus 5.5 full-song Chronomia plan outside the human reference window.

All creative decisions live in DESIGN: phrase by phrase, Claude Opus 5.5 chose
which selectable full-mix-v2 events to chart, their lanes, chords and holds,
after reading the measured evidence for that phrase. This script performs no
musical inference. It maps each authored (bar, sixteenth) token to the
selectable event at that exact editor grid tick, attaches provenance labels,
validates in memory, smoke-compiles in memory (no chart is written) and writes
full.plan.json once. If full.plan.json exists it only verifies byte equality.

Token grammar per bar: "<sixteenth>:<lane>[h<ticks>][+<lane>[h<ticks>]]..."
e.g. "4:0+2h6" = lanes 0 and 2 at sixteenth 4, lane 2 held for 6 sixteenths.
The hold end must be another selectable event; ticks only locate that event.

Run from anywhere:  python3 -I assemble_full_plan.py
"""
from __future__ import annotations

import collections
import copy
import hashlib
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
ANALYSIS = REPO / "Tools/ai-chart/output/chronomia-20261101/fullpack/full-mix-v2.analysis.json"
TEMPLATE = REPO / "Songs/Chronomia/Chronomia_Normal.4k-speedcoef.json"
HUMAN = REPO / "Songs/Chronomia/Chronomia_AI_Upper_Rhythm_Holds_25-45_Refined.4k-speedcoef.json"
OUTPUT = HERE / "full.plan.json"
ANALYSIS_ID = "8a57032b3a6f7755f84e"
TEMPLATE_SHA256 = "c323becd97f68d97b529633248e31e587be3ff7e2a7308e6730bccc0e051514f"
WINDOW_MS = (25000, 45000)  # human reference geometry, spliced by the parent; half-open
TICK_MS = 60000 / 227 / 4
SOURCE_LABEL = {"upper": "upper-stem estimate", "drums": "drums", "bass": "bass"}


def P(pid, section, motif, focus, bars):
    return {"id": pid, "section": section, "motif": motif, "focus": focus, "bars": bars}


# Bars are 0-based editor bars of 16 sixteenths.
DESIGN = [
    P('P01', 'intro',
      'entrance chord then quarter pulse; dotted s6 accent',
      'beat-position co-attacks; strongest local upper onset at s6',
      {3: '0:1+2 4:0 6:3',
       4: '0:0+2 4:1 6:3 8:0 12:2 14:1',
       5: '0:3 4:0 12:2',
       6: '0:1 4:2 8:0 12:3'}),
    P('P02', 'intro',
      'second statement of the bar-4 accent rhythm, mirrored hands',
      'repeat of measured s0/s6/s12/s14 upper accents',
      {7: '0:2 4:1 12:3 14:0',
       8: '0:1+3 4:0 6:2 8:1 12:3 14:0',
       9: '0:2 4:1 8:3 12:0',
       10: '0:1 4:2 8:0 12:3 14:1'}),
    P('P03', 'build',
      'eighth flow begins; held opening accent; 0-6-12 chord figure; rising stair into paired jumps',
      'bar-11 strongest accent; recurring s0/s6/s12 mix accents; measured s8-s11 sixteenth run',
      {11: '0:0h4+3 4:2 6:1 8:3 10:0 12:2 14:1',
       12: '0:1+2 2:0 4:3 6:1 8:2 10:0 12:3 14:1',
       13: '0:1+2 2:0 4:3 6:1+2 10:3 12:0+2 14:1',
       14: '0:2 2:0+3 4:1 6:2 8:0 9:1 10:2 11:3 12:0+2 14:1+3'}),
    P('P04', 'build',
      'all-source eighth drive with sparse accent chords; descending pickup stair',
      'eighth co-attacks; bass+drums accent at bar-17 s8; measured bar-18 s12-s15 pickup',
      {15: '0:0 2:3 4:1 6:0+2 8:3 10:1 12:2 14:0',
       16: '0:1+3 2:0 6:2 8:1 10:3 12:0 14:2',
       17: '0:1 2:3 4:0 6:2 8:1+3 10:0 12:2 14:0+3',
       18: '0:1 2:2 4:0 6:3 8:1 10:2 12:3 13:2 14:1 15:0'}),
    P('P05', 'break',
      'stop-time accents; right-hand hold over bass taps',
      'syncopated mix accents; upper sustain with no upper re-attack t310-t322',
      {19: '0:1+3 4:2 6:0+3h12 8:1',
       20: '0:0 2:1+2 6:3 8:0+2 10:1 14:3'}),
    P('P06', 'groove',
      'beat/offbeat interlock: left hand bass-beat support, right hand upper offbeats',
      'bass on beats, upper(+bass) on offbeats',
      {21: '0:0+2 2:3 4:1 6:2 8:0 10:3 12:1 14:2',
       22: '0:0 2:2 4:1 6:3 8:0 10:2 12:1 14:3',
       23: '0:0 2:3 4:1 6:2 8:0 10:3'}),
    # Bars 23.12-42.8, i.e. [25000, 45000) ms, are the human reference spliced by the parent.
    P('P07', 'post-reference stabs',
      'accent stabs with 0-6-12 hit chords; coiled sixteenth turns into the bar-45/47 downbeats',
      'E-level syncopated mix accents; measured continuous upper sixteenths in bars 44 and 46',
      {42: '10:0+3 12:2 14:0',
       43: '0:1+2 2:0 4:2 6:0+3 8:1 10:2 14:3',
       44: '0:1 2:0+3 4:2 6:1 8:3 10:2 12:0 13:1 14:2 15:1',
       45: '0:0+3 2:1 4:2 6:0+3 8:1 10:3 12:1+2 14:0',
       46: '0:3 2:1+2 4:0 6:2 8:0+3 10:1 12:3 13:2 14:1 15:2'}),
    P('P08', 'drive',
      'two-hand eighth drive, beat-3 accent chords; one upper sixteenth bounce at bar 50',
      'drums+bass eighths; upper accents at s8; locally strong upper s1/s3 onsets in bar 50',
      {47: '0:0+3 2:1 4:2 6:0 8:1+3 10:2 12:0 14:3',
       48: '2:1 4:2 6:0 8:1+3 10:2 12:0+3 14:1',
       49: '0:2 2:0 4:3 6:1 8:0+2 10:3 12:1 14:2',
       50: '0:0+3 1:2 2:1 3:3 4:0 6:2 8:1+3 10:0 12:2 14:1',
       51: '0:0+3 2:2 4:1 6:3 8:0 10:2 12:1 14:3',
       52: '0:1+2 2:0 4:3 6:1 8:0+2 10:3 12:1 14:2'}),
    P('P09', 'syncopated call/response',
      'A-bars: s0/s6 hit chords; B-bars: s0-s4 flurry into held s4 chord released at the s10 hit',
      'recurring measured 2-bar accent pattern; band-74 sustain without upper re-attack in bars 55/57',
      {53: '0:3 2:1 4:0+2 6:3 8:1+2 10:0 12:3 14:1',
       54: '0:3 2:1 4:2 6:0+3 8:1 10:2 12:0 14:1+3',
       55: '0:2 1:0 2:3 3:1 4:0+2h6 10:1+3 12:0 14:2',
       56: '0:1+3 4:0 6:1+2 9:3 12:0 15:2',
       57: '0:0 1:3 2:1 3:2 4:0+3h6 8:1 10:0+2 12:1 14:3',
       58: '0:1+2 4:0 6:1+3 10:0 14:2',
       59: '0:0+3 4:1 6:2 8:0 10:3 12:1'}),
    P('P10', 'break',
      'sparse 0-6-12 taps, held answer, drop-out rest, half-bar hit chords with holds',
      'low mix energy; measured tresillo upper accents; upper near-silent bar 64; sustained bands after the bar-65/66 hits',
      {60: '0:2 6:0 12:3',
       61: '0:1 6:3h6 12:0',
       62: '0:2 8:1 12:3 14:0',
       63: '0:2 8:0 12:3 14:1',
       64: '0:0+2',
       65: '0:1+3 8:0+2h8',
       66: '0:1h8+3 8:2 12:0'}),
    P('P11', 'main 2a',
      'interlock entry, then half-bar accent chords; quarter-hit hammer chords in bars 70/74; phrase-end stair',
      'bass/drum beats vs upper offbeats at bar 67; 4-bar recurrence of accent profiles (68~72, 69~73, 70~74); measured upper sixteenths bar 74',
      {67: '0:1+2 2:3 4:0 6:2 8:1 10:3 12:0 14:2',
       68: '0:0+3 2:1 4:2 6:0 8:3 10:1 12:0+2 14:3',
       69: '0:1 2:2 4:0+3 6:1 8:2 10:0+3 12:1 14:2',
       70: '0:0 2:3 4:1+2 6:0 8:1+3 10:2 12:0+3 14:1',
       71: '0:0+2 2:3 4:1 6:2 8:0 10:3 12:1 14:2',
       72: '0:1+3 2:0 4:2 6:1 8:3 10:0 12:1+2 14:3',
       73: '0:0 2:2 4:1+3 6:0 8:2 10:1+3 12:0 14:2',
       74: '0:1 2:3 4:0+2 6:1 8:0+3 10:2 12:0 13:1 14:2 15:3',
       75: '0:0+2 2:1 4:0+3 6:2 8:1 10:3 12:0 14:3'}),
    P('P12', 'main 2b',
      'tresillo jump-pair cell ([0,2] . . [1,3] . . [0,2] .) on 0-6-12 accents; bar-78 variation; backbeat chords bars 81-83',
      'recurring s0/s6/s12 mix accents with s6 upper onset peaks (bars 76-80); s4/s12 accents bars 81-83',
      {76: '0:0+2 2:3 4:0 6:1+3 8:2 10:1 12:0+2 14:3',
       77: '0:0+2 2:1 4:2 6:1+3 8:0 10:3 12:0+2 14:1',
       78: '0:3 2:0+2 6:1 8:3 10:0 12:1+2 14:3',
       79: '0:0+2 2:1 4:2 6:1+3 8:0 10:3 12:0+2 14:1',
       80: '0:0+2 2:3 4:1 6:0+3 8:2 10:1 12:0+2 14:3',
       81: '0:1 2:2 4:0+3 6:1 8:2 12:0+3 14:1',
       82: '0:2 2:1 4:0+3 6:2 8:1 10:3 12:0+2 14:3',
       83: '0:1 2:2 4:0+3 6:1 8:2 10:0 12:1+3 14:2'}),
    P('P13', 'main 2c',
      'upper-led eighths; flurry roll-back after the bar-86 chord; descending stair into bar-88 s12; paired jumps',
      'upper+drums texture with reduced bass; upper-only C-level beat accents; measured odd-slot upper attacks in bars 86/88',
      {84: '0:0+3 2:1 4:2 6:0 8:3 10:1 12:0+2 14:3',
       85: '0:1+2 2:0 4:3 6:1 8:2 10:0 12:1+3 14:2',
       86: '0:0+3 1:2 2:1 3:0 4:3 6:2 8:1 10:3 12:0+2 14:1+3',
       87: '0:0+2 2:3 4:1 6:2 8:0 10:3 12:1+2 14:0',
       88: '0:1+3 2:0 4:2 6:1 8:3 9:2 10:1 11:0 12:1+3 14:2',
       89: '0:0+3 2:1 4:2 6:0 8:1+3 12:0 14:2',
       90: '0:1+3 2:0 4:2 6:1 10:3 12:0+2 14:1'}),
    P('P14', 'stop + bridge',
      'held decay into the measured stop; bridge bars as a downbeat (often held) plus a short s10-s14 answer; riser turn into bar 101',
      'band-74 decay after bar-91 hit; empty s6-s11 stop in bar 92; low-energy upper attacks clustered at s0 and s10-s14; continuous s10-s15 attacks in bar 100',
      {91: '0:0+3h8',
       92: '0:1 12:3 14:1',
       93: '0:0+2h10 10:3 12:1 14:2',
       94: '0:0 4:3h8 12:1',
       95: '0:2h6 12:0 14:3',
       96: '0:1 4:2 8:0 10:3 12:1 14:2',
       97: '6:3h4 10:1 14:2',
       98: '0:0 2:3 6:1h6',
       99: '0:2 8:3 12:0',
       100: '0:1 2:3h8 10:2 12:0 13:1 14:2 15:1'}),
    P('P15', 'build 2',
      'gradual build: sparse chords to paired accents; descending stair into bar-106 s12 (parallel to build 1); 0-6-12 lull and pre-climax rest',
      'rising accent density bars 101-106; measured s8-s11 run bar 106; only s0/s6/s12 selectable in bar 107; weak bar 108 until upper pickups',
      {101: '0:0+3 2:2 4:1 8:3 10:0 12:2 14:1',
       102: '0:0 2:3 4:1 6:2 10:0 12:3 14:1',
       103: '0:0+2 2:3 4:1 6:2 8:0 10:3 12:1+2 14:0',
       104: '0:3 2:1 6:2 8:0+3 10:1 12:2 14:0+3',
       105: '0:1+2 4:0 6:3 8:1 10:2 12:0+3 14:1',
       106: '0:0+2 2:3 4:1 6:2 8:3 9:2 10:1 11:0 12:1+3 14:2',
       107: '0:0+3 6:1 12:2',
       108: '12:0 14:3'}),
    P('P16', 'climax A',
      'climax drive: half-bar beat chords, four-beat chord bars (110, 114) at the D-level peaks, 3-note pickup run at the group end',
      'all-source eighths with D-level accents on most beats; continuous upper sixteenth ornaments charted only at group ends',
      {109: '0:1+2 2:0 4:3 6:1 8:0+2 10:3 12:1+2 14:3',
       110: '0:0+2 2:1 4:0+3 6:2 8:1+3 10:0 12:1+2 14:3',
       111: '0:0+2 2:1 4:3 6:0 8:1+2 10:3 12:0 14:2',
       112: '0:1 2:3 4:0+2 6:1 8:0+3 10:2 12:1 13:2 14:3',
       113: '0:0+2 2:1 4:3 6:0 10:2 12:1+3 14:0',
       114: '0:1+2 2:3 4:0+2 6:1 8:0+3 10:2 12:1+3 14:0',
       115: '0:2 2:1 4:0+3 6:2 8:1 10:3 12:0+2 14:3',
       116: '0:1+2 2:0 4:3 6:1 10:2 12:0+3 14:1+2'}),
    P('P17', 'climax B',
      'drive variation: paired jumps at s12/s14, split zig-zag flurry into the bar-119 s4 chord, four-beat chord peak (120), 0-6-12 chords (121)',
      'C/D-level beat accents; missing bar-118 downbeat; measured s0-s4 upper/co-attack flurry bar 119; s0/s6/s12 accents bar 121',
      {117: '0:0 2:3 4:1+2 6:0 8:3 10:2 12:0+3 14:1',
       118: '2:2 4:0+3 6:1 8:2 10:0 12:1+3 14:0+2',
       119: '0:1 1:3 2:0 3:2 4:1+3 6:0 8:2 10:1 12:0+3 14:2',
       120: '0:1+3 2:0 4:1+2 6:3 8:0+2 10:1 12:0+3 14:2',
       121: '0:1+3 2:0 4:2 6:1+3 8:2 10:0 12:1+2 14:3'}),
    P('P18', 'pre-final break',
      'beat-led transition, 0-6-12 lull taps, held biggest hit (bar 124) released at the second hit',
      'drums+bass beats bar 122; only s0/s6/s12 strong in bar 123; strongest mix rise of the song at 124.0 with sustained bands to 124.8',
      {122: '0:0+2 2:1 4:3 6:0 8:2 10:1 12:3 14:0',
       123: '0:1 6:2 12:0',
       124: '0:1+3h8 8:0+2 10:1 12:3'}),
    P('P19', 'final section',
      'outer-chord tresillo (125) vs inner-chord answer (127); offbeat accent chords; flurry into bar-129 s4; V-shaped closing run (132)',
      'upper+drums dominant; strong offbeat accents (126.2, 128.6, 129.14, 130.10); 0-6-12 accents bars 125/131; continuous sixteenths bar 132',
      {125: '0:0+3 2:1 4:2 6:0+3 8:1 10:2 12:0+3 14:1',
       126: '0:2 2:0+3 4:1 6:2 8:3 10:0 14:1+2',
       127: '0:0 2:3 4:1+2 6:0 8:3 10:1+2 12:0 14:3',
       128: '0:0+2 2:3 4:1 6:0+3 8:2 10:1+3 12:0 14:2',
       129: '0:1 1:3 2:0 3:2 4:1 6:3 8:0+2 10:1 12:3 14:0+2',
       130: '0:1+3 2:0 4:1+2 6:3 10:0+2 12:1+3 14:0',
       131: '0:1+2 2:3 4:0 6:1+3 8:2 10:0 12:1+3 14:2',
       132: '0:0 2:1+3 4:2 6:0 8:3 9:2 10:1 11:0 12:1 13:2 14:3'}),
    P('P20', 'ending',
      'measured stop (rest), final hit chord, last upper attack; decay left empty',
      'weak bar-133 stop; 7E24 final hit at 134.0; last mix-confirmed upper attack 135.0; decaying weak events and invalid-energy tail not charted',
      {134: '0:0+3',
       135: '0:1'}),
]

DESIGN_NOTES = (
    "Claude Opus 5.5 (runtime-confirmed claude-opus-5-5) full-song design for every Chronomia section "
    "outside the human reference window [25000,45000) ms of full-mix-v2 analysis 8a57032b3a6f7755f84e. "
    "The parent splices the user's Refined chart (180 notes, 14 holds) into that window unchanged, "
    "including its four human-authored moments without a v2 event (27753, 31189, 39053, 40242 ms); none "
    "of them is represented here. Last AI start before the window: FG0270 at 24978 ms; first after: "
    "FG0500 at 45066 ms. The design follows the user's stated reference intent - steady eighth-note flow "
    "where measured attacks exist, two-hand chords (one lane per hand) on important evidenced accents, "
    "holds where a sustained layer is measured - and keeps intentional rests, measured stops and the "
    "recurring 0-6-12 accent figure instead of filling the grid. Sections: bars 0-2 near-silent rest; "
    "3-10 quarter-pulse intro; 11-18 build; 19-20 stop-time break; 21-23 bass-beat/upper-offbeat "
    "interlock into the reference; 42-46 accent stabs; 47-52 drive; 53-59 syncopated call/response; "
    "60-66 break; 67-90 second main section; 91-100 stop and bridge; 101-108 second build; 109-121 "
    "climax; 122-124 pre-final break with the song's strongest hit; 125-132 final section; 134 final "
    "hit, 135 last upper attack; the decay and the invalid-energy tail are left empty. Other-stem "
    "attacks are labelled upper-stem estimates, never melody; bass/drum-only selections are labelled "
    "rhythm-section support. Chords are authorial accents, not pitch claims; hold endpoints are time "
    "references, not certified releases. No audio was listened to; timing (227 BPM, offset 0), grid and "
    "acceleration settings are untouched. Phrase evidence, hold grades and open review choices are in "
    "RATIONALE.md."
)

TOKEN = re.compile(r"^(\d{1,2}):([0-3](?:h\d{1,2})?(?:\+[0-3](?:h\d{1,2})?)*)$")


def parse_design(design):
    notes = []
    for phrase in design:
        for bar, spec in phrase["bars"].items():
            for token in spec.split():
                match = TOKEN.match(token)
                if not match:
                    raise ValueError(f"{phrase['id']} bar {bar}: bad token {token!r}")
                sub = int(match.group(1))
                if not 0 <= sub < 16:
                    raise ValueError(f"{phrase['id']} bar {bar}: sixteenth out of range in {token!r}")
                lanes, holds = [], {}
                for item in match.group(2).split("+"):
                    lane = int(item[0])
                    lanes.append(lane)
                    if "h" in item:
                        holds[lane] = bar * 16 + sub + int(item.split("h")[1])
                if len(set(lanes)) != len(lanes):
                    raise ValueError(f"{phrase['id']} bar {bar}: duplicate lane in {token!r}")
                notes.append({"tick": bar * 16 + sub, "lanes": sorted(lanes), "holds": holds, "phrase": phrase})
    notes.sort(key=lambda n: n["tick"])
    ticks = [n["tick"] for n in notes]
    if len(set(ticks)) != len(ticks):
        dup = sorted(t for t, c in collections.Counter(ticks).items() if c > 1)
        raise ValueError(f"duplicate authored ticks: {dup}")
    return notes


def event_tick(event):
    return event["bar"] * 16 + event["beatInBar"] * 4 + event["sub"]


def has_upper(event):
    return any(p["sourceKey"] == "upper" for p in event["sourceParts"])


def provenance(event):
    keys = [p["sourceKey"] for p in event["sourceParts"]]
    text = "+".join(SOURCE_LABEL[k] for k in keys)
    if "upper" not in keys:
        text += " (rhythm-section support, not upper)"
    return text


def hold_band(by_tick, upper_ticks, start, end):
    """Upper-stem frequency band present after the start attack and before every later
    upper attack up to the endpoint, plus energy continuity relative to the start."""
    first = by_tick[start]
    if not has_upper(first):
        return None
    band = {b for b, _ in first["upperEvidence"]["afterPitchEnergyBins"]}
    reference = first["upperEvidence"]["rmsAfterAbsolute"]
    inner, continuity = 0, []
    for tick in upper_ticks:
        if start < tick <= end:
            event = by_tick[tick]
            band &= {b for b, _ in event["upperEvidence"]["beforePitchEnergyBins"]}
            continuity.append(event["upperEvidence"]["rmsBeforeAbsolute"] / max(reference, 1e-9))
            if tick < end:
                inner += 1
    if not continuity:
        return None
    return {"band": sorted(band), "innerUpperAttacks": inner, "minContinuity": round(min(continuity), 2)}


def human_spans(human):
    spans = []
    for note in human["notes"]:
        tick = math.floor(note["timeMs"] / TICK_MS + 0.5)
        end_ms = note["timeMs"] + note.get("durationMs", 0)
        end_tick = math.floor(end_ms / TICK_MS + 0.5)
        if abs(tick * TICK_MS - note["timeMs"]) > 0.5 or abs(end_tick * TICK_MS - end_ms) > 0.5:
            raise ValueError(f"human note off the sixteenth grid: {note}")
        spans.append((note["lane"], tick, end_tick, "human"))
    return spans


def validate(notes, by_tick, upper_ticks, human):
    errors, holds = [], []
    w0, w1 = WINDOW_MS
    for note in notes:
        tick = note["tick"]
        event = by_tick.get(tick)
        if event is None:
            errors.append(f"bar {tick // 16}.{tick % 16}: no selectable event")
            continue
        mix = event["mixVerification"]
        if not (mix["positiveChangeValid"] and mix["spectralComparisonValid"]):
            errors.append(f"{event['id']}: invalid-energy comparison")
        if w0 <= event["chartMs"] < w1:
            errors.append(f"{event['id']}: inside the human reference window")
        lanes = note["lanes"]
        if len(lanes) > 2 or (len(lanes) == 2 and (set(lanes) <= {0, 1} or set(lanes) <= {2, 3})):
            errors.append(f"{event['id']}: chord {lanes} is not one lane per hand")
        for lane, end_tick in note["holds"].items():
            end = by_tick.get(end_tick)
            if end is None:
                errors.append(f"{event['id']}: hold end bar {end_tick // 16}.{end_tick % 16} has no selectable event")
                continue
            if end_tick <= tick:
                errors.append(f"{event['id']}: hold end not later")
            if not (end["mixVerification"]["positiveChangeValid"] and end["mixVerification"]["spectralComparisonValid"]):
                errors.append(f"{event['id']}: hold end {end['id']} invalid-energy")
            if (event["chartMs"] < w0) != (end["chartMs"] < w0) or (event["chartMs"] < w1) != (end["chartMs"] < w1):
                errors.append(f"{event['id']}: hold crosses a reference boundary")
            band = hold_band(by_tick, upper_ticks, tick, end_tick)
            if not band or not band["band"]:
                errors.append(f"{event['id']}: hold has no persistent upper band")
            holds.append({"start": event["id"], "startMs": event["chartMs"], "end": end["id"], "endMs": end["chartMs"],
                          "lane": lane, "ticks": end_tick - tick, **(band or {})})
    lane_spans = collections.defaultdict(list)
    for note in notes:
        for lane in note["lanes"]:
            lane_spans[lane].append((note["tick"], note["holds"].get(lane, note["tick"]), "AI"))
    for lane, start, end, source in human_spans(human):
        lane_spans[lane].append((start, end, source))
    for lane, spans in lane_spans.items():
        spans.sort()
        for (s1, e1, a), (s2, e2, b) in zip(spans, spans[1:]):
            if "AI" not in (a, b):
                continue
            if s2 - s1 < 2:
                errors.append(f"lane {lane}: starts {s1}->{s2} under 2 sixteenths ({a}->{b})")
            if s2 < e1:
                errors.append(f"lane {lane}: start {s2} inside hold {s1}-{e1}")
            elif e1 > s1 and s2 - e1 < 2:
                errors.append(f"lane {lane}: restart {s2} under 2 sixteenths after hold end {e1}")
    return errors, holds


def role(note, ticks):
    parts = []
    if len(note["lanes"]) > 1:
        parts.append("accent chord")
    if note["holds"]:
        parts.append("hold")
    if note["tick"] - 1 in ticks or note["tick"] + 1 in ticks:
        parts.append("run step")
    return ", ".join(parts) or "flow"


def assemble(notes, by_tick):
    ticks = {n["tick"] for n in notes}
    items = []
    for note in notes:
        event = by_tick[note["tick"]]
        item = {"eventId": event["id"], "lanes": note["lanes"]}
        if note["holds"]:
            item["holdEnds"] = {str(lane): by_tick[end]["id"] for lane, end in sorted(note["holds"].items())}
        phrase = note["phrase"]
        item["motif"] = f"{phrase['id']} {phrase['section']}: {role(note, ticks)}"
        item["focus"] = f"{provenance(event)}; {phrase['focus']}"
        items.append(item)
    return {"schemaVersion": 1, "analysisId": ANALYSIS_ID, "designNotes": DESIGN_NOTES, "notes": items}


def render(plan):
    head = (f'{{\n "schemaVersion": {plan["schemaVersion"]},\n "analysisId": {json.dumps(plan["analysisId"])},\n'
            f' "designNotes": {json.dumps(plan["designNotes"], ensure_ascii=False)},\n "notes": [\n')
    body = ",\n".join("  " + json.dumps(item, ensure_ascii=False) for item in plan["notes"])
    return head + body + "\n ]\n}\n"


def main():
    template_bytes = TEMPLATE.read_bytes()
    if hashlib.sha256(template_bytes).hexdigest() != TEMPLATE_SHA256:
        raise SystemExit("template hash differs from the provenance record; stop")
    analysis_bytes = ANALYSIS.read_bytes()
    analysis = json.loads(analysis_bytes)
    if analysis.get("analysisId") != ANALYSIS_ID:
        raise SystemExit("unexpected analysisId; stop")
    alignment = analysis["alignment"]
    if (alignment["bpm"], alignment["offsetMs"], alignment["bpmChanges"], alignment["allowedSubdivisionsPerBeat"]) != (227.0, 0.0, [], [4]):
        raise SystemExit("unexpected timing/grid in analysis; stop")
    template = json.loads(template_bytes.decode("utf-8-sig"))
    human = json.loads(HUMAN.read_text(encoding="utf-8-sig"))
    by_tick = {}
    for event in analysis["events"]:
        tick = event_tick(event)
        if tick in by_tick or abs(tick * TICK_MS - event["chartMs"]) > 0.5:
            raise SystemExit(f"event/grid mapping failed for {event['id']}")
        by_tick[tick] = event
    upper_ticks = sorted(t for t, e in by_tick.items() if has_upper(e))

    notes = parse_design(DESIGN)
    errors, holds = validate(notes, by_tick, upper_ticks, human)
    if errors:
        print("VALIDATION ERRORS:\n- " + "\n- ".join(errors))
        raise SystemExit(1)
    plan = assemble(notes, by_tick)
    text = render(plan)
    if json.loads(text) != plan:
        raise SystemExit("rendered plan does not round-trip")

    sys.path.insert(0, str(REPO / "Tools/ai-chart"))
    from build import compile_chart
    from validate import evaluate
    chart, report = compile_chart(analysis, copy.deepcopy(plan), template)
    if not report["valid"]:
        raise SystemExit("compile smoke invalid: " + "; ".join(report["errors"]))
    for key in ("timing", "autoCoef", "specialNotes"):
        if chart.get(key) != template.get(key):
            raise SystemExit(f"compile smoke changed template field {key}")
    combined = copy.deepcopy(chart)
    combined["notes"] = sorted(chart["notes"] + copy.deepcopy(human["notes"]), key=lambda n: (n["timeMs"], n["lane"]))
    combined_report = evaluate(combined)
    if not combined_report["valid"]:
        raise SystemExit("AI + human splice invalid: " + "; ".join(combined_report["errors"]))

    if OUTPUT.exists():
        if OUTPUT.read_text(encoding="utf-8") != text:
            raise SystemExit("existing full.plan.json differs from the deterministic assembly; refusing to overwrite")
        status = "verified existing full.plan.json (byte-identical)"
    else:
        with OUTPUT.open("x", encoding="utf-8") as handle:
            handle.write(text)
        status = "wrote full.plan.json"
    if hashlib.sha256(TEMPLATE.read_bytes()).hexdigest() != TEMPLATE_SHA256 or ANALYSIS.read_bytes() != analysis_bytes:
        raise SystemExit("input file changed during run")

    moments = sorted(n["tick"] for n in notes)
    gaps = collections.Counter(b - a for a, b in zip(moments, moments[1:]) if not (a * TICK_MS < WINDOW_MS[0] <= b * TICK_MS))
    sources = collections.Counter("+".join(p["sourceKey"] for p in by_tick[t]["sourceParts"]) for t in moments)
    summary = {
        "status": status,
        "planSha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "moments": len(notes),
        "laneNotes": sum(len(n["lanes"]) for n in notes),
        "chordMoments": sum(len(n["lanes"]) > 1 for n in notes),
        "holds": len(holds),
        "oddSixteenthMoments": sum(t % 2 for t in moments),
        "upperSupportedMoments": sum(has_upper(by_tick[t]) for t in moments),
        "rhythmSectionOnlyMoments": sum(not has_upper(by_tick[t]) for t in moments),
        "sourceCombinations": dict(sorted(sources.items())),
        "gapCensusSixteenths": dict(sorted(gaps.items())),
        "firstAndLast": [plan["notes"][0]["eventId"], plan["notes"][-1]["eventId"]],
        "compileSmoke": {k: report["stats"][k] for k in ("notes", "holds", "attackMoments", "chordRate", "laneDistribution", "peakNps1x", "peakNps2xEstimated")},
        "compileWarnings": report["warnings"],
        "combinedWithHuman": combined_report["stats"],
        "combinedWarnings": combined_report["warnings"],
        "holdEvidence": holds,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
