"""Exact coverage of ideal (infinite-replicate) percentile bootstrap for Bernoulli devices.

Restricted synthetic mathematical benchmark; NOT device-trust validation.
"""
import json
import math

def binomial_cdf(k, n, p):
    if not (isinstance(n, int) and n >= 1 and isinstance(k, int) and 0 <= p <= 1):
        raise ValueError("invalid binomial arguments")
    if k < 0: return 0.0
    if k >= n: return 1.0
    return sum(math.comb(n,j)*p**j*(1-p)**(n-j) for j in range(k+1))

def discrete_quantile(n,p,q):
    """Left inverse CDF."""
    if not 0 < q < 1: raise ValueError("invalid quantile")
    for j in range(n+1):
        if binomial_cdf(j,n,p) >= q-1e-14: return j
    raise AssertionError("unreachable")

def ideal_percentile_interval(x,n,alpha=.05):
    if not (isinstance(x,int) and isinstance(n,int) and n>=1 and 0<=x<=n and 0<alpha<1):
        raise ValueError("invalid count or alpha")
    p=x/n
    return discrete_quantile(n,p,alpha/2)/n,discrete_quantile(n,p,1-alpha/2)/n

def exact_coverage(n,p=.3,alpha=.05):
    if not (isinstance(n,int) and n>=1 and 0<p<1 and 0<alpha<1):
        raise ValueError("invalid design")
    return sum(math.comb(n,x)*p**x*(1-p)**(n-x) for x in range(n+1)
               if ideal_percentile_interval(x,n,alpha)[0]<=p<=ideal_percentile_interval(x,n,alpha)[1])

if __name__=="__main__":
    print(json.dumps({"design":"Independent Bernoulli device effects, equal lengths, p=.3, infinite bootstrap replicates",
      "results":[{"n":n,"exact_ideal_percentile_coverage":exact_coverage(n)} for n in (2,5,20,100)]},indent=2))
