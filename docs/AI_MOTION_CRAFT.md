# Wisdrop AI/code motion craft (AMC rules)

> **Owner decisions, 2026-11-03 (these win over anything below):**
> 1. **No coin, ding, cash or other game-UI sounds** (AMC-S2). Money moves get a swish or tick.
> 2. **Headline type at least 76 px** (AMC-L2; replaces EDITING_CRAFT T3's 72 px).
> 3. **Music sits 22 dB under the voice** as a static bed (AMC-S3/S4; replaces EDITING_CRAFT S4's 15 LU).
>    Band 18-25 dB; any voice line under 8 dB over the bed is flagged.
> 4. **Punch-ins only on stamps** (AMC-V3), stepped on twos. Every other hold gets the slow push (1.2 %/s, cap +6 %).
> 5. **When two rules conflict, the simpler option wins.**
>
> Where it lives in code: `machine/engine/motion.py` (tokens: easing, durations, crc32 seeds, on-twos,
> hold push, punch, contrast), `machine/motion_check.py` (checks, before spend and on rendered frames),
> `machine/engine/automix.py` (music level, banned sounds, sound sync), `machine/worker_render.py`
> (determinism probe). Planted-defect fixture: `machine/fixtures/motion_defects/` (must FAIL 4 checks).
>
> Coded now: crc32 seeding + lint (W1), determinism probe (W2), easing presets (M1), push cap (V2),
> stamp-only punch (V3), paper marks/stickers on twos (T6), maps show change (E1), accent area (C2),
> board contrast (C3), pure black/white (C4), flashes (M10), frame 0 (H1), headline size (L2),
> nothing before the voice (N4), banned sounds (S2), music level + per-line 8 dB alert (S3),
> sound sync <= 2 frames (S5), signposts (H3), long sentences (N2), pause after a question (N3).
> The rest of the 45 checks listed at the end are still to code.


Researched 2026-11-03 for Wisdrop (faceless money-crime explainers, 1920x1080 at 30 fps, rendered by
Python + Pillow/numpy + ffmpeg, AI voice, occasional AI images). This file **extends**
`docs/EDITING_CRAFT.md` (v3). It does not repeat what is there: pacing P1-P5, the hook beats
H1-H3, open-loop rules L1-L2, text rules T1-T7, the sound layers S1-S8, thumbnails K1-K5 and licences.
Where a rule here changes a number there, the row says **[changes EC-xx]**.

**ID namespace.** Rule IDs here carry the prefix `AMC-` when cited from code or other docs (e.g.
`AMC-S3`), because the letters T, L, S and H also exist in EDITING_CRAFT with other meanings.

**Frame maths.** All frame counts assume 30 fps: 1 frame = 33.3 ms; 0.1 s = 3 f; 0.5 s = 15 f; 1 s = 30 f.
Where a source gave frames at another rate, the seconds are kept and converted.

**Source tags.** Numbers in [brackets] point to the source list at the end. [R] = page read in full;
[S] = seen in search results only (a lead, not proof). A rule marked **(proposal)** is my
inference for Wisdrop, not a number a source gave; treat it as a starting value to tune.

**What the strongest new sources are.** Most of the machine-checkable numbers come from people who
build video *by code* and had to turn taste into thresholds: the `showtime` agent video studio docs
(motion craft, colour, sound design, QA, all with measured thresholds) [1-4], the Daena Digital
"grain and map" agent skill that studied Johnny Harris frame by frame every 0.5 s [10], Remotion's
docs on deterministic rendering [11-13], and the IBM Carbon and Material 3 motion token systems [6][7].
Retention and story rules come from Paddy Galloway [8]; measured music levels from three narrated
documentary channels [5].

---

## 1. Colour

| ID | Rule (machine-checkable where possible) | Source |
|---|---|---|
| C1 | **Palette as tokens, each hex written once.** Roles: `ground`, `ink`, `muted`, `accent`, optional `accent2`, `surface`. A hex literal anywhere outside the palette module is a bug (grep `#[0-9a-fA-F]{3,8}` and `(r,g,b)` tuples in scene code). | [3] |
| C2 | **Accent discipline: one accent hue on at most 15 % of the frame area**, and the accent visible in every shot. 60-30-10 as the target split: ground ~60 %, secondary/surface ~30 %, accent ~10 %. Measure per keyframe by counting pixels within ΔE2000 < 10 of the accent. Pass: 0.3 % ≤ accent area ≤ 15 %. | [3] [17] |
| C3 | **Contrast on real rendered pixels, including mid-transition frames:** body text ≥ 4.5:1, large display (≥ 76 px) ≥ 3:1, ink on ground ≥ 7:1, accent used as text ≥ 4.5:1, accent used as a shape ≥ 3:1. WCAG ratio = (L1 + 0.05)/(L2 + 0.05) on relative luminance; judge a fading text at its most opaque frame. | [3] [4] |
| C4 | **No pure #000 or #FFF on large areas.** Near-black `#0B0B0D`-`#141416`, off-white `#F4F2EE` (warm) or `#F2F4F7` (cool). Pure black crushes on phones, pure white glares. Tint neutrals slightly toward the accent. | [3] |
| C5 | **Never encode meaning in red vs green alone** (about 1 in 12 men are red-green deficient). Money in/out, real/fake, before/after: pair colour with a sign, arrow, label or position. Blue/orange is the safe pair. | [3] |
| C6 | **Charts:** focus series in the accent, all other series grey at 30-40 %; label series directly, no legend; at most 7 bars or 3 lines per frame. | [3] |
| C7 | **Survive compression:** saturated strokes ≥ 3 px at 1080p (4:2:0 halves colour resolution, 1-2 px red lines smear); small text on a neutral ground, never red on blue; large red or magenta fields (stamps, "FRAUD" banners) pull chroma down 5-10 % because they bloom after YouTube's re-encode. | [3] |
| C8 | **Colour script per act.** Plan a strip of one small swatch per scene before rendering: colour gets more intense when emotion is more intense and muted when things turn somber (Pixar colour scripts, Lasseter). MagnatesMedia gives each episode its own colour theme. For Wisdrop: an `acts[]` block in the episode JSON with `ground`, `saturation_mult`, `vignette` per act; the accent never changes. Check (proposal): neighbouring acts' grounds differ by ΔE2000 ≥ 15 so the act change is felt; mean saturation of Twist/Fall frames ≥ Setup frames unless the act is marked `somber`. [extends EC §6] | [18] [22] |
| C9 | **Building a palette with no brand:** work in OKLCH from one hue. Dark ground L 0.14-0.18, chroma ≤ 0.02; light ground L 0.96-0.98; accent L 0.65-0.78, chroma 0.14-0.22; check the accent against the ground *and* against a white caption. Light grounds need bolder structure (2-4 px rules, full-saturation accent hits, paper grain) to feel cinematic. | [3] |
| C10 | **Clichés that read as generic AI output:** purple-to-blue gradients, neon cyan on black, gradient text, rainbow accents, glowing glassmorphism. Do not use. | [3] |
| C11 | **Never grade UI mockups, logos, screenshots or documents.** Mood comes from the ground, glows and vignette, not from shifting the evidence's hues. Grade only photographs and AI images, toward the act's ground (lifted blacks, slightly desaturated, warm cast). | [3] [10] |
| C12 | **Colour survives the encode:** a flat brand/accent area sampled from the final MP4 is within about 2 levels (of 255) of the source hex. | [3] |

## 2. Patterns and textures

| ID | Rule | Source |
|---|---|---|
| T1 | **Grain on every frame, animated, same strength in every shot.** A new seeded noise field per frame (seed = episode id + frame index, see W1), monochrome, 1.5-3 % opacity over flat grounds and any gradient or glow. The stylised documentary look runs stronger (Daena's JH skill uses "about 0.35 on a 0-1 scale"): pick one strength per episode and keep it; a shot without grain looks like it came from another video. Check (proposal): std of luma in a flat 64x64 ground patch is within ±25 % of the episode median on every shot. | [3] [10] |
| T2 | **No full-screen linear gradient on a dark ground** (bands after H.264 and again after YouTube's re-encode). Use a solid ground + 1-2 radial glows, peak opacity ≤ 0.45, radius larger than the frame's short side (≥ 1080 px), placed off-centre so the field is never one flat value. | [3] [10] |
| T3 | **Vignette always on at about 0.3** (corners darker than centre) on designed boards, so a light leak reads as light. (On graded photo footage alone, keep vignette 0-0.05.) | [10] [3] |
| T4 | **Light leak: at most one per scene,** warm orange-to-pink blur drifting in from a corner over ~1 s, peaking under 40 % opacity, gone by mid-scene; placed on the cut, never mid-sentence; sits above everything except captions. Generated procedurally (blurred gradient), never a downloaded overlay of unknown licence. | [10] |
| T5 | **Photo cut-outs:** 2-3 layers (subject, middle, background), each edge feathered 2-4 px, background layer blurred 2-3 px, subject sharp; all photos graded to the same field before placing. Sticker border 3-6 px (EC source [2]). | [10] |
| T6 | **Stepped motion ("on twos") on paper elements only.** The Vox/JH stutter = graphics animated at ~12 fps inside a smooth edit; 8-12 fps is the documentary sweet spot, 15-18 fps for fast moves that turn unreadable at 12, 2-6 fps only for single hard graphic hits. In our 30 fps timeline: hold each pose **2 frames (15 fps) by default, 3 frames (10 fps) for the stronger look**. Keep the camera push, captions and voice-synced kinetic type smooth: the contrast between stepped elements and smooth layers *is* the effect; stepping everything makes it disappear. (Mapping 12 fps → 15/10 fps is my conversion, since 12 does not divide 30.) | [9] |
| T7 | **Deliberate imperfection:** tiny rotation wobble, slight position drift and small frame-to-frame exposure flicker on paper layers, each "felt rather than seen". Starting values (proposal): rotation ±0.5-1.5°, position ±1-3 px, exposure ±1-2 %, all stepped with T6 and seeded. Background drift 2-8 px x, 1-4 px y, 1-3 slow cycles per shot. | [9] [2] |
| T8 | **Grids and paper lines** are `muted`: ink at 8-15 % opacity for lines, 45-65 % for secondary text. On light grounds rules are 2-4 px. | [3] |
| T9 | **Banding test:** look at the darkest gradient of each act at 200 % zoom in the final encode. Master flat motion graphics at x264 **CRF 14-16** so grain survives. | [3] |
| T10 | **Moiré:** thin far rings, fine halftone and fine grids alias when scaled. Halftone cell ≥ 6 px and grid pitch ≥ 12 px at final size (proposal); never scale a halftone layer continuously below 1.0 (re-render the dots at the target scale instead). The showtime critic flags "moiré in thin far rings". | [2] |

## 3. Elements and when each fits a story beat

**E0. Every element has exactly one verb** (one way of arriving), and the same one every time [10]:

| Element | Verb (timings at 30 fps) | Source |
|---|---|---|
| Photo / AI image | Hard cut in *already moving*, pushes for the whole scene; no fade, no slide | [10] |
| Map | Camera flies wide → place once per map scene (see V4) | [10] |
| Route / money-flow line | Draws on along its path over ~0.8-1.6 s, paced to the clause that names the journey; no clause, no route | [10] |
| Pin | Drops from above over ~8 frames with one small bounce, holds; its label types on *after* it lands | [10] |
| Label | Types on ~2 frames per letter with a block cursor that disappears when the word is done; condensed or mono uppercase, tracked out | [10] |
| Big line | Lands word by word on the voice; each word pushes up 20-30 px with a snappy spring and blur→sharp over 4 frames; marked phrase in accent | [10] |
| Slate (place, year, source) | Fades up over ~10 frames: the only element allowed to fade | [10] |
| Stamp / "FRAUD" / "SEIZED" | A snap beat (E8) | [2] |
| Light leak | Drifts in on the cut, gone by mid-scene (T4) | [10] |

| ID | Rule | Source |
|---|---|---|
| E1 | **A map is a process, not a place.** Every map scene shows something changing: an area filling or retreating over 0.8-2.5 s on the clause that names the change, a marker riding with its fill, a date stamp at top centre changing on the word that names the new time. A pin on a still map is a caption, not a map scene. At most two fill colours (accent + one). | [10] |
| E2 | **A history (or "all of these", "dozens of victims") is a montage,** not one photo: ≥ 10 real sources in a row, each on screen 0.5-1.5 s (15-45 f), each cutting in already pushing 1.00 → 1.06 or panning across its text, inside a rounded "slide" frame. One documented variant starts at ~8 frames per item and accelerates, with a camera-click on each cut. | [10] [S: Motion Array, 24] |
| E3 | **A capture is raw material.** A screenshot, filing, tweet or bank statement goes into a montage, a parallax layer or onto the map; it is never the whole frame with only a highlight on it. | [10] |
| E4 | **Highlighter / underline** lands on the stressed word, timed from the word timings (N4), revealed as a left-to-right wipe line by line over the word's duration; one per card [EC T5]. | [10] [EC] |
| E5 | **UI mockups (phone, SMS, push notification, bank app, exchange dashboard) move like UI, not like paper:** micro-motion 100-300 ms on `standard` cubic-bezier(0.2, 0, 0, 1); a notification banner enters on emphasized-decelerate (0.05, 0.7, 0.1, 1) ~400 ms and leaves on emphasized-accelerate (0.3, 0, 0.8, 0.15) ~200 ms; button/toggle micro-interactions 70-110 ms. Carbon reserves "expressive" motion for system alerts and notifications, i.e. the scam alert is the expressive moment, everything else productive. Typing and ticking counters use `steps(n)`. Never stepped (T6), never graded (C11). | [7] [6] [2] |
| E6 | **Zooming into a UI target** (the amount, the sender, the link): 1.5-2x for a tap or typed text, 1.3-1.5x for a scroll, hard max ~2.8x; transition duration = 0.6 s + 0.55 s x ln(zoom) (2x → 0.98 s); start 0.15-0.4 s before the action; hold ≥ 1.2 s. Render the mockup at ≥ the max zoom resolution (V6). | [2] |
| E7 | **Charts:** one stage per ~1 s (axis, then marks, then labels); count-ups 1.2-2.5 s (under 0.8 s reads as a flash), eased out, landing on a beat; bars rise on a damped spring staggered 45 ms; land the chart by ~1.25 s and keep a slow push so it never sits still. Over ~50 marks (bars, dots, transactions) reveal with one wipe, not per-mark staggers. A number the viewer must read is held its reading time. | [2] |
| E8 | **Stamps, slams and whips are "snap beats":** the whole distance in 6-9 frames on a hard ease-out (0.16, 1, 0.3, 1), most of it in the first 2-3 frames, then a settle; motion blur only on the snapping element and only on 1-3 snap beats per video; never on text being read. One impact sound per moment (S2). | [2] [1] |
| E9 | **Arrows and annotation circles are drawn on and stepped** (T6) so they read as hand-made, not rendered. | [9] |
| E10 | **Beat → element map for Wisdrop** (proposal built on E1-E9 and [10]: "a map when the voice names a place, a photo when it names a person or thing"): Hook = phone/SMS or stamp or stat; Setup = map + pin, photo montage of the world before; Rise = money-flow routes, counters, charts; Twist = bank-app/exchange UI, document with highlighter; Fall = court filings montage, stamps, red slate; Aftermath = return to the cold-open frame with the new fact typed on. | [10] (proposal) |

## 4. Placement and composition

| ID | Rule | Source |
|---|---|---|
| L1 | **Safe areas (EBU R95 / SMPTE ST 2046-1):** all essential action inside the central 93 % (inset 67 px left/right, 38 px top/bottom at 1920x1080); all text and graphics inside the central 90 % (inset 96 / 54 px). Additionally no small text in the bottom 8 % (YouTube player controls). Our caption band (EC T6, y > 900) sits inside this. | [15] [4] |
| L2 | **Text size floors:** headline ≥ 7 % of frame height = **76 px** [changes EC T3, was 72]; body ≥ 36 px (EC keeps 40, fine); absolute phone floor 5 pt at phone width = 25 px at 1920 wide (2.2 % of height = 24 px); anything below is a FAIL. One idea per card, 1-6 words. | [2] [4] |
| L3 | **Eye trace across cuts.** Divide the frame into 4 quadrants + centre. At the cut, the eye is where the outgoing shot's focus was; put the incoming focus there, or leave that spot deliberately empty so the eye searches. Murch weights eye trace 7 % of a cut's value (emotion 51, story 23, rhythm 10), but in fast faceless video it matters more. Check (proposal): each shot declares `focus_xy`; distance between outgoing focus at cut − 0.1 s and incoming at cut + 0.2 s ≤ 25 % of frame width unless the shot is tagged `jump`. | [16] [S: nofilmschool] |
| L4 | **Cut seams:** same axis, direction and speed on both sides of a cut; cut mid-motion; one main direction for the film (forward push into the picture). The map flight is the move held in reserve for arriving at a place. | [10] |
| L5 | **Three layers in every scene, never fewer:** background (ground + glow + vignette + grain, or the map), midground (photo in parallax, routes/pins), foreground (labels, big line, slate, leak). Parallax: 2-4 depth layers, far layers move 20-40 % of near layers; JH preset: subject 1.00 → 1.08 over the scene, middle half that, background a quarter; layers never stop. | [10] [2] |
| L6 | **At most 2 focal points per frame** (the photo's subject + one line, or the pin + its label). Anchor to edges and use asymmetric splits; centred-everything reads as a web template. | [10] [2] |
| L7 | **Crowding:** labels in one graphic (map names, chart values) never closer than 0.15 em to each other; otherwise aggregate or label only the highlight and extremes. | [4] |
| L8 | **Small moves read premium:** entrances scale from 0.94-0.98 (never from 0), translate 16-40 px (not 200); mask reveals and blur-in (8-12 px → 0) instead of plain fades. | [2] |
| L9 | **Thumbnail = frame 0 = "paused in action":** the opening frame feels like an action about to unpause; bright (≈ 75 % of viewers use dark mode); ≤ 4-5 short words; passes a split-second glance test. | [8] [4] |

## 5. Camera and view

| ID | Rule (exact numbers) | Source |
|---|---|---|
| V1 | **Push-in:** scale 1.00 → 1.04-1.08 over the whole shot, `sine.inOut` or `camera` cubic-bezier(0.65, 0, 0.35, 1). Perception: < 5 % reads static, 10-15 % comfortable, > 30 % dramatic. Never the same ambient zoom on every scene. | [2] |
| V2 | **Hold push (anti-freeze):** any hold > 2 s keeps a slow push of **1.2 % scale per second** (0.04 % per frame at 30 fps), capped at +6 %; 0.8 %/s is borderline for freeze detectors; ≥ 7.5 %/s reads as a zoom, not a hold. On dark frames give a text-only scene a 7-8 % push over the scene. | [2] |
| V3 | **Punch-in:** 1.0 → 1.15-1.3 in 0.25-0.4 s on `power3.out`, hold ≥ 1 s. showtime bans it in explainers ("cheap"), while the Vox/JH style uses aggressive, stepped punch-ins. Resolution for Wisdrop: only on snap beats (E8), stepped (T6), never on consecutive cuts. | [2] [9] |
| V4 | **Map flight:** one continuous camera move per map scene, wide → place over 40-60 frames (≈ 1.3-2 s), eased in and out, with 2-3° rotation so it reads as a flight, not a zoom. Never two map flights in a row. | [10] |
| V5 | **Pull-back reveal:** author the wide at 1x and open scaled in; never enlarge a 1x close-up. In Pillow: every source is rendered or loaded at ≥ (max scale it will reach) x its displayed size; upscale > 1.5x of native pixels is a WARN. | [2] [4] |
| V6 | **Drift:** 2-8 px x, 1-4 px y, 1-3 slow cycles per shot, background layer only. | [2] |
| V7 | **Shake:** only on impacts, ≤ 0.3 s, decaying amplitude, decorrelated x/y noise (seeded). The JH style uses no camera shake at all; the parallax push is the only camera. | [2] [10] |
| V8 | **Whip pan / whip blur:** a snap move in 6-9 frames with blur on the fast frames only; 1-3 per video. | [2] |
| V9 | **Easing for camera moves between two rests:** `camera` (0.65, 0, 0.35, 1) or easeInOutCubic (Motion Canvas's default for camera and property tweens); for long moves 3b1b's `smooth` (zero 1st and 2nd derivative at both ends: s=1−t; t³(10s² + 5st + t²)). Ease zoom in log-zoom space so a 1x→4x move feels even. | [2] [19] [20] |

## 6. Motion principles

| ID | Rule (exact values) | Source |
|---|---|---|
| M1 | **Easing table (one ease per job, same every time):** entrances/reveals `premium` cubic-bezier(0.16, 1, 0.3, 1) or power3.out; exits (0.3, 0, 0.8, 0.15), 20-30 % shorter than the entrance; moves between rests `camera` (0.65, 0, 0.35, 1); UI micro-motion `standard` (0.2, 0, 0, 1) and emphasized-decelerate (0.05, 0.7, 0.1, 1); ambient/Ken Burns `sine.inOut`; ticking `steps(n)`; linear only for opacity < 150 ms, rotation loops and tickers. Carbon alternates: productive standard (0.2, 0, 0.38, 0.9), expressive standard (0.4, 0.14, 0.3, 1), expressive entrance (0, 0, 0.3, 1), expressive exit (0.4, 0.14, 1, 1). | [2] [6] [7] |
| M2 | **Durations:** element entrance 0.3-0.6 s (9-18 f); exit 60-80 % of its entrance; scene/layout move 0.5-0.8 s; first motion 0.1-0.3 s (3-9 f) after a cut, hero visible by 0.5 s; hold ≥ 1 s after a move lands in an explainer, 1.5-2.5 s for anything to read. Duration grows with distance travelled (Carbon and M3 both scale duration with size). Token anchors: M3 emphasized 500 ms on-screen / 400 ms enter / 200 ms exit; Carbon 70, 110, 150, 240, 400, 700 ms. | [2] [6] [7] |
| M3 | **Overshoot:** default none. Overshoot once, on one hero element, never on blocks of text. Spring damping ratio 1 = no overshoot, 0.8-0.85 ≈ 1-2 % overshoot, 0.6-0.7 playful. Remotion's default spring (mass 1, damping 10, stiffness 100) bounces: raise damping (e.g. 200) to remove it. Overshoot curves on transforms only; opacity gets its own non-overshooting ease. | [2] [12] |
| M4 | **Anticipation and contact:** visual hits land 1-2 frames before the beat/sound transient; a whoosh 1-2 frames before a cut reads as anticipation; 0.25-0.5 s of near-silence and stillness before a reveal; then the riser stops and the impact hits on the reveal frame. | [1] [2] |
| M5 | **Stagger in importance order:** letters 15-25 ms, words 30-60 ms (1-2 f), list items/cards 60-100 ms (2-3 f); each group's total ≤ 0.4-0.5 s; over ~9 items use one wipe. Mood: 40 ms urgent, 80 ms conversational, 150 ms deliberate, 250 ms+ ceremonial. Decaying cascade: each next item travels less (80 → 60 → 45 → 30 px) or starts sooner (gap x 0.85). Vary entrance direction between groups. | [2] |
| M6 | **Kinetic typography:** per-letter animation only for 1-3 word hero titles; readable text animates by word or line; at most one big line per scene (the claim or the turn); emphasis by weight, colour or scale, one at a time; never shake, wiggle or rainbow text; display tracking −0.02 to −0.04 em; max 2 type families; numbers in tabular figures. | [2] [10] |
| M7 | **Scene phases:** build 0-30 % (staggered entrances), breathe 30-70 % (one small ambient motion or stillness), resolve 70-100 % (the decisive element, then a still hold). Reveal as it is said and spread reveals into the back half; never front-load and freeze. | [2] |
| M8 | **Rhythm:** slowest scene ≈ 3x the fastest; short-short-long with the longest hold on the key message; 60-70 % of motion on the beat grid feels musical, 100 % mechanical. | [2] |
| M9 | **Dead stops:** a fast move (6+ frames of change) must ease out its last 6-10 frames; landing at ≥ half peak speed then freezing for 4+ frames is a defect. | [4] |
| M10 | **Photosensitivity:** ≤ 3 flashes in any 1 s (WCAG general flash: ≥ 0.1 linear-luminance change over ≥ 25 % of the frame); space strobes and glitch bursts ≥ 0.33 s apart; ≤ 2 flash frames per video. | [4] [2] |

## 7. Sound design

| ID | Rule | Source |
|---|---|---|
| S1 | **Density and family:** one designed sound per visual event that *matters*, not per moving element. Cinematic register = 2-4 big riser→impact moments per video plus subtle cues; whooshes only for far moves or scene changes; text pops on 20-40 % of text events (first, last, the important one); staggered lists accent the first and last item; **one sound family per video** (same whoosh with seeded variants, same click set, tonal effects in the music's key). | [1] |
| S2 | **No game-UI sounds in serious work** (`coin`, `ding`, `success`, `sparkle-up`, `power-up`): they read as cheap. A chart, a filing or a figure gets a `tick`, a `thock`, a low chime a few dB under the bed, or nothing. **[changes EC S6: drop "money = coin"; a register/cash sound only when the money is diegetic, e.g. a till in the scene]**. Prefer low/medium-harshness sounds for anything that repeats (energy > 5 kHz tires). | [1] |
| S3 | **Stem levels before the master:** voice −16 LUFS integrated; music alone −20; **music under voice ≈ −32 LUFS short-term (a 10-14 dB duck, default 12)**; ambience/room tone −32; UI clicks −24 LUFS momentary, peaks ≤ −8 dBFS; foley −22, peaks ≤ −6 dBFS; transitions −18; stingers −16; impacts −14 (the loudest effect, one per moment). Measured narrated documentaries keep the bed **24-31 LU under the voice** with hits ~10 dB under; QA band: **music 18-25 dB under voice, WARN if any voice line is < 8 dB over the bed**. [changes EC S4: bed ≥ 15 LU → 18-25 LU, target 22] | [1] [5] [4] |
| S4 | **Ducking:** depth 12 dB (10-14, up to 16 for dense music); attack 80 ms with a 120 ms look-ahead so the duck is complete when the first word starts; hold 300 ms across pauses inside a sentence; release 0.5 s (0.4-0.8), or up to 2 s so the bed swells only between sentences. Better for continuous narration: **a static bed already 22-24 LU under, no ducking** (avoids pumping; the measured client channel does this). A moderate 6-8 dB duck plus a 1-4 kHz carve sounds fuller than a deep flat duck. | [1] [5] |
| S5 | **Sync:** align the *hit* (transient, loudest pass of a whoosh, end of a riser), not the file start; an entry pop may lead its visual by 0-1 frame; sound never trails the picture by more than 2 frames (66 ms). A success/"confirmed" cue plays when the result is fully visible. | [1] |
| S6 | **Riser → reveal:** riser 1-2 bars long (at 120 bpm a bar is 2 s), its end on the reveal downbeat together with the impact; a reverse cymbal sucks into it. | [1] |
| S7 | **Phone speakers play almost nothing under 300 Hz.** A sub-drop/boom alone is near silent on a phone: layer a mid transient (tick/static/glitch) at −8 to −12 dB on the same hit. QA: the mix above 300 Hz is at most 10 LU under the full mix (FAIL > 18). | [1] [4] |
| S8 | **Master:** −14 LUFS ±0.5 (WARN > 1 LU off, FAIL > 3), true peak ≤ −1 dBTP (keep the owner's −2 dBTP), loudness range ≤ 8 LU; the limiter does 0-4 dB, > 6 dB means lower the hot track instead. Master to WAV and encode once (AAC/MP3 add up to 0.5 dB overshoot). | [1] [4] |
| S9 | **Music per act:** per-section loudness follows the story (quiet setup quieter, the fall louder); a jump > 6 LU between neighbouring sections reads as a mistake unless planned. Emphasis comes from a **cue change or a hit, never from raising the bed**. "No bed in the body, music only at cold open and ending" is a valid, measured choice that makes the open feel bigger. Music starts on frame 1 and ends on a button, never a fade mid-phrase. | [1] [5] [4] |
| S10 | **No accidental silence:** no stretch ≥ 2 s more than 20 LU under integrated loudness, no digital silence ≥ 1 s mid-video (FAIL ≥ 3 s), no sound still ringing on the last frame. Room tone at about −32 LUFS under any dry passage so gaps never sound like dropouts. | [4] [1] |
| S11 | **Typing/ticker clicks are generated from the typing track** (one click per letter actually drawn), not hand-placed times; mark soft UI clicks under the voice as texture. | [1] |

## 8. Narration (AI voice)

| ID | Rule | Source |
|---|---|---|
| N1 | **Rate:** plan at 150 wpm (2.5 words/s) and measure the real take. Bands: documentary 120-150; Kurzgesagt measured 120-130 wpm; a measured spy-documentary channel ~157 wpm; TTS defaults ~165. Wisdrop target **145-160 wpm** measured from Whisper word timings (proposal); outside 130-170 is a WARN. | [14] [21] [5] [S: 23] |
| N2 | **One sentence ≈ one picture.** ~5 s per scene (≈ 12 scenes/min, 10-15 words) as the default; 3-4 s during escalation runs; 6-9 s for maps, diagrams and numbers. A sentence over ~20 words gets two pictures. Quick formula: pictures = seconds ÷ 5; words ≈ seconds x 2.4. | [14] |
| N3 | **Pauses are budgeted:** 0.5-1 s after a question, before its answer (the most valuable pause); ~0.5 s after a number; ~1 s before the final callback line; 0.75-1 s between paragraphs in documentary reads; never after every sentence. A 0.75 s pause costs ~2 words, so cut setup words, not the pause. With TTS: insert explicit breaks rather than hoping the model pauses. | [14] [S: 23] |
| N4 | **The transcript is the edit decision list.** Transcribe the final voice with word timings, convert to frames, and drive every cut and reveal from it: nothing appears before the narration names it; big-line words land on their spoken words; highlighter on the stressed word. Check (proposal): each voice-tied element starts within −2 / +6 frames of its word's start. | [10] [2] |
| N5 | **Cut scenes on places and turns,** 2-6 s each; alternate photo and map (a map when a place is named, a photo when a person or thing is named). | [10] |
| N6 | **Read-back the AI voice:** re-transcribe the final take and compare names, acronyms and numbers with the script; a mismatch on a name in the title or lexicon is a FAIL (fix the pronunciation, regenerate the line). | [4] |
| N7 | **Even voice:** normalise every line to the same loudness (BS.1770) so the voice's loudness range stays ~2.5-3 LU; a quiet bed only works over a steady voice. | [5] |
| N8 | **Reading budget when on-screen text is *not* spoken:** hold = 0.3 s + max(chars/17, words/3) s, ≥ 1 s (phone check); showtime's text-only rule max(1.0, 0.5 + chars/13) s is stricter and matches EC T1. Text read along with the voice is exempt. | [4] [2] |

## 9. Storytelling and retention

| ID | Rule | Source |
|---|---|---|
| H1 | **Deliver on the click within 5-10 s,** preferably *visually*: show what the thumbnail/title promised (Paddy finds visual confirmation outperforms verbal). Frame 0 is the poster: hook complete at t = 0, not black, not a logo; first change by 2 s. | [8] [4] |
| H2 | **Intrigue sentences must be specific:** "he discovered something in October 2017 that changed everything", not "keep an eye out for step five". Statement first, then the intrigue line. | [8] |
| H3 | **Seamless flow:** no signpost sentences ("let's get into it", "let's get started", "in today's video"); bridge straight in ("starting with..."). | [8] |
| H4 | **Foreshadow overtly with "soon X, first Y":** "later I'll show you the account he hid it in, but first..."; both X and Y must be interesting. Plant retention devices on a one-page skeleton before scripting (e.g. a foreshadow in the first 2 min, a curveball around 5-6 min). Focus-group test: pause at any minute; a viewer should be able to say what is coming. | [8] |
| H5 | **Satisfaction beats stringing along:** YouTube optimises viewer satisfaction first, then duration; never pad. **No YouTube chapters on narrative videos** (they let viewers skip to the payoff); chapters only for listicles/tutorials. Use on-screen chapter cards instead. | [8] |
| H6 | **Front-load effort:** the first minute gets 20-30 % of editing time, not 10 %. Audit the whole video in 15 s windows: every window must move the story. | [S: 8b, 8c] |
| H7 | **Long-form structure:** chapters of 90 s-2.5 min, each with its own one-line hook (a sub-question) and its own small payoff, ending on a line that points at the next question. | [14] |
| H8 | **Packaging test before scripting:** if an idea cannot be packaged in a title + thumbnail, it is not a YouTube idea yet; contradiction titles ("...but nobody will buy it") create the "why?". | [8] |
| H9 | **Ending:** the final frame is a designed hold (≤ 4 s still; longer is a WARN) landing on a button in the music. | [4] |
| H10 | **Sound-off test:** watch once at full speed muted; if the pictures tell the story without the voice, the cut is right. | [10] |

## 10. Code-workflow practices

| ID | Rule | Source |
|---|---|---|
| W1 | **Every pixel is a pure function of (episode data, frame index).** No wall-clock time, no unseeded randomness, no accumulators (`x += v` across frames), no state flipped in callbacks. Remotion renders frames out of order on several workers, which is why it ships `random(seed)` (mulberry32 over a string hash) and an ESLint rule against `Math.random()`. Python equivalent: `rng = np.random.default_rng(zlib.crc32(f"{episode}:{element_id}:{frame}".encode()))`. **Never use Python's built-in `hash()` for seeds** (salted per process, so two runs differ). True randomness is allowed only in a one-off planning step whose output is saved to JSON (Remotion's `calculateMetadata` exception). | [11] [2] |
| W2 | **Determinism tests:** render the same frame twice → identical bytes; render a late frame, then an early one → the early frame identical to a forward render; probe ~12 frames across the episode and store their hashes. | [4] |
| W3 | **Data-driven scenes:** shots.json is validated against a schema with defaults (Remotion: default props define the data shape; a schema validates it); durations, sizes and fps are computed once from the data before rendering (the `calculateMetadata` pattern), never inside the frame loop. Render one episode at a time: each render already uses every core. | [13] |
| W4 | **Caching:** memoise expensive pure work (cut-outs, halftones, map rasters, text layouts) with a cache key = content hash of inputs + code version (`functools.lru_cache` in-process, files on disk across runs); never re-fetch external data during a render; procedural textures (grain, leak, vignette) are generated by code, not downloaded overlay packs. | [S: 25] [10] |
| W5 | **Template library with named tokens:** easing and duration tokens (M1/M2) and per-element verbs (E0) live in one module; components expose sync points (`countup.land`, `stamp.hit`, `cursor.click`) and the sound layer places effects on those times instead of guessing. | [2] [6] |
| W6 | **Sub-pixel motion:** animating integer positions makes slow eases stutter (showtime: layout properties snap to whole pixels). In Pillow use affine transforms with float offsets, or supersample 2x and downscale, for any move slower than ~1 px/frame (proposal derived from [2]). | [2] |
| W7 | **Contact sheets for review:** 1 frame per second, plus stills at the hook, every reveal, every cut (cut − 0.1 s and cut + 0.2 s) and the last second; review the sheet at phone size (~360 px wide for 16:9). | [4] [10] |
| W8 | **Delivery file:** H.264 High, yuv420p, BT.709 tags, +faststart, AAC 48 kHz stereo, constant 30 fps; duration = planned ± 1 frame; audio length within 1 frame of video; master flat motion graphics at CRF 14-16. | [4] [3] |
| W9 | **Prove each check fires:** before adding a QA rule, add a planted-defect fixture (a tiny clip that must FAIL it). | [4] |
| W10 | **Agents cannot listen:** numeric audio checks are necessary, not sufficient; a human listens once on laptop speakers and earbuds (hook, reveal, end) before publishing. | [1] [4] |

---

## Checks to add to code

Each line: check name → threshold → rule ID. All run on the rendered frames/stems or on shots.json;
"WARN" prints and continues, "FAIL" blocks the render or the package step.

**Picture**
1. `palette_literals` → any hex/RGB literal outside the palette module = FAIL → C1
2. `accent_area` → per keyframe accent pixels (ΔE2000 < 10) between 0.3 % and 15 % of frame, else WARN → C2
3. `contrast_real_pixels` → text vs its local background ≥ 4.5:1 (≥ 3:1 at ≥ 76 px), sampled at settle frame and mid-transition; FAIL below → C3
4. `pure_black_white` → > 20 % of frame at exactly 0 or 255 luma = WARN → C4
5. `act_ground_delta` → neighbouring acts' ground ΔE2000 < 15 = WARN → C8
6. `grain_consistency` → flat-patch luma std outside ±25 % of episode median = WARN; std ≈ 0 (no grain) = FAIL → T1
7. `banding` → in dark gradients, count of distinct luma steps per 100 px < 8 after encode = WARN (proposal) → T2, T9
8. `light_leak_count` → > 1 leak per scene or leak alpha > 0.40 or leak over caption band = WARN → T4
9. `step_contrast` → if stepped (on-twos) layers exist, camera and caption layers must not be stepped = WARN → T6
10. `safe_area` → any text box outside 96/54 px insets, or small text (< 48 px) in the bottom 8 % = FAIL → L1
11. `text_size` → text < 25 px = FAIL; headline role < 76 px or body < 36 px = WARN → L2
12. `eye_trace_jump` → focus distance across a cut > 25 % of width without `jump` tag = WARN → L3
13. `focal_count` → > 2 declared focal elements in a shot = WARN → L6
14. `labels_crowded` → label boxes closer than 0.15 em = WARN → L7
15. `upscale` → any source drawn > 1.5x its native pixels = WARN → V5
16. `hold_push` → any shot with no element change for > 2 s and camera scale rate < 0.8 %/s = WARN (≥ 6 s with no change = FAIL, EC P1 stays stricter at 2.5 s) → V2
17. `map_flights_adjacent` → two map-flight shots in a row = WARN → V4
18. `map_is_process` → a map shot with no fill/marker/stamp change = WARN → E1
19. `montage_timing` → montage items outside 15-45 frames or a montage run < 10 items = WARN → E2
20. `snap_budget` → > 3 snap/whip/blur beats per video or blur on a text layer = WARN → E8, V8
21. `easing_tokens` → any tween using an ease not in the token table, or `linear` on a spatial move = WARN → M1
22. `duration_bounds` → entrances outside 0.3-0.6 s (UI 0.1-0.3 s), exits longer than their entrance = WARN → M2
23. `overshoot_on_text` → spring damping ratio < 1 or back-ease on a text block = WARN → M3
24. `stagger_cap` → a group's total stagger > 0.5 s = WARN → M5
25. `dead_stop` → move with ≥ 6 frames of change ending at ≥ 50 % peak speed then ≥ 4 still frames = WARN → M9
26. `flash_risk` → > 3 flashes in any 1 s window (≥ 0.1 linear-luminance change over ≥ 25 % of frame) = FAIL → M10

**Sound**
27. `voice_over_bed` → any voice line < 8 dB over the bed = WARN; whole-mix voice-to-music outside 18-25 dB = WARN → S3
28. `sfx_family` → SFX files from > 1 family tag, or any file tagged `game_ui` (coin/ding/success) = WARN → S1, S2
29. `sfx_sync` → effect hit later than its visual event by > 2 frames = FAIL; earlier by > 2 frames (except whoosh into cut) = WARN → S5
30. `speaker_gap` → integrated loudness above 300 Hz more than 10 LU under full mix = WARN, > 18 = FAIL → S7
31. `loudness_master` → integrated −14 ±1 LUFS, TP ≤ −2 dBTP (owner), LRA ≤ 8 LU, limiter gain reduction ≤ 6 dB → S8
32. `level_jump` → > 6 LU change across a cut not marked as a planned music change = WARN → S9
33. `quiet_stretch` / `silent_gap` → ≥ 2 s at > 20 LU under integrated = WARN; digital silence ≥ 1 s = WARN, ≥ 3 s = FAIL; audible sound in last 0.2 s = WARN → S10

**Narration and story**
34. `wpm` → measured voice rate outside 130-170 wpm = WARN → N1
35. `sentence_picture` → a sentence > 20 words spanning one picture = WARN → N2
36. `reveal_pause` → a `?` line followed by an answer with < 0.5 s gap = WARN → N3
37. `word_sync` → voice-tied element starting outside −2/+6 frames of its word = WARN; element appearing before its word is first spoken = FAIL → N4
38. `readback` → re-transcribed names/numbers differ from script = WARN; title/lexicon name differs = FAIL → N6
39. `voice_lra` → voice stem loudness range > 4 LU = WARN → N7
40. `frame0` → frame 0 black, flat or a logo = FAIL; first visual change after 2 s = WARN → H1
41. `signpost_phrases` → script contains "let's get into it / let's get started / in today's video / don't forget to" = WARN → H3
42. `final_hold` → still ending > 4 s = WARN → H9

**Workflow**
43. `determinism` → frame N rendered twice, and N after N+500, must be byte-identical; 12 probe hashes stored per episode → W1, W2
44. `seed_source` → any use of `random.random`, `np.random.rand` without a passed seed, `time.time()` or built-in `hash()` inside render code = FAIL (lint) → W1
45. `delivery_spec` → codec/pix_fmt/BT.709 tags/faststart/48 kHz/duration ± 1 frame → W8

## Conflicts with EDITING_CRAFT to resolve (owner decision)

- **EC S6 "money = coin/register"** vs S2 here (game-UI sounds read cheap): recommend dropping coin.
- **EC T3 headline 72 px** vs L2 here (7 % of height = 76 px): recommend 76.
- **EC S4 bed ≥ 15 LU under voice** vs S3 (measured 24-31; QA band 18-25): recommend 22 LU target.
- **Punch-ins:** showtime says never in explainers, the Vox/JH look uses them; V3 limits them to stepped snap beats.
- **Grain strength:** showtime 1.5-3 % (clean) vs Daena JH 0.35 (stylised); pick one per series and lock it (T1).
- **Sound density:** showtime allows only 1-3 cues in a whole explainer; the JH paper style leans on paper thuds and shutters. S1 resolves it as "sound what matters, one family, 2-4 big moments".

## Sources

1. showtime docs, "Sound design: density, families, alignment, ducking and loudness targets" (v0.4.6) https://faviovazquez.github.io/showtime/docs/sound-design.html [R]
2. showtime docs, "Motion craft: easing, timing, stagger, holds, camera moves and what reads as cheap" https://faviovazquez.github.io/showtime/docs/motion-craft.html [R]
3. showtime docs, "Color: palettes, contrast, banding, grading" https://faviovazquez.github.io/showtime/docs/color.html [R]
4. showtime docs, "QA: acceptance checklists and the critic pass" (rule table, phone check, thresholds) https://faviovazquez.github.io/showtime/docs/qa.html [R]
5. Kevin Tabares / Umbrella Creators, "How loud should background music be under a YouTube voiceover?" (EBU R128 measurements of three narrated documentary channels, 2026-09-26) https://umbrellacreators.com/blog/background-music-volume-under-voiceover [R]
6. IBM Carbon Design System, "Motion" (easing curves, duration tokens) https://www.carbondesignsystem.com/building-blocks/foundations/motion/overview [R]
7. Material Design 3, "Easing and duration: applying" https://m3.material.io/styles/motion/easing-and-duration/applying-easing-and-duration [R]; token cubic-bezier values from the tokens page https://m3.material.io/styles/motion/easing-and-duration/tokens-specs [S]
8. Paddy Galloway on Sweat Equity, "The New Rules Of YouTube In 2026" (notes + full transcript, 2026-02-18) https://pod.wave.co/podcast/sweat-equity/the-new-rules-of-youtube-in-2026-w-paddy-galloway [R]; 8b. Colin & Samir transcript ("first minute gets 20-30 % of attention") https://thetranscriptdesk.substack.com/p/the-new-rules-of-youtube-2025-edited [S]; 8c. Paddy Galloway on X (15-second interval breakdown) https://x.com/PaddyG96/status/1525457921022238720 [S]
9. FCPX Full Access, "How to Get the Vox / Johnny Harris Documentary Style" (on-twos stutter, frame-rate table, cut-out stroke/shadow, imperfection, 2026-09-08) https://fcpxfullaccess.com/blogs/blog/vox-johnny-harris-documentary-style-final-cut-pro [R]
10. Daena Digital, "Grain and map: documentary explainer video style (after Johnny Harris)" agent skill v2.1 (frame-by-frame study every 0.5 s) https://daenadigital.com/resources/skills/grain-and-map [R]
11. Remotion docs, "Using randomness" https://www.remotion.dev/docs/using-randomness [R]; `random()` source (mulberry32) https://github.com/remotion-dev/remotion/blob/main/packages/core/src/random.ts [S]
12. Remotion docs, `spring()` defaults (mass 1, damping 10, stiffness 100) https://www.remotion.dev/docs/spring [S]
13. Remotion docs, `calculateMetadata()` and dataset rendering https://www.remotion.dev/docs/calculate-metadata , https://www.remotion.dev/docs/dataset-render , https://www.remotion.dev/docs/parameterized-rendering [S]
14. StickTale, "How Many Scenes per Minute in an Explainer Video? A Pacing Guide With the Math" (2026-10-22) https://sticktale.com/blog/explainer-video-pacing [R]
15. EBU R 95, "Safe areas for 16:9 television production" https://tech.ebu.ch/docs/r/r095.pdf and pixel calculator https://winberg.ie/tools/safe-areas ; SMPTE ST 2046-1 summary https://mediascaleup.com/post/how-to-get-title-safe-and-action-safe-areas-right-motion [S]
16. Walter Murch, "The Rule of Six" (In the Blink of an Eye, pp. 17-20) https://blogs.ischool.berkeley.edu/i290-viznarr-s12/the-rule-of-six-walter-murch and Murch on quadrants, Web of Stories https://www.youtube.com/watch?v=s49Al2CMfTI [S]; No Film School on eye trace in fast video https://nofilmschool.com/2018/08/editing-eye-trace-mind-rule-six-incorrect [S]
17. Nielsen Norman Group, "Using Color to Enhance Your Design" (60-30-10) https://www.nngroup.com/articles/color-enhance-design [S]
18. MoMA audio, "Colorscript, Toy Story 1995" (Lasseter on Eggleston's colour scripts) https://www.moma.org/audio/playlist/192/2581 [S]
19. Motion Canvas docs, "Tweening" (easeInOutCubic as property-tween default) https://motioncanvas.io/docs/tweening [S]
20. 3Blue1Brown manim, `rate_functions.py` (`smooth`) https://github.com/3b1b/manim/blob/master/manimlib/utils/rate_functions.py [S]
21. "A Comparative Study of Visual Learning Design in Popular Science Educational Videos: Kok Bisa? and Kurzgesagt", European Journal of Education and Pedagogy (2026) https://eu-opensci.org/index.php/ejedu/article/view/70181 [S]
22. "Edit Like MagnatesMedia in CapCut" transcript (per-episode colour themes) https://ytscribe.com/v/EDZl5Mdl7Tw [S]
23. Vois, "Documentary Pace: Letting the Story Breathe" (750-1000 ms paragraph pauses) https://vois.so/blog/documentary-narration-pacing [S]
24. Motion Array, "Edit Documentaries in Premiere Pro: 3 Johnny Harris Style Tips" (8-frame montage items, shutter clicks) https://motionarray.com/learn/premiere-pro/edit-documentary-in-premiere-pro/ [S]
25. Remotion docs, "Performance Tips" (memoisation, data-fetch caching, concurrency) https://www.remotion.dev/docs/performance [S]

Not established: no source read gave numeric rules for halftone cell size or exact wobble amplitudes
(T7, T10 are proposals); no read source gave Coffeezilla-specific numbers; Kurzgesagt's colour process
is only described qualitatively in what I could reach.
