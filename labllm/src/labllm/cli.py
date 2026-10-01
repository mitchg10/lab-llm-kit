"""labllm command line.

  labllm chat [-m MODEL] [--system S]             interactive chat in the terminal
  labllm ask "question" [-m MODEL] [-f FILE]      one question (FILE contents appended)
  labllm batch IN.csv --prompt USER.md [--system SYSTEM.md] --text-col C --out OUT.csv
                                                  run your prompts over every row (resumable)
  labllm scan FILE... [--names F] [--allow F]     check files for identifiers (exit 1 if any)
  labllm models [ollama|lmstudio|cornell]         list models a backend is serving

MODEL is 'name' (Ollama), 'lmstudio:name' or 'cornell:name'. Default: $LAB_DEFAULT_MODEL.

System prompts: `chat` and `ask` are for general chat, so they use the lab's
default chat prompt unless you pass --system "text" / --system file.md, or
--no-system. `batch` (and the Python API) send ONLY the prompts you give.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from .client import DEFAULT, LabLLM
from .scan import IdentifierError, load_terms, read_text_file, scan_text


def _scanner_args(p):
    p.add_argument("--names", help="file of real names to look for (one per line)")
    p.add_argument("--allow", help="file of allowed terms, e.g. pseudonyms (one per line)")
    p.add_argument("--ignore", default="", help="comma-separated finding kinds to skip, e.g. date,netid")


def cmd_scan(a) -> int:
    names, allow = load_terms(a.names), load_terms(a.allow)
    ignore = [k for k in a.ignore.split(",") if k]
    total = 0
    for f in a.files:
        try:
            text = read_text_file(f)
        except (ValueError, OSError) as e:
            print(f"! {e}", file=sys.stderr)
            total += 1
            continue
        hits = scan_text(text, names=names, allow=allow, ignore=ignore, source=f)
        total += len(hits)
        if hits:
            print(f"✗ {f}: {len(hits)} possible identifier(s)")
            for h in hits:
                print(f"   {h}")
        else:
            print(f"✓ {f}: no identifiers found by the automatic check")
    if total:
        print("\nFix these (or confirm they're false positives with --allow/--ignore) before using a model.\n"
              "The automatic check can't see indirect identifiers — read the data yourself too.")
    return 1 if total else 0


def _chat_system(a):
    if a.no_system:
        return None
    return a.system if a.system else DEFAULT


def cmd_ask(a) -> int:
    prompt = a.question
    if a.file:
        prompt += "\n\n---\n" + read_text_file(a.file)
    llm = LabLLM(a.model, system=_chat_system(a), ignore=[k for k in a.ignore.split(",") if k],
                 names_file=a.names, allow=load_terms(a.allow))
    try:
        r = llm.chat(prompt, temperature=a.temperature)
    except IdentifierError as e:
        print(e, file=sys.stderr)
        return 1
    print(r.text)
    print(f"\n[{r.backend}:{r.model} · {r.seconds}s]", file=sys.stderr)
    return 0


def cmd_chat(a) -> int:
    llm = LabLLM(a.model, ignore=[k for k in a.ignore.split(",") if k], names_file=a.names,
                 allow=load_terms(a.allow))
    sys_prompt = _chat_system(a)
    history: list[dict] = []
    label = "lab default chat prompt" if sys_prompt is DEFAULT else ("your system prompt" if sys_prompt else "no system prompt")
    print(f"Chatting with {llm.backend}:{llm.model} ({label}). Empty line or Ctrl-D to quit; /reset clears history.")
    while True:
        try:
            q = input("\nyou › ").strip()
        except EOFError:
            break
        if not q:
            break
        if q == "/reset":
            history.clear()
            print("(history cleared)")
            continue
        try:
            r = llm.chat(messages=history + [{"role": "user", "content": q}], system=sys_prompt,
                         temperature=a.temperature)
        except IdentifierError as e:
            print(e)
            continue
        history += [{"role": "user", "content": q}, {"role": "assistant", "content": r.text}]
        print(f"\n{llm.model} › {r.text}")
    return 0


def cmd_batch(a) -> int:
    template = Path(a.prompt).read_text(encoding="utf-8")
    schema = json.loads(Path(a.schema).read_text()) if a.schema else None
    system = Path(a.system).read_text(encoding="utf-8") if a.system else None
    llm = LabLLM(a.model, system=system, ignore=[k for k in a.ignore.split(",") if k], names_file=a.names,
                 allow=load_terms(a.allow), save_to=a.save_to)
    rows = list(csv.DictReader(open(a.input, newline="", encoding="utf-8-sig")))
    if not rows:
        print("empty input")
        return 1
    if a.text_col not in rows[0]:
        print(f"column '{a.text_col}' not found; columns are: {', '.join(rows[0])}")
        return 1
    id_col = a.id_col if a.id_col in rows[0] else None
    out = Path(a.out)
    done = set()
    if out.exists():
        with open(out, newline="", encoding="utf-8") as f:
            done = {r.get("_row") for r in csv.DictReader(f)}
    fields = list(rows[0]) + ["_row", "_model", "_status", "response"]
    new = not out.exists()
    skipped = errors = 0
    with open(out, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        if new:
            w.writeheader()
        for i, row in enumerate(rows, 1):
            key = row[id_col] if id_col else str(i)
            if key in done:
                continue
            try:
                prompt = template.format(text=row[a.text_col], **{k: v for k, v in row.items() if k != "text"})
            except KeyError as e:
                print(f"prompt template uses {{{e.args[0]}}} but there is no such column")
                return 1
            rec = {**row, "_row": key, "_model": f"{llm.backend}:{llm.model}"}
            try:
                r = llm.chat(prompt, json_schema=schema, temperature=a.temperature)
                rec.update(_status="ok", response=r.text)
            except IdentifierError as e:
                kinds = sorted({x.kind for x in e.findings})
                rec.update(_status="NOT SENT: possible identifiers " + ",".join(kinds), response="")
                skipped += 1
            except Exception as e:  # network/model errors: record and continue
                rec.update(_status=f"error: {type(e).__name__}: {e}"[:300], response="")
                errors += 1
            w.writerow(rec)
            f.flush()
            print(f"  row {key}: {rec['_status']}", file=sys.stderr)
    print(f"Done → {out}  ({skipped} not sent because of identifiers, {errors} errors)")
    return 1 if (skipped or errors) else 0


def cmd_models(a) -> int:
    for m in LabLLM(backend=a.backend).models(a.backend):
        print(m)
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="labllm", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scan", help="check files for identifiers")
    s.add_argument("files", nargs="+")
    _scanner_args(s)
    s.set_defaults(fn=cmd_scan)

    for name, fn, hlp in (("chat", cmd_chat, "interactive chat"), ("ask", cmd_ask, "ask one question")):
        s = sub.add_parser(name, help=hlp)
        if name == "ask":
            s.add_argument("question")
            s.add_argument("-f", "--file")
        s.add_argument("-m", "--model")
        s.add_argument("-s", "--system", help="your system prompt: text or a .md/.txt file")
        s.add_argument("--no-system", action="store_true", help="send no system prompt at all")
        s.add_argument("-t", "--temperature", type=float, default=0.0 if name == "ask" else 0.7)
        _scanner_args(s)
        s.set_defaults(fn=fn)

    s = sub.add_parser("batch", help="run a prompt template over a CSV")
    s.add_argument("input")
    s.add_argument("--prompt", required=True, help="USER prompt template file; use {text} and any {column}")
    s.add_argument("--system", help="SYSTEM prompt file (optional; nothing is added if omitted)")
    s.add_argument("--text-col", required=True)
    s.add_argument("--id-col", default="id")
    s.add_argument("--out", required=True)
    s.add_argument("--schema", help="JSON Schema file for structured output")
    s.add_argument("--save-to", help="JSONL with full prompts/replies for your methods record")
    s.add_argument("-m", "--model")
    s.add_argument("-t", "--temperature", type=float, default=0.0)
    _scanner_args(s)
    s.set_defaults(fn=cmd_batch)

    s = sub.add_parser("models", help="list models a backend serves")
    s.add_argument("backend", nargs="?", default="ollama", choices=["ollama", "lmstudio", "cornell"])
    s.set_defaults(fn=cmd_models)

    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
