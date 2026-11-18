"""Rhythm drafts from the original chart, with an even density across the song.
easy(): a quarter-note pulse on the original's onsets (off-beat when the beat itself is empty), one 8th pair
every `pair_every` bars at a fixed place in the bar (the pickup into the next bar when the music has it),
a chord on the downbeat every `chord_every` bars, holds only where the original sustains.
mid(): the original on an 8th grid, varied bar by bar with phrase templates (5-note runs, plain quarters,
runs into the next downbeat) instead of one repeated figure."""
import json, collections
def _grid(src):
    d = json.load(open(src, encoding='utf-8')); beat = 60000 / d['timing']['bpm']; q = beat / 4
    notes = d['notes']; c = collections.Counter(round((n['timeMs'] / beat % 1) * 96) % 96 for n in notes)
    ph = max(range(96), key=lambda x: c[x] + c[(x + 48) % 96] * .5); off = ph / 96 * beat
    at = collections.defaultdict(list)
    for n in notes: at[round((n['timeMs'] - off) / q)].append(n)
    return beat, at, max(at) // 16
def _strength(ns, beat): return len({n['lane'] for n in ns}) + (1.5 if any(n.get('durationMs', 0) >= beat for n in ns) else 0)
def _hold(ns, beat, hmin): return any(n.get('durationMs', 0) >= hmin * beat for n in ns)
def easy(src, pair_every=1, chord_every=1, hold_min=1.5, pair_beats=(3, 1), start_bar=0):
    beat, at, last = _grid(src); R = {}
    for m in range(last + 1):
        row = ['.'] * 16
        for b in range(4):
            s = 4 * b; k = m * 16 + s
            on, offb = at.get(k, []), at.get(k + 2, [])
            # take the stronger of the beat and its off-beat (a held or chorded off-beat is the accent)
            if on and (not offb or _strength(on, beat) + (1.5 if b == 0 else 0.5) >= _strength(offb, beat)): pick = s
            elif offb: pick = s + 2
            else: continue
            row[pick] = 'h' if _hold(at[k + pick - s], beat, hold_min) else 'x'
        if (m - start_bar) % chord_every == 0 and row[0] == 'x' and len({n['lane'] for n in at.get(m * 16, [])}) >= 2: row[0] = 'c'
        if (m - start_bar) % pair_every == 0:
            for b in pair_beats:
                s = 4 * b; k = m * 16 + s
                if row[s] in 'xc' and at.get(k + 2) and row[s + 2] == '.' and not _hold(at.get(k, []), beat, 0.6):
                    row[s + 2] = 'x'; break
                if row[s] == '.' and row[s + 2] in 'xh' and at.get(k):
                    row[s] = 'x'; break
        if any(ch != '.' for ch in row): R[m] = ''.join(row)
    return R
TEMPLATES = {'A': '11111010', 'B': '10101111', 'C': '11101110', 'D': '10101011', 'Q': '10101010', 'F': '11111111'}
def mid(src, phrase='ABAD', hold_min=1.0, chord_beats_only=True, chord_slots=(0, 4, 8, 12)):
    beat, at, last = _grid(src); R = {}
    for m in range(last + 1):
        mask = TEMPLATES[phrase[m % len(phrase)]]
        row = ['.'] * 16
        for e in range(8):
            s = 2 * e; ns = at.get(m * 16 + s, [])
            if not ns: continue
            if mask[e] == '0' and e % 2 == 1 and len({n['lane'] for n in ns}) == 1 and not _hold(ns, beat, 0.75): continue   # templates drop plain off-beat 8ths only
            if _hold(ns, beat, hold_min): row[s] = 'h'
            elif len({n['lane'] for n in ns}) >= 2 and (s in chord_slots or not chord_beats_only): row[s] = 'c'
            else: row[s] = 'x'
        if any(ch != '.' for ch in row): R[m] = ''.join(row)
    return R
