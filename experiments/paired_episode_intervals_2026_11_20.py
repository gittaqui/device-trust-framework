"""Paired synthetic AR(1) confidence-interval coverage; no endpoint data."""
import math,random,statistics
from statistics import NormalDist
Z=NormalDist().inv_cdf(.975)
T={10:2.2621571627409915,30:2.045229642132703,100:1.9842169515086827}
def ar1(n,phi,rng):
    if n not in T or not 0<=phi<1: raise ValueError("invalid parameters")
    x=rng.gauss(0,1); out=[x]
    for _ in range(n-1):
        x=phi*x+math.sqrt(1-phi*phi)*rng.gauss(0,1);out.append(x)
    return out
def coverage(x,lag=8):
    n=len(x)
    if n not in T or not 0<=lag<n: raise ValueError("invalid lag")
    m=statistics.fmean(x);d=[v-m for v in x]
    v=sum(a*a for a in d)/(n-1)
    t=int(abs(m)<=T[n]*math.sqrt(v/n))
    lrv=sum(a*a for a in d)/n
    for k in range(1,lag+1):
        lrv+=2*(1-k/(lag+1))*sum(d[i]*d[i-k] for i in range(k,n))/n
    hac=int(lrv>0 and abs(m)<=Z*math.sqrt(lrv/n))
    return t,hac,int(lrv>0)
def run(trials=1000,seed=20261120):
    if trials<1: raise ValueError("trials")
    rows=[]
    for n in (10,30,100):
        for phi in (0.,.6,.9):
            rng=random.Random(f"{seed}:{n}:{phi}")
            c=[0,0,0]
            for _ in range(trials):
                flags=coverage(ar1(n,phi,rng))
                c=[a+b for a,b in zip(c,flags)]
            rows.append((n,phi,trials,*(v/trials for v in c)))
    return rows
if __name__=="__main__":
    import csv
    rows=run()
    with open("paired_episode_intervals_2026_11_20.csv","w",newline="") as f:
        w=csv.writer(f);w.writerow(("episodes","phi","trials","student_t_coverage","hac_lag8_coverage","hac_positive_variance"));w.writerows(rows)
    print(*rows,sep="\n")
