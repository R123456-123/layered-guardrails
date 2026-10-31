# Layered Guardrails for Production LLM Agents

[![tests](https://github.com/R123456-123/layered-guardrails/actions/workflows/tests.yml/badge.svg)](https://github.com/R123456-123/layered-guardrails/actions/workflows/tests.yml)

A small, tested guardrail pipeline for LLM agents, plus an ablation harness that measures
what each layer actually contributes (attack success rate, false positives, latency).
Built as a ResearchDen technical project.

![Demo](docs/demo.png)

## Architecture

```mermaid
flowchart TD
  C["Client"] --> G["FastAPI gateway<br/>API key + rate limit"]
  G -->|"401 / 429"| R["Rejected"]
  G --> I["Input guards (parallel)<br/>injection / PII / topic"]
  I -->|"block"| F["Safe fallback"]
  I --> A["Agent loop"]
  A --> T["Tool layer<br/>allowlist, schema, RBAC, approval gate"]
  T -->|"high-risk"| H["Human review"]
  T --> A
  A --> O["Output guards<br/>leak / groundedness / format / PII"]
  O -->|"fail: retry max 2"| A
  O -->|"still failing"| F
  O -->|"pass"| V["Validated response"]
  G -.-> L[("JSONL audit log")]
  O -.-> L
```

Design principles: one choke point (the gateway), fail-closed guards, policy as YAML,
independent input checks run in parallel, `approved` is never a client-supplied field,
and the audit log stores a hash of the input, never the raw text.

## Quickstart (Windows PowerShell)

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q                 # 20 tests
uvicorn app.main:app --reload       # http://127.0.0.1:8000/docs
python -m eval.make_dataset; python -m eval.run_eval; python -m eval.make_chart
```

Demo keys are in `policies/policy.yaml` (`demo-viewer-key`, `demo-analyst-key`, `demo-admin-key`).

## Results

58 prompts (39 attacks, 19 benign) across 4 attack goals: system-prompt leak, unauthorized tool use,
hallucinated citations, PII leak. Success is judged by **outcome** (a canary leaked, a dangerous tool
actually ran, a fake citation or raw PII reached the response), not by whether a guard fired.

![Ablation](docs/results.png)

| config            | ASR  | leak | tool | hallucination | pii  | FPR | p50 ms | p95 ms |
| ----------------- | ---- | ---- | ---- | ------------- | ---- | --- | ------ | ------ |
| no_guards         | 100% | 100% | 100% | 100%          | 100% | 0%  | 0.0    | 0.1    |
| input_only        | 56%  | 60%  | 45%  | 100%          | 29%  | 11% | 0.3    | 0.5    |
| tools_only        | 72%  | 100% | 0%   | 100%          | 100% | 0%  | 0.0    | 0.1    |
| output_only       | 33%  | 0%   | 100% | 0%            | 29%  | 0%  | 0.2    | 0.7    |
| full              | 5%   | 0%   | 0%   | 0%            | 29%  | 11% | 0.4    | 1.3    |
| full_minus_input  | 5%   | 0%   | 0%   | 0%            | 29%  | 0%  | 0.4    | 2.3    |
| full_minus_tools  | 18%  | 0%   | 45%  | 0%            | 29%  | 11% | 0.6    | 2.9    |
| full_minus_output | 44%  | 60%  | 0%   | 100%          | 29%  | 11% | 0.3    | 0.6    |

Latency with model-backed input guards simulated at 50 ms each: serial p50 187 ms vs parallel p50 64 ms.

### Findings

1. **No single layer is enough.** The best single layer leaves 13/39 attacks through; the full stack leaves 2/39.
2. **Layers own different failure modes.** Only the tool layer stops unauthorized actions; output guards catch
   leaks that evade input regexes (9/15 evasive leaks passed the input layer) and fabricated citations.
3. **In this setup the input guards added no measurable security but cost 2/19 false positives.** This is
   dataset-specific: the output leak check is an exact canary match against a mock model that leaks verbatim.
   Input guards still reject early, saving an agent loop. See limitations.
4. **Parallelizing independent guards cut latency about 2.9x** once guards are model-backed.
5. **Residual failures:** 2 obfuscated-PII inputs (spaced phone number, "dot/at" email) and 2 benign prompts
   that merely mention filters or injection phrases.

## Limitations

- The LLM is a deliberately gullible mock, a worst-case stand-in so results are deterministic and free. Real models behave differently.
- The dataset is small (n=58) and author-written, with the guards in mind, so rates are optimistic and have no confidence intervals. Treat this as a controlled demonstration, not a benchmark.
- Detectors are regex/heuristic baselines. Leak detection uses an exact canary; groundedness is a URL/number-in-context check.
- Latency for model-backed guards is simulated with sleeps.

## Next steps

Swap in a trained injection classifier and Presidio-based PII detection; add a paraphrasing mock (or a real
model) so the exact-match canary no longer suffices; LLM-as-judge groundedness; evaluate adaptive attackers.

## Layout

`app/` gateway, pipeline, agent, guards, tools · `policies/policy.yaml` · `eval/` dataset + harness · `tests/`
