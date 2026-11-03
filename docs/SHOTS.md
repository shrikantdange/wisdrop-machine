# shots.json: how an episode is drawn (the only per-episode visual file)

The operator AI writes `episodes/<ep>/shots.json` from the `visual` notes in lines.json.
Nothing else is per-episode: the renderer, motion, captions, grade and mix are shared, so
every episode has the same visual language.

```json
{"music": ["Spy Glass", "Investigations", "Investigations", "Hitman", "Spy Glass", "Investigations"],
 "shots": [ {"at": 0, "type": "scene", ...}, ... ]}
```
- `at`: the line id where the shot starts (cut lands at the line's start + 0.04 s). `offset`: extra seconds.
  A shot lasts until the next shot. Every line must be covered; the first shot starts at 0.
- `music`: one kit/music track per part; parts change at each `chapter` shot (index 0 = cold open).
- Any shot may add `"sfx": [{"n": "coins", "off": 0.3, "under": 10}]` (kit/sfx names) or `"quiet": true`.

| type | fields |
|---|---|
| scene | set (library set id or "board"), time (library time_light key), move (push, pull, hold, pan_l, pan_r), focus [x,y], cast [{who, pose, x 0-1, h, y, flip, enter}], light [[x,y,r]], fx [rain, dust, sparks, flicker, dim], overlay [{text, x, y, size, color, t, mono}] |
| stat | value, decimals, prefix, suffix, text (fixed text instead of a count), color, label, source |
| headline | outlet, date, title, sub, highlight, source, recreated (default true) |
| card | kind (filing, email, quote, doc, post), header, date, from, lines [..], highlight, source, recreated |
| name | name, role, color, source |
| chapter | num, title |
| flow | title, boxes [label or {label, color, strike}], step, source |
| tree | levels, branch, label, source |
| bars | items [{label, value, text, color}], source |
| timeline | events [{date, label, color}], source |
| list | items [text or {text, strike}], step, source |
| chart | points [0-1 ...], label, draw, illustrative (default true), source |
| coin | drain, drain_at, label |
| screen | device (laptop, phone), set + time (blurred behind) or none, ui: balance {title, value, prefix, suffix, decimals, tick, sub} / chat {messages [{text, meta, me}]} / banner {text} / text {lines} |
| end | text, sub |

Rules: real people are never a `cast` member (use name/card/headline). A new set, cast member or
pose must be added to library/library.json first; `machine/plan_images.py` refuses unknown ones.
Colours: red, gold, amber, paper, grey, green, white. Words on screen are always drawn by code.

## Quality rules (v1.1)
- A `scene` with `cast` is COMPOSED by the image model: the character is painted into the set with the
  set's own light and shadows (Qwen-Image-Edit-2509, refs = set plate + character master). No paste-on
  cutouts in story shots. Use `"compose": false` only for a character entering/moving (`enter`).
- Never put `overlay` code text on a generated picture (it will not line up). Put words on board shots:
  card, headline, stat, screen, list.
- Reuse beats variety: the same set+time+cast+pose makes the same picture for free (cache).

## COLLAGE look (v2, default from 2026-11-03; library.json "look": "collage")
Vox/BBC-style: charcoal paper board, torn cream paper cards with tape, duotone + halftone
treatment on every picture, yellow highlighter, red marker, kinetic type. Aim per episode:
~60% code graphics (stat, card, kinetic, chart, flow, timeline, list, screen), ~25% real photos,
10-15% AI pictures (only Rosa-type story moments that no photo can show).

New shot types:
- `photo`: `{"type":"photo","q":"Sofia Airport terminal","mood":"dawn","label":"Sofia, 25 Oct 2017"}`
  machine/fetch_media.py finds a commercial-safe Wikimedia Commons photo (CC0/PD/CC BY/CC BY-SA),
  credit goes on screen and in the description. Or `"commons": "File:Exact.jpg"`. Options: `w`,
  `x`, `y`, `rot`, `crop_y`, `bleed` (full frame), `mood` (time-of-day duotone or `archive`).
  Never use a photo of a real person as if it were someone else; photos of real people only when
  they ARE that person and the licence allows.
- `kinetic`: `{"type":"kinetic","text":"Then she vanished.","hl":"vanished","step":0.25}` words
  pop in one per `step` s, `hl` words get the highlighter (pop and marker sounds are automatic).
- `scene` now shows the AI picture as a taped collage card (or `"bleed": true` for full frame),
  with optional `label` sticker.
Sounds: every scene/photo gets a paper slide + tape, kinetic words get pops, highlighter gets a
marker squeak, lists/flows get flicks. All synthesised by tools/synth_sfx.py (CC0, ours).
