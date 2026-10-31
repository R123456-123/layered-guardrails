import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

d = json.loads(Path("eval/results/results.json").read_text(encoding="utf-8"))
rows = d["rows"]
names = list(rows)
att, bn = rows["full"]["att"], rows["full"]["bn"]
asr = [100 * r["succ"] / r["att"] for r in rows.values()]
fpr = [100 * r["fp"] / r["bn"] for r in rows.values()]

fig, ax = plt.subplots(figsize=(10, 4.5))
x, w = list(range(len(names))), 0.4
ax.bar([i - w / 2 for i in x], asr, w, label="Attack success rate (lower is better)")
ax.bar([i + w / 2 for i in x], fpr, w, label="False-positive rate (lower is better)")
for i, v in enumerate(asr):
    ax.text(i - w / 2, v + 1, f"{v:.0f}", ha="center", fontsize=8)
ax.set_xticks(x)
ax.set_xticklabels(names, rotation=30, ha="right")
ax.set_ylabel("%")
ax.set_ylim(0, 110)
ax.set_title(f"Guardrail ablation ({att} attacks, {bn} benign prompts)")
ax.legend()
fig.tight_layout()
Path("docs").mkdir(exist_ok=True)
fig.savefig("docs/results.png", dpi=160)
print("saved docs/results.png")