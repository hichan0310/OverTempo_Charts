"""List awkward spots in a built chart, by measure: 8th jacks, one-hand trills, chord jacks, chord runs."""
import json, sys, collections
d = json.load(open(sys.argv[1])); beat = 60000 / d['timing']['bpm']; notes = sorted(d['notes'], key=lambda n: (n['timeMs'], n['lane']))
c = collections.Counter(round((n['timeMs'] / beat % 1) * 96) % 96 for n in notes); off = max(range(96), key=lambda x: c[x] + c[(x + 48) % 96] * .5) / 96 * beat
meas = lambda t: int((t - off) // (4 * beat))
ev = collections.OrderedDict()
for n in notes: ev.setdefault(n['timeMs'], []).append(n)
times = list(ev); flags = collections.defaultdict(list)
for i in range(1, len(times)):
    a, b = ev[times[i - 1]], ev[times[i]]; g = (times[i] - times[i - 1]) / beat
    la = {n['lane'] for n in a}; lb = {n['lane'] for n in b}
    ends = {n['lane'] for n in a if n['durationMs'] > 0}
    if g <= 0.51 and (la & lb):
        flags[meas(times[i])].append('jack' if len(la) == 1 and len(lb) == 1 else 'chordjack')
for i in range(3, len(times)):
    w = [ev[times[j]] for j in range(i - 3, i + 1)]
    gs = [(times[j] - times[j - 1]) / beat for j in range(i - 2, i + 1)]
    if all(len(x) == 1 for x in w) and max(gs) <= 0.51:
        ls = [x[0]['lane'] for x in w]
        if all(l < 2 for l in ls) or all(l >= 2 for l in ls): flags[meas(times[i])].append('onehand')
    if all(len(x) >= 2 for x in w[1:]) and max(gs[1:]) <= 1.01: flags[meas(times[i])].append('chords3')
print(' '.join(f"{m}:{','.join(sorted(set(v)))}" for m, v in sorted(flags.items())))
