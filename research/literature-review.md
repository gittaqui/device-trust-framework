# Literature Review — Day 1

_Last reviewed: 2026-09-03_

## 1. Zero Trust establishes the architectural need for device-aware decisions

NIST SP 800-207 defines Zero Trust Architecture around explicit authentication and
authorization of both subjects and devices rather than implicit trust based on
network location. NIST's implementation guidance further describes a policy engine
that can calculate trust scores or confidence levels using information supplied by
identity, endpoint-security, analytics, and other components.

**Implication for this project:** device posture should be treated as an input to a
broader access decision rather than a single binary property.

Sources:
- NIST SP 800-207, *Zero Trust Architecture*.
  https://doi.org/10.6028/NIST.SP.800-207
- NIST NCCoE, *Implementing a Zero Trust Architecture*.
  https://pages.nist.gov/zero-trust-architecture/

## 2. Prior work supports dynamic and context-aware trust evaluation

Syed et al. surveyed Zero Trust research and identified authentication, access
control, trust/risk computation, micro-segmentation, and automation as important
technical areas and open research challenges.

Bhattarai et al. proposed trust-score-based Zero Trust access for advanced metering
infrastructure, using multiple attributes and policy thresholds rather than a single
binary decision.

Albomi, Jahan, and Gamble proposed risk-adaptive access control for service meshes,
where runtime trust evaluation can influence dynamically adapted access policies.

**Implication:** multidimensional and adaptive trust is established research territory,
so novelty cannot simply be “use a trust score.” The contribution must be narrower
and empirically defensible.

## 3. Recent literature identifies unresolved trust-scoring limitations

A 2026 systematic literature review of 33 peer-reviewed trust-scoring studies reports
persistent problems with standardization, scalability, validation, parameter
subjectivity, explainability, and adversarial testing. It also reports that much of
the literature relies on simulation and that relatively few studies test large-scale
or adversarial conditions.

**Implication:** a useful contribution is a reproducible, explainable model evaluated
under explicit endpoint scenarios, missing-signal conditions, adversarial cases, and
large populations.

## 4. Continuous verification is broader than login-time authentication

ACM Computing Surveys literature on continuous authentication shows a longstanding
research direction in maintaining confidence after initial authentication rather
than treating authentication as a one-time event.

**Implication:** future iterations of this project can evolve from point-in-time
device trust toward longitudinal trust decay and continuous reevaluation.

## 5. Day-1 synthesis

The literature does **not** justify claiming that enterprise endpoint trust scoring
is unsolved. It does support a narrower gap:

> Existing Zero Trust trust-scoring approaches are diverse and often domain-specific,
> while recent reviews still identify weak standardization, explainability,
> adversarial validation, and scale testing. A reproducible enterprise-endpoint study
> that compares binary compliance against an explainable multidimensional model under
> controlled scenarios can therefore be a useful empirical contribution.

## Core references

1. S. Rose, O. Borchert, S. Mitchell, and S. Connelly, “Zero Trust Architecture,”
   NIST SP 800-207, 2020. DOI: 10.6028/NIST.SP.800-207.
2. N. F. Syed, S. W. Shah, A. Shaghaghi, A. Anwar, Z. A. Baig, and R. Doss,
   “Zero Trust Architecture (ZTA): A Comprehensive Survey,” IEEE Access, vol. 10,
   pp. 57143–57179, 2022. DOI: 10.1109/ACCESS.2022.3174679.
3. H. Bhattarai, A. Kulkarni, and M. Niamat, “Trust Score-Based Zero Trust
   Architecture for Advanced Metering Infrastructure Security,” NAECON 2024,
   pp. 334–339. DOI: 10.1109/NAECON61878.2024.10670642.
4. R. Albomi, S. Jahan, and R. F. Gamble, “A Risk Adaptive Access Control Model for
   the Service Mesh Architecture,” IEEE ICMI 2024.
   DOI: 10.1109/ICMI60790.2024.10585800.
5. F. A. Ruambo et al., “Trust scoring algorithms for zero trust-based
   software-defined perimeter architectures: A systematic literature review of
   advancements, challenges, and future directions,” Computers & Electrical
   Engineering, vol. 132, 111002, 2026.
   DOI: 10.1016/j.compeleceng.2026.111002.
6. L. González-Manzano, J. M. de Fuentes, and A. Ribagorda, “Leveraging
   User-related Internet of Things for Continuous Authentication: A Survey,”
   ACM Computing Surveys, vol. 52, no. 3, 2019.
   DOI: 10.1145/3314023.

## Literature-review next steps

- Expand to 30–50 peer-reviewed sources.
- Separate work by domain: enterprise, cloud, IoT, service mesh, mobile, and campus.
- Extract each paper's trust signals, weighting method, threshold method, evaluation
  population, adversarial scenarios, explainability, and scalability.
- Search specifically for enterprise endpoint posture, risk-adaptive access control,
  trust decay, missing telemetry, and sensitivity analysis.
