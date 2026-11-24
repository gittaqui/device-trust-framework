"""Development-only paired AR(1) FGLS audit; Python standard library."""
import math, random, statistics, csv
from statistics import NormalDist
Z=NormalDist().inv_cdf(.975)
T={10:2.2621571627409915,30:2.045229642132703,100:1.9842169515086827}
def fit(x):
    n=len(x); m=statistics.fmean(x); d=[v-m for v in x]
    den=sum(v*v for v in d[:-1])
    if den<=0: raise ValueError("constant series")
    p=max(-.98,min(.98,sum(a*b for a,b in zip(d[:-1],d[1:]))/den))
    w=math.sqrt(1-p*p)
    a=[w]+[1-p]*(n-1)
    y=[w*x[0]]+[x[i]-p*x[i-1] for i in range(1,n)]
    q=sum(v*v for v in a)
    mu=sum(u*v for u,v in zip(a,y))/q
    s2=sum((v-u*mu)**2 for u,v in zip(a,y))/(n-1)
    if not math.isfinite(s2) or s2<=0: raise ValueError("invalid variance")
    return mu,math.sqrt(s2/q)
def run(trials=2000,seed=20261123):
    rows=[]
    for n in T:
        for p in (0.,.3,.6,.9,-.3,.95):
            rng=random.Random(f"{seed}:{n}:{p}")
            hits=[0,0,0]; diff=[]; widths=[]; failures=0
            oracle=Z/math.sqrt((1-p*p+(n-1)*(1-p)**2)/(1-p*p))
            for _ in range(trials):
                x=[rng.gauss(0,1)]
                for i in range(1,n): x.append(p*x[-1]+math.sqrt(1-p*p)*rng.gauss(0,1))
                m=statistics.fmean(x)
                t=int(abs(m)<=T[n]*statistics.stdev(x)/math.sqrt(n))
                o=int(abs((x[0]+x[-1]+(1-p)*sum(x[1:-1]))/(2+(n-2)*(1-p)))<=oracle)
                try:
                    mu,se=fit(x); h=int(abs(mu)<=Z*se); widths.append(2*Z*se)
                except ValueError:
                    failures+=1; h=0
                hits=[a+b for a,b in zip(hits,(t,h,o))]
                diff.append(h-t)
            rows.append((n,p,*(v/trials for v in hits),statistics.fmean(diff),statistics.stdev(diff)/math.sqrt(trials),statistics.median(widths),failures))
    return rows
if __name__=="__main__":
    import sys
    w=csv.writer(sys.stdout);w.writerow(("n","phi","t","fgls","oracle","paired_difference","paired_se","median_fgls_width","failures"));w.writerows(run())
