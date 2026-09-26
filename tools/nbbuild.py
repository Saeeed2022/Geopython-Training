"""Tiny notebook builder used to write the training notebooks.

Each notebook is described in a small Python file in tools/content/.
Run `python tools/build_all.py` to regenerate notebooks/, and
`python tools/check_solutions.py` to run every solution as a test.
"""
import json
import re
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parent.parent
NB_DIR = ROOT / "notebooks"


def _clean(text):
    return dedent(text).strip("\n")


class NB:
    def __init__(self, name, title):
        self.name = name
        self.cells = []
        self.checks = []          # code the checker runs, in order
        self.md(f"# {title}")

    # --- raw cells --------------------------------------------------------
    def md(self, text):
        self.cells.append({"cell_type": "markdown", "metadata": {}, "source": _clean(text)})

    def code(self, text, run=True):
        """A normal code cell. run=True: the checker runs it too."""
        src = _clean(text)
        self.cells.append({"cell_type": "code", "metadata": {}, "execution_count": None,
                           "outputs": [], "source": src})
        if run:
            self.checks.append(src)

    # --- building blocks ----------------------------------------------------
    def level(self, n, name, goal, daily=None):
        txt = f"---\n## Level {n} — {name}\n\n**Goal of this level:** {goal}"
        if daily:
            txt += f"\n\n**Daily-life picture:** {daily}"
        self.md(txt)

    def ex(self, id, title, command, purpose_a, life_a, hint, starter, solution,
           purpose_q=None, life_q=None, task=None, note=None, qtype=None):
        """One exercise in the fixed 4-step format.

        Step 1 purpose -> Step 2 real life -> Step 3 hint -> Step 4 code.
        """
        purpose_q = purpose_q or f"What is the **purpose** of `{command}`? Say in one sentence what it does."
        life_q = life_q or "Give **one real-life situation** where a planner or analyst would use it."
        head = f"### Exercise {id} — {title}\n\n"
        if qtype:
            head += f"🧭 **Question type:** {qtype}\n\n"
        head += (f"**Step 1 · Purpose.** {purpose_q}\n\n"
                 f"**Step 2 · Real life.** {life_q}\n\n")
        if task:
            head += f"**Step 4 · Your task.** {_clean(task)}\n\n"
        self.md(head + f"<details><summary>💡 <b>Step 3 · Hint</b> (open only after you tried)</summary>\n\n{_clean(hint)}\n\n</details>")
        self.md("✍️ **Your answers** (double-click this cell and write):\n\n"
                "- Purpose: …\n- Real life: …")
        self.code(starter, run=False)
        sol = _clean(solution)
        extra = f"\n\n{_clean(note)}" if note else ""
        self.md(
            "<details><summary>✅ <b>Solution</b> (compare after you answered)</summary>\n\n"
            f"**Purpose:** {_clean(purpose_a)}\n\n**Real life:** {_clean(life_a)}\n\n"
            f"```python\n{sol}\n```{extra}\n\n</details>"
        )
        self.checks.append(sol)

    def pro(self, id, title, qtype, scenario, plan_hint, starter, solution, answer, why=None):
        """Professional exercise: identify the question type, plan, then code."""
        self.md(
            f"### Exercise {id} — {title}\n\n"
            f"**Scenario.** {_clean(scenario)}\n\n"
            "**Step 1 · Question type.** What *kind* of question is this? "
            "(descriptive, measurement, proximity, overlay, statistical, modelling, decision, temporal…)\n\n"
            "**Step 2 · Plan.** Write the commands you need **in order**, in plain words first.\n\n"
            "**Step 3 · Code.** Turn the plan into code below.\n\n"
            f"<details><summary>💡 <b>Hint</b></summary>\n\n{_clean(plan_hint)}\n\n</details>"
        )
        self.md("✍️ **Your answers:**\n\n- Question type: …\n- Plan (steps): 1. … 2. … 3. …\n- Result / interpretation: …")
        self.code(starter, run=False)
        sol = _clean(solution)
        extra = f"\n\n**Why this matters:** {_clean(why)}" if why else ""
        self.md(
            "<details><summary>✅ <b>Solution</b></summary>\n\n"
            f"🧭 **Question type:** {qtype}\n\n{_clean(answer)}\n\n```python\n{sol}\n```{extra}\n\n</details>"
        )
        self.checks.append(sol)

    def test(self, intro, questions):
        """End-of-library test. questions = list of (kind, text, model_answer)."""
        self.md(f"---\n## 🏁 Final test\n\n{_clean(intro)}")
        for i, (kind, text, model) in enumerate(questions, 1):
            label = {"task": "🛠️ Task question", "model": "🧠 Modelling question",
                     "stat": "📊 Statistical question", "decision": "🗺️ Decision question"}.get(kind, kind)
            self.md(f"### Test {i} — {label}\n\n{_clean(text)}")
            self.md("✍️ **Your answer** (plan in words first, then code if the question asks for it):\n\n…")
            self.code("# your code (if needed)", run=False)
            self.md(f"<details><summary>✅ <b>Model answer</b> (open only after you answered)</summary>\n\n{_clean(model)}\n\n</details>")
            for block in re.findall(r"```python\n(.*?)```", _clean(model), flags=re.S):
                self.checks.append(block)

    def reflect(self, text):
        self.md(f"### 🪞 Reflection — your long-term plan\n\n{_clean(text)}\n\n✍️ **Your answer:** …")

    # --- output -------------------------------------------------------------
    def save(self):
        nb = {
            "cells": [dict(c, source=c["source"].splitlines(keepends=True)) for c in self.cells],
            "metadata": {
                "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                "language_info": {"name": "python"},
            },
            "nbformat": 4,
            "nbformat_minor": 5,
        }
        for i, c in enumerate(nb["cells"]):
            c["id"] = f"{self.name[:20]}-{i:03d}".replace("_", "-")
        NB_DIR.mkdir(exist_ok=True)
        path = NB_DIR / f"{self.name}.ipynb"
        path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n")
        return path


SETUP = '''
import sys, warnings
from pathlib import Path
sys.path.insert(0, str(Path.cwd().parent))      # lets the notebook find the `geotrain` helper
warnings.filterwarnings("ignore")
from geotrain import write_riverton, DATA_DIR
if not (DATA_DIR / "riverton.gpkg").exists():   # build the Riverton data the first time
    write_riverton()
GPKG = DATA_DIR / "riverton.gpkg"
print("Data folder:", DATA_DIR)
'''
