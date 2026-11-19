"""Synthetic AR(1) episode-mean HAC coverage audit; no endpoint data."""
import csv, math, random, statistics
Z=1.959963984540054
def ar1(n,phi,rng):
    if n<3 or abs(phi)>=1: raise ValueError("invalid n or phi")
    x=rng.gauss(0,1); out=[x]
    for _ in range(n-1):
        x=phi*x+math.sqrt(1-phi*phi)*rng.gauss(0,1);out.append(x)
    return out
def cover(x,lag):
    n=len(x)
    if not 0<=lag<n: raise ValueError("invalid lag")
    m=statistics.fmean(x);d=[v-m for v in x]
    iid=sum(v*v for v in d)/(n*(n-1))
    lrv=sum(v*v for v in d)/n
    for k in range(1,lag+1):
        lrv+=2*(1-k/(lag+1))*sum(d[t]*d[t-k] for t in range(k,n))/n
    return int(abs(m)<=Z*math.sqrt(max(0,iid))),int(lrv>0 and abs(m)<=Z*math.sqrt(lrv/n)),int(lrv>0)
def run(trials=2000,seed=20261118):
    rows=[]
    for n in (10,30,100):
        for phi in (0.,.3,.6,.9):
            for lag in (0,3,8):
                rng=random.Random(f"{seed}:{n}:{phi}")
                counts=[0,0,0]
                for _ in range(trials):
                    flags=cover(ar1(n,phi,rng),lag)
                    counts=[a+b for a,b in zip(counts,flags)]
                rows.append((n,phi,lag,trials,*(c/trials for c in counts)))
    return rows
if __name__=="__main__":
    rows=run()
    with open("episode_hac_coverage_2026_11_18.csv","w",newline="") as f:
        w=csv.writer(f);w.writerow(("episodes","phi","lag","trials","iid_coverage","hac_coverage","hac_positive_variance"));w.writerows(rows)
    print(*rows,sep="\n")
