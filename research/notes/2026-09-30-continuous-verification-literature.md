# Research log — continuous-verification literature audit

Date: 2026-09-30

## Work completed

Inspected the current repository before making changes. The project already contains a frozen external-validation protocol, synthetic policy comparisons, statistical tests, LANL adapters, and an IEEE manuscript draft. This step therefore narrows the novelty boundary instead of introducing another trust-scoring mechanism.

Fresh literature research verified two peer-reviewed IEEE records and their DOI metadata:

1. Han Zhang, Qian Wang, Xiaoli Zhang, Yi He, Bo Tang, and Qi Li, “Toward Zero-Trust IoT Networks via Per-Packet Authorization,” IEEE Communications Magazine, vol. 62, no. 12, pp. 90–96, 2024. DOI: 10.1109/MCOM.001.2300390.
2. Biao Zhang, Shuo Yang, Xinran Zheng, and Xingjun Wang, “STCA: Stacked Token-based Continuous Authentication Protocol for Zero Trust IoT,” IEEE WCNC 2024, pp. 1–6. DOI: 10.1109/WCNC57260.2024.10571244.

IEEE Xplore metadata was used to verify publication venue, year, and DOI. Author lists were cross-checked against DBLP.

## Synthesis and novelty consequence

OUTSIDE demonstrates that fine-grained zero-trust authorization can be continuously enforced at packet granularity using application capabilities, with a Raspberry Pi/ESP32 prototype. STCA demonstrates protocol-level continuous authentication across a session using stacked tokens and evaluates security/performance in an IoT setting.

These papers strengthen an important boundary for the provisional manuscript “Beyond Binary Compliance: An Explainable Multidimensional Device Trust Framework for Enterprise Access Decisions”: **continuous verification itself is not novel**. The defensible contribution must remain the empirical study of explainable enterprise-endpoint decision structure—especially missing evidence, abstention/STEP_UP, non-compensatory safety constraints, adversarially compliant endpoints, sensitivity, and leakage-controlled external validation—rather than a claim to have invented continuous device trust.

The papers also reinforce why the manuscript should not equate authentication continuity with endpoint-posture validity. Both verified comparators operate primarily at authentication/authorization protocol layers and do not supply independent evidence for the full eight-signal enterprise endpoint model.

## Evidence classification

No new performance result was generated in this step. No synthetic result is reclassified as real-world evidence. No confidential employer data was used.

## Limitations

This audit adds two strong continuous-verification comparators but is not a systematic review update. IoT protocol results do not establish enterprise endpoint effectiveness. The repository still requires externally sourced telemetry results before making effectiveness claims beyond synthetic mechanism analysis.

## Next step

Run the frozen LANL external-validation path on an auditable bounded slice, preserving source provenance/checksum and temporal ordering. Report only the Level-1 descriptive outputs allowed by experiments/external-validation-freeze.md unless independent labels are available.
