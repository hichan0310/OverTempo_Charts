import json,sys,collections
p=sys.argv[1]; d=json.load(open(p)); bpm=d['timing']['bpm']; beat=60000/bpm
notes=d['notes']
# grid phase from notes
c=collections.Counter(round(((n['timeMs'])/beat%1)*96)%96 for n in notes); ph=max(range(96),key=lambda x:c[x]+c[(x+48)%96]*.5)
off=ph/96*beat
sub=int(sys.argv[2]) if len(sys.argv)>2 else 4   # slots per beat
slots=collections.defaultdict(set); holds={}
for n in notes:
    pos=(n['timeMs']-off)/beat*sub; k=round(pos)
    if abs(pos-k)>0.25: k=('x',round(pos*3)) # tuplet
    slots[k].add(n['lane'])
    if n.get('durationMs',0)>0: holds[(k,n['lane'])]=round(n['durationMs']/beat,2)
mx=max(k for k in slots if isinstance(k,int))
sp=d.get('specialNotes') or []
spm={int(round((s['timeMs']-off)/beat*sub)):s for s in sp}
per=4*sub
for m in range(0,mx//per+1):
    row=[]
    for k in range(m*per,(m+1)*per):
        ls=slots.get(k,set()); h=[l for l in ls if (k,l) in holds]
        cell=''.join(str(l+1) if (k,l) not in holds else 'DFJK'[l] for l in sorted(ls)) or '.'
        if k in spm: cell='*'+cell
        row.append(cell.ljust(3))
    t=(m*per)/sub*beat+off
    print(f"{m:3d} {t/1000:6.1f}s | "+' '.join(row[i] for i in range(per)))
