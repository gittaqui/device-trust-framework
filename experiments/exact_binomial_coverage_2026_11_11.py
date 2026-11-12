"""Exact binomial interval coverage for equal-length two-point synthetic fixture only."""
import math
import json

def cdf(k,n,p):
    return sum(math.comb(n,j)*p**j*(1-p)**(n-j) for j in range(k+1))

def cp_interval(x,n,alpha=.05):
    if type(x)!=int or type(n)!=int or not 0<=x<=n or n<1 or not 0<alpha<1:
        raise ValueError("invalid count or alpha")
    def root(fn,increasing):
        lo,hi=0.,1.
        for _ in range(65):
            mid=(lo+hi)/2
            if (fn(mid)<alpha/2)==increasing: lo=mid
            else: hi=mid
        return (lo+hi)/2
    lower=0. if x==0 else root(lambda p:1-cdf(x-1,n,p),True)
    upper=1. if x==n else root(lambda p:cdf(x,n,p),False)
    return lower,upper

def exact_coverage(n,p=.3):
    return sum(math.comb(n,x)*p**x*(1-p)**(n-x) for x in range(n+1)
               if cp_interval(x,n)[0]<=p<=cp_interval(x,n)[1])

if __name__=="__main__":
    print(json.dumps({"model":"independent Bernoulli device effects, equal intervals, true p=.3",
      "coverage":[{"n":n,"exact_cp_coverage":exact_coverage(n)} for n in (2,5,20,100)]},indent=2))
