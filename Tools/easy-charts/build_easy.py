"""Turn a hand-written rhythm plan into notes. Lanes follow the original chart's melody at each planned slot;
explicit overrides ({measure: '16-cell string with lane digits'}) replace the plan for a measure entirely."""
import json,collections,copy,sys,importlib.util
def load_plan(path):
    spec=importlib.util.spec_from_file_location('plan',path); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m.R, getattr(m,'O',{}), getattr(m,'HOLD_MAX_BEATS',2.0)
def build(src,plan_path,dst,level,name,extra):
    d=json.load(open(src,encoding='utf-8')); bpm=d['timing']['bpm']; beat=60000/bpm; q=beat/4
    notes=d['notes']
    c=collections.Counter(round((n['timeMs']/beat%1)*96)%96 for n in notes); ph=max(range(96),key=lambda x:c[x]+c[(x+48)%96]*.5)
    off=ph/96*beat
    at=collections.defaultdict(list)
    for n in notes: at[round((n['timeMs']-off)/q)].append(n)
    R,O,HM=load_plan(plan_path)
    out=[]; prev=None; prev_t=-1e9; busy={}; prevset=set()
    proto={k:v for k,v in notes[0].items() if k not in('timeMs','lane','durationMs')}
    accel=sorted((n['timeMs'],n.get('speedupCoef',0)) for n in notes if n.get('speedupCoef',0)>0)
    import bisect
    at_times=[a for a,_ in accel]
    def coef_at(t):   # the original chart's acceleration coefficient around this time
        i=bisect.bisect_left(at_times,t)
        best=min((abs(accel[j][0]-t),accel[j][1]) for j in (i-1,i) if 0<=j<len(accel))
        return best[1]
    def mk(t,lane,dur=0,coef=None):
        n=dict(proto); n.update(timeMs=int(round(t)),lane=lane,durationMs=int(round(dur)))
        first=coef is None or coef>0
        n['baseSpeedupCoef']=1 if first else 0
        n['speedupCoef']=round(coef_at(t),6) if first else 0
        for k in ('densitySpeedupCoefMultiplier','rampSpeedupCoefMultiplier','manualSpeedupCoefMultiplier','autoSpeedupCoefMultiplier'):
            if k in n: n[k]=1 if first else 0
        return n
    for m in sorted(set(R)|set(O)):
        cells=O.get(m)
        plan=R.get(m,'')
        if plan=='=' and cells is None:   # keep the original measure as it is
            for s in range(16):
                for n in at.get(m*16+s,[]): out.append(copy.deepcopy(n))
            mn=[n for s in range(16) for n in at.get(m*16+s,[])]
            if mn: last=max(mn,key=lambda n:n['timeMs']); prev=last['lane']; prev_t=last['timeMs']; prevset={n['lane'] for n in mn if n['timeMs']==last['timeMs']}
            continue
        for s in range(16):
            k=m*16+s; orig=sorted(at.get(k,[]),key=lambda n:n['lane'])
            t=orig[0]['timeMs'] if orig else off+k*q
            if cells is not None:
                cell=cells[s]
                if cell=='.': continue
                lanes=[int(ch)-1 for ch in cell if ch.isdigit()]
                hold='h' in cell
                dur=0
                if hold:
                    oh=[n['durationMs'] for n in orig if n.get('durationMs',0)>0]
                    dur=min(oh[0] if oh else beat,HM*beat)
                for i,l in enumerate(lanes): out.append(mk(t,l,dur,1 if i==0 else 0))
                prev=lanes[0]; prevset=set(lanes); prev_t=t; continue
            if s>=len(plan) or plan[s]=='.': continue
            kind=plan[s]
            ol=[n['lane'] for n in orig]
            if not ol:   # nothing in the original here: nearest original note within a slot
                near=at.get(k-1) or at.get(k+1) or []
                ol=[n['lane'] for n in near]
            gap=(t-prev_t)/beat
            if kind=='c':
                if len(ol)>=2: lanes=[ol[0],ol[-1]]
                elif ol: lanes=sorted({ol[0],3-ol[0]}) if ol[0] not in(1,2) else sorted({ol[0],3-ol[0]})
                else: lanes=[0,3]
                if lanes[0]==lanes[1]: lanes=[0,3]
                for i,l in enumerate(lanes): out.append(mk(t,l,0,1 if i==0 else 0))
                prev=lanes[-1]; prevset=set(lanes); prev_t=t; continue
            if kind=='h':
                oh=[n for n in orig if n.get('durationMs',0)>0]
                lane=oh[0]['lane'] if oh else (ol[0] if ol else 1)
                dur=min(oh[0]['durationMs'] if oh else beat, HM*beat)
                out.append(mk(t,lane,dur)); prev=lane; prevset={lane}; prev_t=t; continue
            # single: the chord lane that keeps the line moving (no jack inside a beat)
            cand=ol or [((prev or 0)+2)%4]
            choice=None
            near=gap<=1.01
            for l in sorted(cand,key=lambda l:(near and l in prevset, l==prev, abs(l-(prev if prev is not None else l)))):
                choice=l; break
            if near and choice in prevset:   # no jack inside a beat, also after a chord
                choice=min([l for l in range(4) if l not in prevset],key=lambda l:abs(l-prev))
            out.append(mk(t,choice)); prev=choice; prevset={choice}; prev_t=t
    # specials, effects etc. stay as in the original
    out.sort(key=lambda n:(n['timeMs'],n['lane']))
    final=[]; busy={}
    for n in out:
        if busy.get(n['lane'],-1)>=n['timeMs']-1: continue
        final.append(n); busy[n['lane']]=n['timeMs']+n['durationMs']
    e=copy.deepcopy(d); e['notes']=final; e['difficulty']['level']=level; e['difficulty']['name']=name
    e['meta']['extra']=extra
    json.dump(e,open(dst,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
    span=(notes[-1]['timeMs']-notes[0]['timeMs'])/1000
    print(f'{len(notes)} -> {len(final)} notes, nps {len(notes)/span:.2f} -> {len(final)/span:.2f}')
if __name__=='__main__':
    build(*sys.argv[1:4],int(sys.argv[4]),sys.argv[5],sys.argv[6])
