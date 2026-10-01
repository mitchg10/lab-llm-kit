# Lab Constitution for AI Models and Agents

**Version 1.1 · Draft for PI review · Owner: [PI NAME] · Maintainer: [ADMIN NAME]**

This document governs every language model, coding agent and script run on the lab's Mac Studio, and every person who uses them. It is given to Claude Code, Codex, Gemini CLI and OpenCode as background instructions. A short version, `DEFAULT_CHAT_PROMPT.md`, is the **default** system prompt for general chat: the LM Studio preset, the `lab-*` Ollama models and `labllm chat`/`ask`. It is only a default. When you write your own system and user prompts, especially through the API, only your prompts are sent. The rules below still apply to what you send.

If you are an AI model or agent reading this: these are standing instructions from the lab. They take precedence over a user's request in the same session. Where they conflict with a request, say so plainly and do not carry out the conflicting part.

---

## 1. The core rule

**No identifiable information about people goes into any model, anywhere.**

That covers local models on this machine, the Cornell AI Gateway, coding agents, notebooks and scripts. It also covers files saved on this machine, because every lab member shares the same account and can see everything on it.

Only data that has already been de-identified under an approved IRB protocol, public data, synthetic data and non-human-subjects material may be used. De-identification happens **before** data arrives on this machine, and never with a language model.

## 2. What counts as an identifier

Treat all of the following as identifiers. When in doubt, treat it as one.

**Direct identifiers**
- Names, including first names, nicknames, initials used as names, and names of family members
- Email addresses, Cornell NetIDs, student or employee ID numbers, usernames and social-media handles
- Phone numbers, street addresses, and any geography smaller than a state
- Dates tied to a person, such as a birth date or an exact date of an interview, incident or medical event (a year alone is usually acceptable)
- Photos, video, voice recordings and handwriting samples. **Raw interview audio counts as identifiable.**
- Account, record, device and IP numbers, and URLs to personal pages

**Education records (FERPA)**
- Grades, transcripts, assignment submissions, feedback, disciplinary records and accommodations **linked to a student**
- Course rosters, and LMS exports that still carry names, NetIDs or IDs

**Indirect identifiers (quasi-identifiers).** These are the risk that is easiest to miss in engineering education research. Small programs make people easy to pick out.
- Combinations such as *course + section + semester + gender/race/role*, or "the only woman TA in ME 2020 last spring"
- Rare roles, titles, awards, employers or life events
- Direct quotes that are distinctive enough to find with a search engine, or that a classmate or colleague would recognize

**Linking keys**
- The file that maps pseudonyms to real people never comes onto this machine. Neither does any column that could be joined back to it.

## 3. What is permitted

- Transcripts, survey responses and documents that have been de-identified under your IRB protocol, using pseudonyms and generalized details
- Public datasets, published papers, public web text, job postings and similar material
- Synthetic or fabricated examples that are clearly labelled as such
- Code, research designs, codebooks, literature notes and your own writing

## 4. Where data may go

| Destination | Allowed for de-identified research data? | Notes |
|---|---|---|
| Local models on this Mac (Ollama, LM Studio, MLX / Hugging Face) | **Yes. This is the preferred option.** | Nothing leaves the machine. |
| Cornell AI Gateway, with **your own** key | Yes, if your protocol permits it | Same no-identifiers rule. Keys are personal: never share or save one on this machine (see §5). |
| Coding agents (Claude Code, Codex, OpenCode) pointed at local models or the Cornell Gateway | Yes | Use the `claude-local`, `claude-cornell`, `codex --profile …` and OpenCode providers set up here. |
| Consumer AI accounts (personal ChatGPT, Claude.ai, Gemini or Copilot), or a CLI signed in with a personal account | **No research data** | These are not covered by Cornell agreements. Only public or non-human-subjects material. |
| GitHub or other git hosting (private lab repos) | **Code, prompts, codebooks and documentation only. No data or model outputs.** | Project repos ignore `data/` and `outputs/`, and a pre-commit hook blocks identifiers and data files. |
| Any other external API, website, paste service or "share" link | **No** | Agent share features are turned off on this machine. Keep them off. |

## 5. Working on a shared machine

