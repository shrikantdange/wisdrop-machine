# Wisdrop editing craft (v3): what the best explainer editors do, turned into machine rules

Researched 2026-11-03. Every rule has an ID; the IDs marked **[check]** are enforced in code by
`machine/craft_check.py` (free, CPU, runs before every render). The rest guide the operator AI when
it writes `shots.json`. Sources are listed at the end; [R] = page read in full, [S] = seen in search
results only (lead, not proof).

## 1. The style we are copying (and what we are not)

- **Collage, not slideshow.** The Vox/Johnny Harris look is a paper collage on a textured board:
  cut-out photos with white sticker borders and soft shadows, halftone dots, tape, ONE accent colour
  carried through every frame, bold condensed type [2][3]. If a frame could be a movie still it is
  wrong; if it could be a magazine spread it is right [2].
- **Motion carries information, never decoration.** The single rule that separates pro from
  amateur Vox-style work: every animated element answers a question the narrator just raised [4].
  A map appears because a place is named; a highlighter lands on the word being stressed [4][1].
- **One picture worked over beats five cards in a row**: hold a photo as a stage and move the camera
  inside it, draw marks on it, point at relationships [6].
- **Maps** answer a specific question the voice raises: zoom, brush-stroke border highlight, labels
  on cue, route line drawn in time with the sentence [4][7].
- **Desk-explainer pacing (Johnny Harris):** evidence on the desk/board, the camera "looks" at each
  piece as it is named; textured maps; Retro typer text [7][8].
- **Faceless money-crime storytelling (Magnates/Coffeezilla):** set up the fall inside the first 30 s,
  then earn it; cliffhanger at every chapter edge; documents and sources stacked on screen [9][10].
- **Kurzgesagt/TED-Ed:** script is the backbone; storyboard visual metaphors before drawing; an
  illustration library is reused but each film gets a unique look [11].

## 2. Pacing and attention

| ID | Rule | Source |
|---|---|---|
| P1 **[check]** | Nothing on screen holds still for more than **2.5 s**. Every shot must have a visual event (element enters, highlight, count-up, camera move change, marker stroke) at least every 2.5 s. Continuous moves (route drawing, ticker, chat typing) count. | habituation after ~5 s static [12]; "nothing still for more than 1.5 s" in paper-collage practice [6]; owner rule |
| P2 **[check]** | First 60 s: a **cut or major visual change every 1.5-3 s**. Hooks cut every 3-5 s at most [13]; collage editorial rhythm cuts every 1-3 s with narration beats [5]. |
| P3 | After the first minute, pattern interrupts vary in type (map, phone, document, stat, kinetic word, sound drop) and land where attention dips: topic changes, numbers, long same-type runs. Never the same interrupt type 3 times in a row. | [12][13][14] |
| P4 **[check]** | Same shot type never 3 times in a row (except `kinetic` beats that are one sentence). | [14] (interrupts must vary or they become the pattern) |
| P5 | One idea per screen; at most 3 things start moving at the same moment. | [15] |

## 3. Hook, open loops, structure (mapped to our 6 beats)

| Beat | Machine rule |
|---|---|
| **Hook** (0-30 s) | H1 **[check]** shock fact or striking visual inside **5 s** (a `stat`, `map` route, `phone`, `stamp` or `photo` shot must start by 5.0 s). H2 **[check]** a question line (`preset: question` or text ending `?`) by **8 s**; if the approved script cannot, the check prints REVIEW and the hook bank offers rewrites for the owner. H3 a promise (what the viewer will learn) by 15 s. No greeting, no logo, no "in this video" [16]. |
| **Setup** | Open a smaller loop right before any slow context section [17]. |
| **Rise** | Escalate with numbers and comparisons to familiar scale [2]; money counter climbs. |
| **Twist** | Re-hook near 40% of runtime: change board colour/visual style and raise stakes [17]. |
| **Fall** | Documents, court filings, stamps. Riser into the reveal, cut to silence, impact on the reveal frame [18]. |
| **Aftermath** | Return to the cold open with new meaning; last line quotable [2]. Close the main loop only in the last 10% [17]. |

- L1 **[check]** at least one open question (a `?` line) per part (between chapter cards) [17].
- L2 the last 5 s of every chapter opens the next loop; first 5 s of a chapter is a mini cold open [17].
- Open loops are promises: never tease what the video will not pay off [17].

