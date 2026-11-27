"""Chart builder v2: a rhythm plan per measure (x single, c chord, h hold, '.' rest, 16 slots) plus explicit
cells, with lanes assigned for playability: follow the original's contour (up/down), keep the hands
alternating (penalise 3+ notes in a row on one hand), no jacks inside JACK_BEATS, chords split across the
hands, keep the left/right balance. Holds only where the original holds at least HOLD_MIN_BEATS; other 'h'
become taps. Special notes, timing and effects are copied from the original."""
import json, collections, copy, sys, bisect, importlib.util
def load_plan(path):
    spec = importlib.util.spec_from_file_location('plan', path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m
def grid(d):
    beat = 60000 / d['timing']['bpm']; q = beat / 4; notes = d['notes']
    c = collections.Counter(round((n['timeMs'] / beat % 1) * 96) % 96 for n in notes)
    ph = max(range(96), key=lambda x: c[x] + c[(x + 48) % 96] * .5); off = ph / 96 * beat
    at = collections.defaultdict(list)
    for n in notes: at[round((n['timeMs'] - off) / q)].append(n)
    return beat, q, off, at
HAND = lambda l: 0 if l < 2 else 1
def build(src, plan_path, dst, level, name, extra):
    d = json.load(open(src, encoding='utf-8')); beat, q, off, at = grid(d); notes = d['notes']
    P = load_plan(plan_path)
    R = getattr(P, 'R', {}); O = getattr(P, 'O', {})
    HMIN = getattr(P, 'HOLD_MIN_BEATS', 1.5); HMAX = getattr(P, 'HOLD_MAX_BEATS', 2.0)
    JACK = getattr(P, 'JACK_BEATS', 1.0); RUNMAX = getattr(P, 'HAND_RUN', 2); ONEHAND_CHORD = getattr(P, 'ONEHAND_CHORD_COST', 3.0); SPIRAL = getattr(P, 'SPIRAL_COST', 3.0)
    proto = {k: v for k, v in notes[0].items() if k not in ('timeMs', 'lane', 'durationMs')}
    accel = sorted((n['timeMs'], n.get('speedupCoef', 0)) for n in notes if n.get('speedupCoef', 0) > 0); att = [a for a, _ in accel]
    def coef_at(t):
        i = bisect.bisect_left(att, t)
        return min((abs(accel[j][0] - t), accel[j][1]) for j in (i - 1, i) if 0 <= j < len(accel))[1]
    def mk(t, lane, dur, first):
        n = dict(proto); n.update(timeMs=int(round(t)), lane=lane, durationMs=int(round(dur)))
        n['baseSpeedupCoef'] = 1 if first else 0; n['speedupCoef'] = round(coef_at(t), 6) if first else 0
        for k in ('densitySpeedupCoefMultiplier', 'rampSpeedupCoefMultiplier', 'manualSpeedupCoefMultiplier', 'autoSpeedupCoefMultiplier'):
            if k in n: n[k] = 1 if first else 0
        return n
    out = []
    hist = []            # (time, lanes) of placed events
    busy = {}            # lane -> hold end time
    prev_target = None
    def free(l, t): return busy.get(l, -1e18) < t - 1
    def recent_run(hand, t):
        r = 0; tt = t
        for (pt, ls) in reversed(hist):
            if (tt - pt) > beat * 1.01 or len({HAND(l) for l in ls}) != 1 or HAND(ls[0]) != hand: break
            r += 1; tt = pt
        return r
    def balance_cost(hand):
        last = [HAND(l) for _, ls in hist[-8:] for l in ls]
        if not last: return 0
        f = sum(1 for h in last if h == 0) / len(last)
        return max(0, f - 0.5) * 4 if hand == 0 else max(0, 0.5 - f) * 4
    def jack_cost(l, t):
        if not hist: return 0
        pt, ls = hist[-1]; g = (t - pt) / beat
        if l in ls and g <= JACK + 0.01: return 1e6
        if len(hist) >= 2:
            pt2, ls2 = hist[-2]
            if l in ls2 and (t - pt2) / beat <= JACK * 0.5 + 0.01: return 1e6
        if l in ls and g <= 2 * JACK + 0.01: return 0.8
        return 0
    def place_single(t, target, direction):
        best = None
        for l in range(4):
            if not free(l, t): continue
            cost = abs(l - target) * 0.7 + jack_cost(l, t) + balance_cost(HAND(l))
            if hist:
                pl = hist[-1][1]; plane = pl[-1] if len(pl) == 1 else None
                if plane is not None and direction:
                    if direction > 0 and l <= plane: cost += 1.2
                    if direction < 0 and l >= plane: cost += 1.2
                r = recent_run(HAND(l), t)
                if r >= RUNMAX: cost += 3 + 3 * (r - RUNMAX)
                elif r == RUNMAX - 1 and RUNMAX >= 2: cost += 0.4
                # spiral: a third adjacent step in the same direction (1-2-3-4)
                if SPIRAL and len(hist) >= 2 and len(hist[-1][1]) == 1 and len(hist[-2][1]) == 1:
                    a, b2 = hist[-2][1][0], hist[-1][1][0]
                    if abs(b2 - a) == 1 and l - b2 == b2 - a: cost += SPIRAL * (0.5 if len(hist) < 3 or len(hist[-3][1]) != 1 or hist[-2][1][0] - hist[-3][1][0] != b2 - a else 1)
                # one-hand trill: same hand, back to the lane two notes ago
                if len(hist) >= 2 and len(hist[-2][1]) == 1 and hist[-2][1][0] == l and HAND(hist[-1][1][0]) == HAND(l) and (t - hist[-2][0]) / beat <= 1.01:
                    cost += 4
            if best is None or cost < best[0]: best = (cost, l)
        return None if best is None else best[1]
    def place_chord(t, ol):
        best = None
        for a in range(4):
            for b in range(a + 1, 4):
                if not (free(a, t) and free(b, t)): continue
                cost = jack_cost(a, t) + jack_cost(b, t)
                if HAND(a) == HAND(b): cost += ONEHAND_CHORD
                if ol: cost += 0.3 * (min(abs(a - x) for x in ol) + min(abs(b - x) for x in ol))
                if hist and set(hist[-1][1]) == {a, b}: cost += 1.5          # same chord again
                if best is None or cost < best[0]: best = (cost, [a, b])
        return None if best is None else best[1]
    measures = sorted(set(R) | set(O))
    for m in measures:
        cells = O.get(m); plan = R.get(m, '')
        for s in range(16):
            k = m * 16 + s; orig = sorted(at.get(k, []), key=lambda n: n['lane'])
            t = min((n['timeMs'] for n in orig), key=lambda x: abs(x - (off + k * q))) if orig else off + k * q   # the on-grid one of flammed notes
            ol = [n['lane'] for n in orig] or [n['lane'] for n in (at.get(k - 1) or at.get(k + 1) or [])]
            ohold = [n['durationMs'] for n in orig if n.get('durationMs', 0) > 0]
            if cells is not None:
                cell = cells[s]
                if cell == '.': continue
                lanes = [int(ch) - 1 for ch in cell if ch.isdigit()]
                dur = min(ohold[0] if ohold else beat, HMAX * beat) if 'h' in cell else 0
                lanes = [l for l in lanes if free(l, t)]
                if not lanes: continue
                for i, l in enumerate(lanes): out.append(mk(t, l, dur, i == 0))
                for l in lanes:
                    if dur: busy[l] = t + dur
                hist.append((t, lanes)); prev_target = sum(lanes) / len(lanes); continue
            if s >= len(plan) or plan[s] == '.': continue
            kind = plan[s]
            # melody target: the tap that is new against the previous original slot, else the top tap
            taps = [n['lane'] for n in orig if n.get('durationMs', 0) == 0] or ol
            prevo = set()
            for j in range(1, 5):
                if at.get(k - j): prevo = {n['lane'] for n in at[k - j]}; break
            fresh = [l for l in taps if l not in prevo]
            target = (max(fresh) if fresh else max(taps)) if taps else 1.5
            if kind == 'c':
                lanes = place_chord(t, ol)
                if lanes is None: kind = 'x'
                else:
                    for i, l in enumerate(lanes): out.append(mk(t, l, 0, i == 0))
                    hist.append((t, lanes)); prev_target = target; continue
            direction = 0 if prev_target is None else (1 if target > prev_target + 0.25 else -1 if target < prev_target - 0.25 else 0)
            l = place_single(t, target, direction)
            if l is None: continue
            dur = 0
            if kind == 'h' and ohold and ohold[0] >= HMIN * beat:
                dur = min(ohold[0], HMAX * beat); busy[l] = t + dur
            out.append(mk(t, l, dur, True)); hist.append((t, [l])); prev_target = target
    out.sort(key=lambda n: (n['timeMs'], n['lane']))
    e = copy.deepcopy(d); e['notes'] = out; e['difficulty']['level'] = level; e['difficulty']['name'] = name; e['meta']['extra'] = extra
    json.dump(e, open(dst, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    span = (notes[-1]['timeMs'] - notes[0]['timeMs']) / 1000
    print(f'{len(notes)} -> {len(out)} notes, nps {len(notes)/span:.2f} -> {len(out)/span:.2f}')
if __name__ == '__main__':
    lv = float(sys.argv[4]); build(*sys.argv[1:4], int(lv) if lv == int(lv) else lv, sys.argv[5], sys.argv[6])