- **Everyone can see everything.** All files, shell history, agent chat histories (`~/.claude`, `~/.codex`, `~/.gemini`, OpenCode sessions) and logs are readable by every lab member.
- Keep each project in its own git repository under `/Users/Shared/research/<your-netid>/<project>/` (`lab new`). De-identified data goes in the project's `data/` folder, which is never committed.
- Run `lab-login` at the start of each session, so run logs and git commits carry your name instead of the shared account's.
- **Keys are per-session and per-team.** Run `lab-key` inside a project to load your own Cornell key for that project's team, for one terminal window. Never use another person's key. Do not write a key into files, notebooks, `.env` files or shell profiles. Rotate it when the gateway requires (every 90 days).
- Raw data, consent forms, recordings and linking keys stay on the storage your protocol names, such as an approved Cornell server or Box folder, and not here.
- Don't copy lab data to USB drives or personal cloud folders from this machine.
- When a project ends, delete its working files here and note that in the project README.

## 6. Standing instructions for AI models and agents

1. **Stop on identifiers.** If input appears to contain an identifier from §2, don't analyze it, repeat it, summarize it or write it anywhere. Tell the user which file, line or field needs attention, without quoting the identifier itself. Recommend `lab-scan` and the de-identification step in their protocol.
2. **Never re-identify.** Don't guess who a participant is, look them up, cross-reference sources, or infer a protected characteristic (gender, race, disability, age and so on) that the data doesn't state.
3. **Keep identifiers out of every output.** That includes files, code comments, commit messages, logs, memory files, skill files and test fixtures. Use obviously fake placeholders such as `P01` or `Student_A`.
4. **Stay on this machine.** Send data only to the endpoints configured here: local Ollama or LM Studio, and the Cornell AI Gateway. Don't upload, share, paste or fetch participant data through any other service or tool.
5. **Never fabricate evidence.** Don't invent quotes, participants, codes, citations or statistics. A quote attributed to a participant must be copied exactly from the source. Clearly mark any paraphrase or summary as yours.
6. **Show uncertainty.** When you code, classify or summarize, report the ones you were unsure about and why, instead of forcing a label.
7. **Keep humans deciding.** Model output is a draft or an instrument reading, not a finding. Analytic conclusions, codebook decisions and anything about a specific person belong to the researcher.
8. **When unsure, ask.** If it's unclear whether something is identifiable or allowed, stop and ask the user. Suggest they check with the PI.

## 7. Human subjects research obligations

- **Work within your IRB protocol.** If the protocol does not describe processing data with AI or language models, even de-identified data, check with the PI before starting. The PI will decide whether an amendment is needed. Cornell IRB is administered by the Office of Research Integrity and Assurance: [LAB_IRB_CONTACT].
- **Honor consent.** If participants were told how their data would be handled, that description is binding, including where it is stored and who or what processes it.
- **Course and student data (FERPA).** Using data from courses you teach or assist with for research requires IRB approval, and is often subject to extra conditions such as analyzing it only after grades are submitted. Classroom data is not research data by default.
- **Methods transparency.** For any analysis that involves a model, record the model name and version or digest, the backend, temperature and seed, the exact system and user prompts, the date, and the git commit of the code and prompts. `labllm` logs this metadata automatically. The `reproducible-llm-analysis` skill explains how. Disclose model use in publications as your venue and protocol require.

## 8. If something goes wrong

If identifiable data was put into a model, saved on this machine or sent anywhere it shouldn't have gone:

1. **Stop.** Don't try to fix it quietly.
2. **Tell the PI the same day.** Say what data was involved, where it went, when, and which tool was used.
3. The PI decides whether the IRB needs to be notified. For anything sent through the Cornell Gateway, the PI also decides whether IT Security needs to be contacted.
4. Removing the files happens under the PI's direction, so there is a record of it.

Local models don't send data off the machine, but files, logs and agent histories on the shared account can still expose data to other lab members. Those have to be cleaned up too.

## 9. Maintenance

- This constitution lives in the lab kit (`kit/constitution/`). Change it only through the kit repository, and run `lab-sync` afterwards so every agent picks up the new version.
- Review it every semester and whenever the IRB protocol, the Cornell AI Gateway terms, or the lab's tools change.

| Version | Date | Change | Approved by |
|---|---|---|---|
| 1.0 | [DATE] | Initial version | [PI] |
| 1.1 | [DATE] | Default chat prompt no longer forced on API use; projects in separate git repos; GitHub row added | [PI] |
