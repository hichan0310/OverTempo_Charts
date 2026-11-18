"""Pattern quality report: hold ratio, same-hand runs, jacks, density spread over 2-bar windows."""
import json, sys, collections, statistics
def report(path, verbose=False):
    d = json.load(open(path)); beat = 60000 / d['timing']['bpm']
    notes = sorted(d['notes'], key=lambda n: (n['timeMs'], n['lane']))
    c = collections.Counter(round((n['timeMs'] / beat % 1) * 96) % 96 for n in notes)
    off = max(range(96), key=lambda x: c[x] + c[(x + 48) % 96] * .5) / 96 * beat
    bar = lambda t: int((t - off) // (4 * beat))
    ev = collections.OrderedDict()
    for n in notes: ev.setdefault(n['timeMs'], []).append(n)
    times = list(ev)
    holds = sum(1 for n in notes if n['durationMs'] > 0)
    # same-hand runs: consecutive single-note events within 1 beat on one hand
    runs = []; run = 0; prevhand = None; prevt = -1e9
    bad_runs = collections.Counter()
    for t in times:
        e = ev[t]
        hands = {0 if n['lane'] < 2 else 1 for n in e}
        if len(hands) == 1 and (t - prevt) <= beat * 1.01 and hands == {prevhand}: run += 1
        else: run = 1
        prevhand = next(iter(hands)) if len(hands) == 1 else None; prevt = t
        if run >= 3: bad_runs[bar(t)] += 1
        runs.append(run)
    jacks = collections.Counter()
    for i in range(1, len(times)):
        g = (times[i] - times[i - 1]) / beat
        if g <= 1.01 and {n['lane'] for n in ev[times[i - 1]]} & {n['lane'] for n in ev[times[i]]}: jacks[bar(times[i])] += 1
    per = collections.Counter(bar(n['timeMs']) for n in notes)
    bars = range(min(per), max(per) + 1)
    win = [per[b] + per[b + 1] for b in bars if per[b] + per[b + 1] > 0]
    q = statistics.quantiles(win, n=10)
    name = path.split('/')[-1][:44]
    print(f"{name:44} n={len(notes):4} hold={holds/len(notes):4.0%} maxrun={max(runs)} runs3+={sum(bad_runs.values()):3} jacks={sum(jacks.values()):3} "
          f"2bar p10/p50/p90={q[0]:.0f}/{statistics.median(win):.0f}/{q[-1]:.0f}")
    if verbose:
        print('  runs3+ bars:', dict(sorted(bad_runs.items())))
        print('  jack bars:', dict(sorted(jacks.items())))
        print('  notes/bar:', ' '.join(f'{b}:{per[b]}' for b in bars))
if __name__ == '__main__':
    v = '-v' in sys.argv
    for p in [a for a in sys.argv[1:] if a != '-v']: report(p, v)
