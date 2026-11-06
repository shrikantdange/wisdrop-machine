# Wisdrop agent chain (4 prompts)

Written 2026-11-06. Splits `docs/DIRECTOR_PROMPT.md` + `docs/FAILURE_MODES.md` into four agents.
Each prompt is standalone: paste it into any AI chat as the system prompt (or first message),
then paste or attach the input files it asks for. Each agent writes exact files; the next agent
reads them. If a prompt and a repo doc disagree, the repo doc wins and the agent flags it.

## The chain

```
AGENT 1  Research + Writer   ->  topics.md  (OWNER GATE 1: pick topic)
                             ->  brief.md, research.md, beats.md, bible.md, script.md, lines.json,
                                 titles.md, package_draft.md          (OWNER GATE 2: approve script)
AGENT 2  Director            ->  chapters.json, chapters.md, scenes.md, shots.json, director_check.md
AGENT 3  Builder (chapters)  ->  rendered chapter previews + qa/*.json + build_log.md
                                 (OWNER GATE 3: approve chapter-1 look)
AGENT 4  Voice + Finisher    ->  vo/ + vo_qc.json, final video.mp4, captions.srt, package/
                                 (OWNER GATE 4: final video + thumbnail, before ANY upload)
```

All files live in `episodes/<ep>/` (e.g. `episodes/ep02-ftx`). In a chat, "write file X" means:
print it in one fenced block headed with its file name, so the owner can save it.

## Hand-off files (formats are defined inside the prompt that writes them)

| file | written by | read by | format |
|---|---|---|---|
| topics.md | 1 | owner | scored table, 5-10 rows |
| brief.md, research.md | 1 | 2, 4 | markdown; research = fact table F01.. with 2 sources per key number |
| bible.md | 1 | 2, 3, 4 | names, `say` spellings, palette per part, music per part, counter ledger |
| lines.json | 1 | 2, 3, 4 | list of {id, text, preset, gap, visual, src, say?} |
| titles.md, package_draft.md | 1 | 4 | 5 titles, description, chapters, tags, thumbnail concepts, credits |
| chapters.json | 2 | 3, 4 | schema `schemas/chapters.schema.json` |
| shots.json | 2 | 3 | `docs/SHOTS.md` field reference |
| scenes.md | 2 | owner, 3 | one row per shot (human sheet) |
| qa/*.json, build_log.md | 3 | 4 | machine checks + per-chapter result |
| package/ | 4 | owner | title, description, chapters, captions, credits, thumbnail |

## Owner gates (an agent never passes one for the owner: FM-O01, FM-K10)
1. Topic pick (agent 1 stops after topics.md).
2. Script + cast (agent 1 stops after lines.json; repo: PR `gate/<ep>/script`).
3. Chapter-1 look (agent 3 stops after chapter 1 preview).
4. Final video + thumbnail + AI-disclosure setting (agent 4 stops; repo: FINAL REVIEW PR). No upload before it.

## How to run
**In any AI chat (no repo):** new chat per agent. Paste the prompt file, then the input files.
Agents 3 and 4 need code execution; in a plain chat they output exact commands/specs and you run them.

**Via the repo machine:** an AI with the repo reads `docs/REPO_MAP.md` first, then the prompt.
- Agent 1/2 write files in `episodes/<ep>/` and run free checks:
  `python machine/fm_check.py <ep>`, `python machine/craft_check.py <ep>`, `python machine/motion_check.py <ep>`.
- Agent 3 renders one chapter at a time: `python tools/chapter_lines.py <ep>` prints each chapter's
  `test_lines` range; run workflow `episode` with that range (`max_gpu_seconds` low), read `out/<ep>/summary.json`.
- Agent 4 runs the full `episode` workflow (cache reuses every passed line and shot), then package.

## Never bend (all agents)
Never draw a real person (FM-L03). Every number sourced, key numbers twice (FM-R01, FM-R02).
No secrets anywhere (FM-X12). Frugal: free checks first, test small, redo only what changed (FM-X08..X10).
Absolute dates (2026-11-06), times with zone. Licences CC0/PD/CC BY/CC BY-SA/MIT only (FM-P06).
