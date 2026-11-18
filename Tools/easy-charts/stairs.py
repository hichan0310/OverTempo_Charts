import json,sys
for p in sys.argv[1:]:
    d=json.load(open(p)); ev={}
    for n in d['notes']: ev.setdefault(n['timeMs'],[]).append(n['lane'])
    seq=[ls[0] if len(ls)==1 else None for t0,ls in sorted(ev.items())]
    cnt=0
    for i in range(len(seq)-3):
        w=seq[i:i+4]
        if None in w: continue
        dd=[w[j+1]-w[j] for j in range(3)]
        if all(x==1 for x in dd) or all(x==-1 for x in dd): cnt+=1
    print(p.split('/')[-1][:40],'4-note stairs:',cnt)
