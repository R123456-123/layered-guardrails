| config | ASR | leak | tool | hallucination | pii | FPR | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|
| no_guards | 100% | 100% | 100% | 100% | 100% | 0% | 0.0 | 0.1 |
| input_only | 56% | 60% | 45% | 100% | 29% | 11% | 0.3 | 0.5 |
| tools_only | 72% | 100% | 0% | 100% | 100% | 0% | 0.0 | 0.1 |
| output_only | 33% | 0% | 100% | 0% | 29% | 0% | 0.2 | 0.7 |
| full | 5% | 0% | 0% | 0% | 29% | 11% | 0.4 | 1.3 |
| full_minus_input | 5% | 0% | 0% | 0% | 29% | 0% | 0.4 | 2.3 |
| full_minus_tools | 18% | 0% | 45% | 0% | 29% | 11% | 0.6 | 2.9 |
| full_minus_output | 44% | 60% | 0% | 100% | 29% | 11% | 0.3 | 0.6 |

**Marginal contribution** (ASR increase when a layer is removed from `full`):
- input guards: +0 pts
- tool layer: +13 pts
- output guards: +38 pts

**Latency, full pipeline, input guards simulated at 50 ms each (model-backed):**
- serial (short-circuits on block): p50 187 ms, p95 195 ms
- parallel: p50 64 ms, p95 67 ms