## 4. Words on screen (kinetic type, labels, captions)

| ID | Rule | Source |
|---|---|---|
| T1 **[check]** | Reading time: text that is not spoken word-for-word must stay settled for at least **1 s per 13 characters** (2.3 s for a 30-character line); minimum 0.8 s for any label. | [19][15] |
| T2 | Max ~30 characters per line, max 3 lines per text block. | [19] |
| T3 | Body text >= 40-60 px at 1080p (phone legibility); titles >= 1.5x body. Our minimums: labels 34 px, body 40 px, headlines 72 px+. | [19][15] |
| T4 | Entrances 0.25-0.6 s, exits faster; motion ends, then text holds; never wobble readable text. | [15][20] |
| T5 | One emphasised word per card (the highlighter word), timed to the narrator's stress. | [1][4][20] |
| T6 **[check]** | Captions never overlap a card: cards and kinetic text keep out of the caption band (y > 900 px). | owner rule |
| T7 | Count-ups ease out, land on a beat, label appears after the number. | [20] |

## 5. Sound design layers

| ID | Rule | Source |
|---|---|---|
| S1 | Four layers: voice, music, effects, ambience/room tone. Voice first. | [21] |
| S2 | Whoosh peaks ON the cut (starts a few frames early); riser ends exactly on the reveal, often by stopping dead; impact on the reveal frame. | [18][21] |
| S3 | Effects: on the contact frame or one frame early, never two (ITU sync window ~45 ms early). | [21] |
| S4 | While the voice speaks, effects sit **4-10 dB under** it; ambience beds >= 15 LU under voice. Place effects in the gaps between words. | [21] |
| S5 | Fewer than you think: sound the cuts that carry meaning; never more than 2 same-kind sounds at once (Murch's law of two-and-a-half). | [18][21] |
| S6 | Each element type has its own sound (phone = buzz/ding, map = whoosh+marker, money = coin/register, stamp = stamp, photo = shutter/tape, page = page turn). | [21] (sound tells what the picture does not) |
| S7 **[check]** | Master -14 LUFS integrated, true peak <= -2 dBTP (owner rule; -1 dBTP is the common online ceiling [18]); voice RMS always above music RMS while speaking. | [18][21] |
| S8 | J-cuts: the next part's music/ambience may start up to 0.75 s before the picture changes. | [22] |

## 6. Colour script per act

- Each part gets its own board colour (navy, warm off-white, sky blue, charcoal) so the viewer
  feels the act change; the accent (highlighter yellow, marker red) never changes [2][4].
- Pictures inside a part share the part's duotone; time of day still sets photo mood.

## 7. Thumbnails and titles

| ID | Rule | Source |
|---|---|---|
| K1 | Thumbnail: one clear idea, rule of thirds, not too complex, as large as possible on all devices; text in an easy font. | YouTube Help [23] |
| K2 | 3-5 words of bold text that ADD to the title, never repeat it. | [24][25] |
| K3 | Title: accurate, short, important words first; limit ALL CAPS. Searchable vs intriguing titles are both valid. | [23] |
| K4 **[check in package]** | Every thumbnail is checked at phone size (246x138 px preview) for legibility. | [23] |
| K5 | No real person's face is drawn (channel rule); emotion comes from objects, contrast and a fictional composite. | owner rule |

## 8. Licences for pictures, vectors, sound

- Allowed: CC0, public domain, CC BY, CC BY-SA, MIT, ISC, Apache 2.0. Refused: NC, ND, "editorial
  only", unknown. Every non-CC0 asset is credited on screen (photos) or in the description.
- Free sound libraries: check each file; NonCommercial is not allowed for a monetised channel [21].
  Our own synthesised sounds (tools/synth_sfx.py) are CC0.

## Sources
1. TypeFlow, "How to Get the Vox Explainer Look" (2026-09-13) https://www.typeflow.studio/blog/vox-style-explainer-videos [S]
2. CK42BB, vox-explainer-skill, "Vox Style Guide" https://github.com/CK42BB/vox-explainer-skill/blob/main/references/vox-style-guide.md [R]
3. Kapwing, "How to Make Vox-Style Animations" (2026-10-10) https://www.kapwing.com/resources/how-to-make-informational-videos-like-vox/ [S]
4. EarnEdits, "How Vox-Style Edits Are Built" (2026-08-03) https://earnedits.com/how-vox-style-edits-are-built [R]
5. Calliope, "Vox Style Video prompt pack" (2026-08-26) https://www.calliopelabs.co/guides/vox-style-shorts [S]
6. Daena Digital, "Paper studio: collage explainer video style" https://daenadigital.com/resources/skills/paper-studio [S]
7. Johnny Harris, "How I Make My Maps" (2020) https://www.youtube.com/watch?v=GsojLuJpe_0 and Glasp summary https://glasp.co/youtube/GsojLuJpe_0 [S]
8. Valentin Macke, art direction for Johnny Harris https://vmacke.com/johnny-harris [S]
9. Faceless.my, "Channels like MagnatesMedia" (2026-05-18) https://faceless.my/youtube/channels-like-magnatesmedia/ [S]
10. Trustfull, "YouTube channels about fraud" (Coffeezilla) https://trustfull.com/articles/top-12-youtube-channels-about-fraud-scams-financial-crime [S]
11. Kurzgesagt, "Our video process" https://kurzgesagt.org/what-we-do and "How to Make a Kurzgesagt Video in 1200 Hours" https://www.youtube.com/watch?v=uFk0mgljtns [S]
12. Teyro, "Retention Editing Masterclass" (2026-09-01) https://teyro.app/blog/retention-editing-masterclass [S]; Search Engine Land, audience retention guide https://searchengineland.com/guide/audience-retention [S]
13. Retention-editing skill (pacing by section) https://github.com/gutidev-cl/skills-founder/blob/main/youtube/retention-editing/SKILL.md [S]
14. Prepublish, "YouTube Pattern Interrupts" https://prepublish.ai/guides/youtube-pattern-interrupts [S]; Vanpelt Studio, "Pattern interrupts" https://vanpelt.studio/learn/retention/pattern-interrupts/ [S]
15. showtime docs, "Pacing" and "Typography for video" https://faviovazquez.github.io/showtime/docs/pacing.html , https://faviovazquez.github.io/showtime/docs/typography.html [S]; Motion Cheat Code, kinetic typography https://motioncheatcode.com/glossary/kinetic-typography/ [S]
16. Prepublish, "The First 30 Seconds of a YouTube Video" (updated 2026-10-17), citing YouTube Help answer 9314415 https://prepublish.ai/guides/first-30-seconds [R]
17. Asendify, "Open Loops in Video Editing" (2026-10-21) https://www.asendify.co/blog/open-loops-video-editing/ [R]
18. Opus Sounds Directory, "Whoosh, Riser and Transition Sound Effects" (2026-10-06) https://opussounds.directory/blog/whoosh-and-transition-sound-effects-for-video-editing [R]
19. legibility.info (DBSV), "Rules for text in videos" https://legibility.info/rules-for-text-in-videos [R]
20. SkillMedev, kinetic typography skill https://github.com/SkillMedev/motion-video-direction/blob/main/skills/kinetic-typography/SKILL.md [S]
21. Mustafa Zuhuri, "Sound effects for video: choose them, time them, sit them under the voice" https://zuhuri.com/learn/stories/sound-05-sound-effects/ [R] (cites Murch, ITU-R BT.1359, Torcoli et al. 2019)
22. Adobe, "J cut and L cut" https://www.adobe.com/creativecloud/video/post-production/cuts-in-film/l-and-j-cut.html [S]; Soundstripe, "A Video Editor's Guide to J Cuts and L Cuts" https://www.soundstripe.com/blogs/a-video-editors-guide-to-j-cuts-and-l-cuts [S]
23. YouTube Help, "Thumbnail & title tips" https://support.google.com/youtube/answer/12340300 [R]
24. vidIQ, "YouTube Thumbnail Design Tips" (updated 2026-07-14) https://vidiq.com/blog/post/youtube-thumbnail-design-tips [S]
25. YouTube Blog, podcast thumbnail guidance (3-5 words) https://blog.youtube/creator-and-artist-stories/the-definitive-guide-to-creating-engaging-podcast-content/ [S]
