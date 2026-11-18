"""Draft plan for a middle chart: the original on an 8th grid (16th notes dropped), chords only on beats,
holds kept; in 8th runs the off-beat 8th of beats 2 and 4 is dropped so a bar reads 'x.x. x... x.x. x...'.
The draft is only the starting point: each song's plan overrides measures by hand."""
import json, collections
def auto(src, thin=True):
    d = json.load(open(src, encoding='utf-8')); beat = 60000 / d['timing']['bpm']; q = beat / 4
    notes = d['notes']
    c = collections.Counter(round((n['timeMs'] / beat % 1) * 96) % 96 for n in notes)
    ph = max(range(96), key=lambda x: c[x] + c[(x + 48) % 96] * .5); off = ph / 96 * beat
    at = collections.defaultdict(list)
    for n in notes: at[round((n['timeMs'] - off) / q)].append(n)
    last = max(at) // 16
    R = {}
    for m in range(last + 1):
        row = ['.'] * 16
        for s in range(0, 16, 2):
            ns = at.get(m * 16 + s, [])
            if not ns: continue
            if any(n.get('durationMs', 0) > 0 for n in ns): row[s] = 'h'
            elif len(ns) >= 2 and s % 4 == 0: row[s] = 'c'
            else: row[s] = 'x'
        if thin:
            for s in (6, 14):
                if row[s] == 'x' and row[s - 2] != '.' and row[(s + 2) % 16 if s == 6 else 0] != '.' and row[s-6] != '.':
                    row[s] = '.'
        if any(ch != '.' for ch in row): R[m] = ''.join(row)
    return R
