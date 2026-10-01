# Cornell AI Gateway keys

How keys are issued, loaded and protected. The short version: **the PI issues each student one key per Cornell team in the gateway dashboard; the kit loads the right one for the project you're in.**

## How it works

- The PI has several **teams** in the Cornell gateway, each tied to a budget. From a team's dashboard she issues one key per student, each with its own spending cap.
- Each project belongs to one team. The team's name is stored in the project's `.lab-project` file (a single line such as `soc-media-2026`). It holds no secret and is committed with the project.
- Inside a project, `lab-key` finds `.lab-project`, asks for **your** key for that team, and loads it into the current terminal window only. Everything that uses the gateway (`labllm`, `claude-cornell`, `opencode`, `codex --profile cornell`, `lab models cornell`) reads it from there.
- `cd` into a project from a different team and a one-line hint tells you to run `lab-key` again. Nothing is switched silently, and switching never leaves the old team's key in the window.
- `lab-key <team>` loads a team's key when you're not inside a project.
- `labllm` records the window's team in `labllm.jsonl` next to your NetID. Cornell's per-key spend is the source of truth for billing; the log is for local reference only.

## PI / admin tasks

| Task | How |
|---|---|
| New team | Create it in the Cornell dashboard, then add its slug (lowercase letters, digits, `- _ .`) to `config/teams.txt` and run `lab update` / copy it to the kit. |
| New student on a team | Issue them a key in that team's dashboard with a cap. Send it privately, never in a channel the lab doesn't control. |
| Student leaves, or a key leaks | Revoke that one key in the dashboard. Nothing in the kit changes. |
| Key expires (90 days) | Issue a replacement; the student runs `lab-key` again. With the `age` backend they delete `/Users/Shared/research/<netid>/.keys/<team>.age` first. |

Keep the roster of who holds a key for which team in your own records, not in this repo. `config/teams.txt` lists team names only.

## Student tasks

```
cd /Users/Shared/research/<netid>/<project>
lab-key            # paste your key for this project's team (input is hidden)
```

New projects ask which team they belong to (`lab new <name> --team <slug>` skips the question). For an older project, run `echo <team> > .lab-project`.

### Optional: keep keys encrypted (`age`)

Set `LAB_KEY_BACKEND=age` in your window (or in `config/lab.local.env` for everyone) and install `age` (`brew install age`). The first `lab-key` for a team asks for the key once and for a passphrase, and saves the key encrypted under `$LAB_PROJECTS/<netid>/.keys/<team>.age`. After that you only type the passphrase. Use a long passphrase: everyone shares this macOS account, so anyone can copy the encrypted file and try to guess it offline.

## What this does not protect against

Everyone shares one macOS account, and there is no admin tooling that needs `sudo`. So:

- A key loaded in a window can be read by other people on the account (`ps eww`, agent session logs under `~/.claude` and `~/.codex`). Never paste a key into an agent chat.
- The limits that matter are therefore **per-key caps and prompt revocation**, which Cornell enforces: a leaked key costs at most that student's cap on that team.
- The pre-commit hook refuses commits containing key-shaped strings (`sk-…`, GitHub tokens, private keys, `CORNELL_AI_API_KEY=…`) and reports file names only. It's a safety net, not a guarantee.

The full fix is structural: per-student macOS accounts, or a gateway proxy owned by a separate account that holds the real keys. Either needs `sudo`, so both are deferred. `lab-key` reads keys through `LAB_KEY_BACKEND`, so a new source can be added without changing anything else.
