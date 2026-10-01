---
name: lab-data-privacy
description: Check research data for identifiers before any model sees it, and apply the lab's human-subjects rules. Use whenever a task involves interview transcripts, survey responses, student work, course or LMS exports, field notes, or any file that might describe real people. Also use when a user asks whether data is safe to analyze, or asks about de-identification or the lab constitution.
---

# Lab data privacy check

The lab rule is **no identifiable information about people in any model, anywhere**. The full text is in `$LAB_CONSTITUTION`. This skill is the procedure for applying that rule.

## Before you open or analyze a data file

1. **Scan it without reading it into the conversation.**
   ```bash
   lab-scan path/to/file.txt                  # .txt .md .csv .json .vtt .srt .docx
   lab-scan data/*.csv --allow pseudonyms.txt # a file of pseudonyms the user confirms are fine
   lab-scan notes.md --ignore date            # skip a finding kind the user confirms is a false positive
   ```
   Exit code 0 means nothing was found. Exit code 1 means there are findings. The output masks what it found, so relaying it is safe.
2. **If it reports findings,** stop. Don't read or summarize the file. Tell the user the file name, line numbers and finding kinds. Ask them to de-identify the data at the source (see below) and re-scan. Only accept a false-positive override (`--allow` or `--ignore`) when the user explicitly confirms it.
3. **If the scan is clean,** you still need to look for **indirect identifiers** as you read. The scanner can't detect them. Examples:
   - Course, section and semester combined with a demographic
   - "the only …" or "the one … in our program"
   - Distinctive employers, awards or life events
   - Quotes someone could find with a search engine

   If you see any, stop and point them out without repeating them.

## What to tell the user about de-identification

De-identification happens **before** the data comes to this machine. It is done by a person or with the protocol's approved tooling, never with a language model.

- Replace names with stable pseudonyms such as `P01` and `Instructor_B`. Keep the linking key **off** this machine.
- Generalize details:
  - an exact date becomes a month or term
  - a specific course becomes something like "a sophomore ME course"
  - a hometown becomes a region
  - a rare role becomes a broader category
- Remove email addresses, IDs and URLs entirely rather than masking them.
- For small groups, merge demographic categories or drop them.
- Raw audio and video are identifiable. Transcription and de-identification happen under the protocol, not here.

## Things you never do

- Put raw or partially de-identified data into a prompt "just to check" it.
- Write identifiers into files, logs, code, commit messages or memory, even while fixing them.
- Try to work out who a participant is, or infer demographics that the data doesn't state.
- Send data to any service other than local Ollama or LM Studio, or the Cornell AI Gateway.

## If identifiable data already went somewhere

Follow constitution §8. Stop and tell the user to inform the PI the same day. Don't quietly delete anything: cleanup happens under the PI's direction so there is a record of it.

## Git and GitHub

Project repos ignore `data/` and `outputs/`, and a pre-commit hook runs the same scan on everything being committed. It also blocks data files and recordings. GitHub is an external service: only code, prompts, codebooks and documentation go there. See `research-version-control` for what to do when the hook blocks a commit.

## Scripting it

In Python, `labllm` runs the same scan on every call and raises `IdentifierError` before anything is sent:
```python
from labllm import scan_text, read_text_file
findings = scan_text(read_text_file("t.txt"), allow=["P01", "P02"])
```
