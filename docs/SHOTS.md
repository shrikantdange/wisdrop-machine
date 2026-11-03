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

## v3 look (default from 2026-11-03; library.json "look": "v3")
Board colour rotates per part (cold open navy, then off-white, sky blue, charcoal...), faint grid and
paper grain on every board, so the screen is never empty. Any shot may add:
- `marks`: `[{"k": "circle|arrow|underline|sticker|emoji", "t": seconds, ...}]` circle {x0,y0,x1,y1},
  arrow {x0,y0,x1,y1}, underline {x0,x1,y}, sticker {text,x,y,size}, emoji {code (OpenMoji hex), x,y,size}.
  Coordinates 0-1 of the frame; keep y <= 0.78 (captions live below).
- `stickers`: `["word", ...]` pop-in labels around a picture. `label`: one sticker.
- `counter_to`: value for the episode money counter (shots.json top level `"counter": {label, prefix, suffix, decimals}`).
The renderer adds a small camera punch-in when a shot would otherwise hold still > 2.5 s.

| type | fields |
|---|---|
| phone | app: sms {title, messages[{text, me, meta}]}, group {title, sub, messages[{from, text, me}]}, notify {notes[{app, title, text, icon, when}]}, bank {title, value, from, prefix, decimals, sub, down, rows[{name, when, amount, icon}]}, ticker {title, sym, values[a,b], points, change, illustrative}, inbox {rows[{from, subject, snippet, when, hl}]}, live {title, banner, viewers, messages[{from, text}]}; plus step, first, x, rot, side (kinetic line beside the phone), label, source |
| pair / trio / wall / polaroids | photos[{file or q or commons, mood, label, caption}], step, title, circle (index) |
| split | photos[2], vs (default true) |
| magnify | file or q, detail [x,y] (0-1 of the photo), zoom, label |
| map | bbox [lon0, lat0, lon1, lat1], highlight [ISO3], pins[{name, lat, lon, t, dx, dy}], flight or route [[lat,lon],...], route_at, route_s, focus, label, source |
| money | nodes[{label, icon (Tabler name), x, y, color}], flows[{from, to, label, bend}], counter {value, prefix, suffix, label}, title, source |
| stamp | text, sub, pre, color, size, rot, at_s, source |
| scrub | events[{year, label}], from, to, speed, title, source |
| barrace | items[{label, values[], color}], steps[labels], prefix, suffix, decimals, title, source |
| kinetic | + stamp: ["WORD"] words that slam in red |

## The 20 templates (copy, then change the words)
1. **Flight-route hook**: `map` + flight + 2 pins + date label (ep01 line 0).
2. **Stamp verdict**: `stamp` VANISHED / FRAUD / GUILTY with sub line + source.
3. **Big number**: `stat` + `counter_to` + underline mark.
4. **Number sentence**: `kinetic` with `stamp` on the figure + `hl` on the unit.
5. **Story picture**: `scene` (AI, composite) + label + 2 stickers + emoji mark.
6. **Document**: `card` doc/filing + highlight + sticker + marker circle.
7. **Question beat**: `coin` drain or `kinetic` question + emoji mark.
8. **Part opener**: `chapter` (stamp PART n, title, underline; riser into it).
9. **Text from a friend**: `phone` sms, 2-3 messages, side line, DRAMATISATION label.
10. **Group hype**: `phone` group, 4-6 messages from different senders.
11. **Lock screen**: `phone` notify, 2-3 notifications (buzz + ding each).
12. **Balance drop**: `phone` bank, value from -> to, rows of withdrawals (sourced numbers).
13. **Price ticker**: `phone` ticker, line draws, `illustrative` unless real data.
14. **The webinar**: `phone` live, banner, chat scrolling, side line.
15. **Inbox**: `phone` inbox, one row highlighted.
16. **Evidence pair**: `pair` of photos + labels + circle on one.
17. **Collage wall**: `wall` of 4-6 photos for "everywhere" moments.
18. **Polaroid memory**: `polaroids` stack with captions.
19. **Follow the money**: `money` nodes + flows + coins + counter.
20. **Years fly by**: `scrub` timeline or `barrace` for rankings over time.

## v4 fx (machine/engine/v4fx.py, CPU only; checks V1-V6 in craft_check)
21. **2.5D parallax**: `parallax` {file|q, label, amp=60}. One photo split into far/mid/near layers (depth = lower + more detail), drifting 1x/1.7x/2.6x. Counts as continuous motion. Credit shown.
22. **Document reveal**: `docreveal` {kind, title, lines[], redact[line idx], step=.45, quote, cps=26, source}. Scanned paper; redaction bars wipe off on twos; the quote types on under a highlighter. Quote must be verbatim from the source.
23. **Headline montage**: `headlines` {items:[{outlet, head, date, source}], step=.7}. Clippings slam in (1.45x->1x in 0.12 s, small shake). REAL headlines only, verbatim, each with outlet + date + source (V4). Column texture is grey bars, never fake words.
24. **3D coin**: `coin3d` {text, label, spins=.6, drain, drain_at}. Shaded gold coin, rim thickness, specular sweep, floor shadow; drain empties it from the top.
25. **3D chart**: `chart3d` {title, items:[{label, value, text}], hl=index, step=.45, source}. Extruded bars, top/side shading, specular sweep. Needs a source (numbers).
26. **Line-art flashback**: `lineart` {file|q, label "Flashback", flashback: true, trace=1.6}. Photo -> ink sketch (edge detection) traced on left to right with a red pen line.
27. **Transitions** (any shot, field `trans`): `glitch` = 8 frames RGB split + block displace, crypto moments only (V1), max 4 per episode (V6); `leak` = 0.5 s light-leak / film-burn wipe, only on a chapter card or the shot after it (V3).
**Beat sync** (automatic, `beat_sync: false` in shots.json turns it off): music onsets found by numpy spectral flux (same track offsets as automix); mark pops snap to a beat within 2 frames; cuts only move later (never before the voice).
28. **End screen**: `endscreen` {text, sub}. Last line of every episode; that line gets `gap` 16 in lines.json so the board runs ~20 s (YouTube end screens use the last 5-20 s, video must be >= 25 s; up to 4 elements on 16:9). Code-drawn slots: 16:9 "WATCH NEXT" box left (x 250-1070, y 340-801 at 1920x1080), round SUBSCRIBE slot right (centre 1430, r 190). In Studio: Editor -> End screen -> place the Video element on the box and Subscribe on the circle. Slots breathe, so it is never a still frame.
