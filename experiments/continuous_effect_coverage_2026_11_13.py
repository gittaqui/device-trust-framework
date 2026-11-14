"""Synthetic continuous paired-effect CI coverage; independent device clusters only."""
import json
import math
import random

def quantile(values, p):
    v = sorted(values)
    h = (len(v)-1)*p
    i = int(h)
    return v[i]*(1-(h-i))+v[min(i+1,len(v)-1)]*(h-i)

def weighted_mean(effects, weights):
    return sum(x*w for x,w in zip(effects,weights))/sum(weights)

def intervals(effects, weights, rng, b=399):
    n=len(effects)
    if n<2 or len(weights)!=n or any(w<=0 for w in weights) or b<20:
        raise ValueError('invalid design')
    estimate=weighted_mean(effects,weights)
    draws=[]
    for _ in range(b):
        idx=[rng.randrange(n) for _ in range(n)]
        draws.append(weighted_mean([effects[i] for i in idx],[weights[i] for i in idx]))
    percentile=(quantile(draws,.025),quantile(draws,.975))
    tcrit={5:2.776445,20:2.093024,100:1.984217}[n]
    residual=[w*(x-estimate) for x,w in zip(effects,weights)]
    se=math.sqrt(n/(n-1)*sum(z*z for z in residual))/sum(weights)
    return percentile,(estimate-tcrit*se,estimate+tcrit*se)

def run(seed=20261113, datasets=300, b=399):
    rng=random.Random(seed)
    results=[]
    for n in (5,20,100):
        for variable in (False,True):
            hits=[0,0]
            for _ in range(datasets):
                effects=[.4*(2*rng.random()-1) for _ in range(n)]
                weights=[rng.choice((10,20,50,100)) if variable else 50 for _ in range(n)]
                cis=intervals(effects,weights,rng,b)
                for j,(lo,hi) in enumerate(cis):
                    hits[j]+=lo<=0<=hi
            results.append(dict(n=n,variable_lengths=variable,datasets=datasets,bootstrap_replicates=b,
                                percentile_coverage=hits[0]/datasets,t_linearized_coverage=hits[1]/datasets,
                                monte_carlo_se_upper_bound=math.sqrt(.25/datasets)))
    return results

if __name__=='__main__':
    print(json.dumps({'synthetic_only':True,'results':run()},indent=2))
