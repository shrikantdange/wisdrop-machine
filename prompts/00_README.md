# Wisdrop agent chain (4 standalone prompts)

Version 2, 2026-11-06. Each prompt is now **fully self-contained**: role, inputs and their validation, numbered steps
with time and token budgets, every rule inlined with its FM id, exact output schemas, a worked example from ep01
OneCoin, a self-check, the exact owner-gate message, error handling, hand-off and token-saving rules. An agent never
needs to open another document. The long reference stays in `docs/` (DIRECTOR_PROMPT, FAILURE_MODES, SHOTS,
AI_MOTION_CRAFT, EDITING_CRAFT, RETENTION, THUMBNAILS, PUBLISH_CHECKLIST); if a prompt and a repo doc ever disagree,
the repo doc wins and the agent flags it in one line.

## Which file to paste where

| agent | file | paste into | needs | start with |
|---|---|---|---|---|
| 1 Research + Writer | `01_research_writer.md` | any AI chat with web browsing (system prompt or first message) | web access | `Start. Episode folder: episodes/<epNN-slug>. Constraints: <...>` |
| 2 Director | `02_director.md` | any capable AI chat; attach agent 1's files | no tools needed (repo helps for free checks) | `Direct episodes/<ep>.` |
| 3 Builder | `03_builder.md` | an AI with code execution + the repo + GitHub workflow access (Hark project, Codex, Claude Code, etc.) | repo, gh/GitHub connector | `Build episodes/<ep>, chapter c01 first.` |
| 4 Voice + Finisher | `04_voice_finish.md` | same as agent 3 | repo, GitHub workflows | `Voice and finish episodes/<ep>.` |

Use a **new chat per agent**. In a plain chat without code, agents 3 and 4 print exact commands and workflow inputs; you
run them and paste back the JSON results.

## The chain

```
AGENT 1  Research + Writer   ->  topics.md                                  OWNER GATE 1: pick the topic
                             ->  brief.md, research.md, beats.md, bible.md, hooks.md,
                                 script.md, lines.json, titles.md, package_draft.md
                                                                            OWNER GATE 2: approve script + cast
                                                                            (merge PR gate/<ep>/script)
AGENT 2  Director            ->  chapters.json, chapters.md, scenes.md, shots.json, director_check.md
AGENT 3  Builder             ->  chapter previews (c01 first), qa/*.json, build_log.md
                                                                            OWNER GATE 3: approve the chapter-1 look
AGENT 4  Voice + Finisher    ->  voice QC + retakes, full cached run = one film, seams.md,
                                 mastered video.mp4, captions, package/, thumbnails
                                                                            OWNER GATE 4: final video + thumbnail +
                                                                            title + AI disclosure (merge FINAL REVIEW PR)
OWNER uploads (never an agent)
```

## Hand-off files

| file | written by | read by | format defined in |
|---|---|---|---|
| topics.md | 1 | owner | 01 section 5 (weighted score /100) |
| brief.md, research.md | 1 | 2, 4 | 01 sections 6-8 (fact table F01.., two sources per key number) |
| beats.md, hooks.md | 1 | 2 | 01 sections 9, 11 |
| bible.md | 1 | 2, 3, 4 | 01 section 10 (names, say spellings, palette, music, counter ledger) |
| script.md, lines.json | 1 | 2, 3, 4 | 01 section 12 (lines.json schema + ep01 excerpt) |
| titles.md, package_draft.md | 1 | 4 | 01 section 13 |
| chapters.json, chapters.md | 2 | 3, 4 | 02 section 8 (schema `schemas/chapters.schema.json`, ep01 example) |
| scenes.md, shots.json | 2 | 3 | 02 sections 9-10 (field reference + ep01 excerpt) |
| director_check.md | 2 | 3, owner | 02 section 11 |
| build_log.md, qa/*.json | 3 | 4 | 03 section 6 |
| seams.md, package/, captions | 4 | owner | 04 sections 8-9 |

## Owner gates (an agent never passes one for you: FM-O01, FM-K10)

| gate | when | you see | you do |
|---|---|---|---|
| 1 topic | after topics.md | top 3 with scores and risks | reply with a row number |
| 2 script + cast | after lines.json | runtime, hook, title, open items | merge PR `gate/<ep>/script` or send line ids + notes |
| 3 chapter-1 look | after c01 renders | preview link, checks, cost | approve, or say what to change (cheap now) |
| 4 final | after the full run | video, thumbnail, title, AI-disclosure recommendation, cost | merge the FINAL REVIEW PR; then upload yourself |

## Token cost note

A longer prompt costs a little more input on every turn (about 7-11k tokens per prompt; cached by most providers after
the first turn). It saves far more: no exploring the repo, no guessing formats, fewer wrong outputs and far fewer redo
rounds, which are the expensive part (a redo of research or a render costs more than the whole prompt many times over).

## Never bend (all agents)

Never draw a real person (FM-L03). Every number sourced, key numbers twice (FM-R01, FM-R02). No secrets anywhere
(FM-X12). Frugal: free checks first, test small, redo only what changed (FM-X08, FM-X09, FM-X10). Absolute dates,
times with zone. Licences CC0 / PD / CC BY / CC BY-SA / MIT only (FM-P06). Owner approves before any upload (FM-K10).

## Files

PDFs for reading: `WISDROP_AGENT_1_RESEARCH_WRITER.pdf`, `WISDROP_AGENT_2_DIRECTOR.pdf`, `WISDROP_AGENT_3_BUILDER.pdf`,
`WISDROP_AGENT_4_VOICE_FINISH.pdf`, `WISDROP_AGENT_CHAIN_README.pdf`. Paste the `.md` files, not the PDFs.
