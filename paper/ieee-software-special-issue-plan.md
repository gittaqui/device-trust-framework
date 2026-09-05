# IEEE Software Special-Issue Submission Plan

**Status:** Proposed publication target; not submitted, accepted, or peer reviewed.

## Target venue

**IEEE Software — Special Issue: Building Trustworthy Software in the Time of AI**

- Submission deadline: **5 November 2026**
- Expected publication: **July/August 2027**
- CFP: https://www.computer.org/digital-library/magazines/so/cfp-building-trustworthy-software-ai
- General IEEE Software author guidance: https://www.computer.org/digital-library/magazines/so/cfp-ieee-software
- Submission system: https://ieee.atyponrex.com/journal/sw-cs
- Submission fee: the CFP does **not state a submission fee**. IEEE Software is a hybrid publication; any optional open-access publication charge should be verified from the current IEEE pricing policy before submission/acceptance.

## Why this venue fits

The special issue explicitly seeks practical, evidence-based methods for trustworthy AI-enabled software, including:

- monitoring and governance of AI systems;
- transparency and explainability;
- human oversight and fail-safe mechanisms;
- security and privacy controls;
- LLMs/agents used for monitoring, compliance, and governance;
- real-world case studies and repeatable practices.

The Device Trust Framework can fit if the article is positioned as a **trustworthy decision-support pattern for AI-assisted endpoint operations**, not as a claim that a weighted trust score is novel by itself.

## Proposed article title

**Trustworthy AI-Assisted Endpoint Decisions: Designing Explainable Device-Trust Controls for Enterprise Operations**

Alternative:

**Beyond Binary Compliance: Practical Guardrails for AI-Assisted Enterprise Device Trust**

## Draft abstract (IEEE Software style, <=150 words)

Enterprise endpoint platforms increasingly combine compliance, identity, security, freshness, and behavioral telemetry to guide access and remediation decisions. AI-assisted operations can make these decisions faster, but missing evidence, opaque aggregation, and overconfident automation can create new failure modes. This article presents an explainable device-trust pattern for enterprise operations that separates weighted evidence from non-compensatory safety gates and explicitly represents uncertainty through step-up decisions. We evaluate the design using reproducible synthetic endpoint scenarios, including compliant-but-compromised devices and structured telemetry outages, and define a validation path using independently sourced enterprise telemetry. The results are used to illustrate practical design trade-offs among false allows, false denials, user friction, explainability, and missing-signal behavior. We provide implementation guidance for engineers building AI-assisted endpoint, identity, and access-control workflows without treating model output as an unquestioned authorization decision.

## Three practitioner insights

1. **Do not let missing telemetry silently increase trust.** Renormalizing only the signals that remain can remove adverse evidence from the denominator and produce overconfident decisions.
2. **Use non-compensatory safety gates for catastrophic signals.** Severe threat evidence or absent critical protections should not be averaged away by otherwise healthy posture indicators.
3. **Treat uncertainty as an explicit operating state.** `STEP_UP`, defer, or human review can be safer than forcing uncertain sessions into a binary allow/deny decision.

## Article structure

1. **The operational problem**
   - Why binary compliance is useful but incomplete.
   - Why AI-assisted endpoint operations increase both opportunity and risk.

2. **Trustworthy-decision design principles**
   - Transparent signals.
   - Directionally consistent scoring.
   - Non-compensatory safety gates.
   - Explicit uncertainty/abstention.
   - Auditable explanations.

3. **Reference implementation**
   - Eight normalized trust dimensions.
   - Weighted evidence layer.
   - Safety gates.
   - ALLOW / STEP_UP / DENY policy bands.

4. **Failure-mode experiments**
   - Healthy and degraded endpoints.
   - Compliant-but-compromised endpoints.
   - Missing telemetry.
   - Structured outages.
   - Threshold sensitivity.

5. **What the current results do and do not prove**
   - Synthetic evidence is useful for logic/failure-mode validation.
   - It does not establish production security effectiveness.

6. **External validation path**
   - LANL enterprise authentication/process telemetry.
   - Controlled non-production endpoint lab.
   - Mapping limitations between public telemetry and commercial endpoint-management signals.

7. **Engineering recommendations**
   - Operational guardrails.
   - Logging and explainability.
   - Human escalation.
   - Monitoring model drift and missing-data behavior.

## Evidence required before submission

The current repository is not yet strong enough to submit. Before November 5, 2026, complete at minimum:

- threshold and minimum-coverage sensitivity analysis;
- per-scenario confusion/error analysis;
- at least one alternative non-trivial baseline beyond binary compliance;
- externally sourced telemetry experiment (preferably LANL) or a clearly justified reason why external validation is not possible;
- explicit treatment of missing-data uncertainty;
- reproducible tables/figures generated from committed code;
- stronger related-work comparison showing the article's practical contribution;
- threats-to-validity section separating synthetic, testbed, and enterprise evidence;
- manual review of all references and bibliographic metadata.

## EB-1A relevance

If peer reviewed and accepted, this could support **authorship of scholarly articles**. It may also become supporting evidence for **original contributions** only if independent evidence later demonstrates significance, such as citations, adoption, invited discussion, use by other engineers/researchers, or independent expert testimony tied to concrete impact.

Submission alone, GitHub publication, or self-described novelty should not be treated as evidence of major significance.
