# WISDROP PLAYBOOK v3 (2026-11-03)
The creative rulebook for every Wisdrop video: what to make, and how it should look, sound and feel.
The companion file WISDROP_AI_INSTRUCTIONS.md covers how to build it (setup, tools, code, step by step).
If a rule here and a habit somewhere else disagree, this file wins.

---------------------------------------------------------------------
## 0. THE CHANNEL IN ONE PARAGRAPH
Wisdrop (@Wisdrop) is an English, faceless YouTube channel for a global audience. Tagline: "Money crimes behind the hype."
Each video tells one real financial fraud, scam or bubble, using only facts backed by regulators, courts or major outlets. One unseen narrator explains it like a smart friend over coffee: calm, clear, dry and a little sarcastic about the schemers, never about the victims.
Visuals: editorial flat-vector illustration (story scenes) plus clean code-built evidence cards (real numbers with sources).
Philosophy: **simple, clear, a little sly.** Quality comes from the story and the voice, not from busy screens. If something costs a lot of effort or makes the viewer work harder, cut it.

---------------------------------------------------------------------
## 1. THE GOLDEN RULE: SAY IT, SHOW IT
**What the narrator says and what the viewer sees must be the same thing, at the same moment.**
- Every script line is written WITH its visual. No line exists without a [VISUAL] cue, and no visual without a line.
- The visual shows the noun or action of the line literally:
  - "irons his newspaper" means Ray ironing a newspaper, not Ray holding coffee.
  - "every screen said AI" means screens showing AI, not a person on a street.
  - "Gordon Gekko would ask for a second opinion" means a nod to the joke (a doctor's clipboard reading "250x", or the number with a raised eyebrow), not a random factory shot.
- Every number spoken is the number on screen, in the same form ("eight thousand times" shows "8,000x").
- The cut happens on the line. Shot changes are timed from the real voice timing, not from estimates. A visual may lead the line by up to 0.15 s, never lag it.
- If no fitting image exists for a line, rewrite the line or make the image. Never "close enough".
- QA test: mute the video and read the captions. Every frame should still make sense with its caption.

---------------------------------------------------------------------
## 2. MACRO: WHAT EVERY EPISODE IS
- Length 12-13 min, about 2,100-2,200 words, voice paced at 165-172 WPM.
- One real case, one human we follow from start to end, one clear lesson.
- Weekly upload, same day and time. From episode 3, 2-3 Shorts cut from each episode.
- No logo intro or sting. The video starts on story within the first second. Branding is a small corner mark only.

### 2.1 Story shape (always these 5 parts)
| Part | Time | Job |
|---|---|---|
| Cold open | 0:00-0:30 | The most shocking real moment, the real number on screen by 0:10, who got hurt by 0:20, the big question by 0:30 |
| Part 1: The Dream | 0:30-3:00 | Why normal people believed it. Meet our human. |
| Part 2: The Machine | 3:00-7:00 | How the trick worked. 2 real cases. Mid-point twist around 6:30 (a sourced regulator finding). |
| Part 3: The Fall | 7:00-10:30 | The crash, the fines, the human cost. |
| Part 4: The Lesson | 10:30-12:30 | 3 red flags anyone can spot, payoff of the cold-open question, a 1-line tease of the next case. |
- Each part ends on one open question (about one every 2 minutes).
- Chapter cards: a 2 s card at the start of each part ("PART 1 / THE DREAM"). Simple, no animation tricks.

---------------------------------------------------------------------
## 3. SCRIPT RULES (micro)
- Sentences of 8-14 words. Every 4-6 sentences, one short punch of 2-4 words ("On a promise." "Gone.").
- Link beats with "but / so / then", never "and then".
- Speak to "you" about once a minute ("If you bought in July...").
- Every big number gets one plain, sourced comparison.
- Max 3 numbers on screen per minute.
- Write numbers for the voice the way they are said ("eight thousand times"), and show them as figures on screen ("8,000x").
- Read it aloud. If you need a breath mid-sentence, split the sentence.
- Never: stock tips, "this market is rigged" claims, caricature of real executives, made-up quotes, unsourced numbers.

### 3.1 Script format (mandatory)
Every line is one row:
```
[ID] [PART] VO: "spoken line"
      VISUAL: exactly what is on screen (shot type + who/what + action)
      ON-SCREEN TEXT: number/label (or none)
      SOURCE: outlet, date (for any fact)
      VOICE: facts | tension | beat | dry   (emotion preset, see 8.3)
      SFX: none | name (only on actions and numbers)
```
Example:
```
[08] [P1] VO: "Meet Ray. Retired, careful, the kind of man who irons his newspaper."
      VISUAL: STORY. Ray's kitchen, morning. Ray carefully ironing a folded newspaper, glasses on.
      ON-SCREEN TEXT: none
      VOICE: facts
      SFX: none
```

---------------------------------------------------------------------
## 4. TONE: SARCASM, WIT AND POP CULTURE
- Dose: one wry line about every 90 s (8-10 per episode). One pop-culture reference per part (5 max). Never two jokes in a row.
- Aim at the scheme, the greed, the absurd numbers. Never at victims. Never at a real person beyond documented facts.
- Style: dry understatement, not punchlines. The voice stays straight; the line does the work.
- Lines that fit:
  - "That's not a queue. That's a Black Friday stampede."
  - "A company with no product, and a stock up 400%. Totally normal stuff."
  - "The chip was 'in mass production.' The mass production was a press release."
  - "Even Gordon Gekko would have asked for a second opinion."
  - "It's the Monopoly rule: the game goes on until someone checks the bank."
  - "Spoiler: the regulators did read the comments."
- Pop-culture rules: words only. Never use clips, songs, character images or logos. Pick globally known, long-lived references (Titanic, Monopoly, Wolf of Wall Street, Gordon Gekko, Squid Game, Game of Thrones, Marvel, Black Friday, Sherlock Holmes, magic tricks). Avoid fast-dating memes, politics and religion.
- Each joke line still gets a matching visual (Rule 1).

---------------------------------------------------------------------
## 5. CHARACTERS (new cast per story)
- Each episode gets its own cast, designed for that story. Characters repeat only when a story needs them (for example a recurring archetype or a sequel).
- Cast size: 2-4 characters per episode.
  - THE HUMAN (the saver or victim we follow)
  - THE PROMOTER (the scheme's face)
  - Optional: THE HYPE VOICE (influencer or salesman)
  - Optional: THE SKEPTIC (investigator or regulator stand-in)
- All characters are FICTIONAL composites. They never look like real people, never wear real logos, and are never named after real people.
- Real people and companies are referenced in narration and on evidence cards only, never drawn as characters.
- Characters NEVER speak (no lip-sync). They act through pose, expression and props.

### 5.1 How every character must look (house style)
- Adult proportions, about 7 heads tall. Realistic hands. Calm, believable faces (no cartoon eyes or big heads).
- Flat-vector shapes with restrained realism: 2-3 flat tones per material, one hard shadow shape, subtle paper grain.
- Palette: clothing in muted navy, charcoal, beige, olive, rust or burgundy. One signature colour accent per character (for example a gold tie on the promoter, a red pen on the skeptic).
- One signature prop per character (mug, gimbal phone, folder, red pen), kept in most shots.
- Clear silhouette: each character must be recognisable as a black shape.
- Fixed heights across all shots (record each in the cast sheet). Adults are 0.80-0.95 of frame height in a full-body shot.
- Each character needs: 1 master sheet (front, 3/4, side, back, 3 face expressions), then poses as needed by the script (usually 4-8 per character).
- Expression set: neutral, hopeful, excited, worried, shocked, sly, thinking, defeated. Make only the ones the script uses.

### 5.2 Cast sheet (write one per episode)
```
NAME | ROLE | AGE | BUILD | HAIR | OUTFIT | SIGNATURE COLOUR | PROP | HEIGHT (frame %) | PERSONALITY IN 5 WORDS
```

---------------------------------------------------------------------
## 6. VISUAL STYLE (locked: EDITORIAL)
- Look: calm, adult editorial flat-vector illustration, like a serious magazine feature. Hard-edged shadows, low cinematic angles, soft window or lamp light, subtle paper grain.
- Base palette:
  - Navy #10182A (backgrounds, night)
  - Charcoal #1E1E22
  - Amber/gold #ECB840 (hype, money, highlights)
  - Off-white paper #F4EEE0 (documents, cards)
  - Red #E84038 (fraud, losses, falls only)
  - Grey #969EB0 (labels, sources)
  - Green: rarely, tiny accents only.
- One grade on every shot: lifted navy blacks, warm highlights, saturation -6%, film grain plus soft vignette. Never change it per shot.
- Never in images: text or letters (add text in code), real logos, real faces, gore, guns aimed at camera, sexual content, flags as targets.
- Story shot = AI image plate (background) + character cutouts (transparent PNG) + small code-made props or effects. Three depth layers: plate, character, foreground prop.
- Every story shot carries a small "DRAMATISATION" tag (top-left).
- Corner mark: "WISDROP" bottom-right, 34 px, 30% white.

### 6.1 Sets (backgrounds)
- Built per episode from the script: 4-6 sets per episode (for example kitchen, trading hall, office, street, factory, phone screen).
- Sets may repeat across episodes when they fit (the trading hall, a regulator office).
- Wide 16:9 plates with empty space where characters will stand. No people in plates unless they are a distant crowd.

### 6.2 Shot mix and motion
- About 50% story shots, 40% evidence cards, 10% hero moments (one bigger animated moment per part, for example a press stamping boxes "AI").
- A new visual or a slow push every 5-8 s. Evidence cuts 1-3 s, story shots 4-6 s, emotional holds 6-10 s.
- Motion vocabulary (only these): slow push-in or pull-out (3-9%), gentle parallax, idle breathing and sway on characters, blinks every 3-5 s (when blink frames exist), light particles (dust, rain), soft light flicker, cross-dip cuts (0.18 s).
- Not allowed: whip pans, spinning text, glitch effects, camera shake (except a 5 px shake on a heavy impact), cartoon bounces.
- A 5 s breather every 2-3 min: no voice, music only, slow push on a set.

---------------------------------------------------------------------
## 7. EVIDENCE CARDS (3 templates, code-built)
Navy board with a faint 96 px grid, the same grade and grain as everything else.
1. **Stat slam:** one big number (Anton, about 250 px, gold; red for losses) counts up over 0.8 s. Label underneath (Anton 72, off-white). Source line at the bottom (Mono 26, grey): "SOURCE: OUTLET, DATE". A strike-through in off-white when something is "gone".
2. **Headline / filing card:** off-white paper cards (red top strip), serif headline with the key phrase highlighted amber, a small mono dateline, slid in at a slight angle with a soft shadow. Label "PARAPHRASED FROM: ..." or "RECREATED FROM: ..." unless it is a real screenshot.
3. **Chart:** a line draws itself (gold while rising, red while falling), the peak marked, a big red % at the end, months on the axis. Say "shape illustrative" when not plotted from real data, or plot real data.
Optional, only when a story truly needs it: a bar comparison (P/E 250x vs 30x).
- Every number on screen carries its source.
- One evidence card every 45-60 s minimum.

---------------------------------------------------------------------
## 8. VOICE (locked: Chatterbox)
- Model: Chatterbox TTS by Resemble AI (MIT licence, commercial use allowed). Output carries an inaudible watermark (fine).
- Voice identity: zero-shot clone of a 10 s reference clip made with Kokoro voice "am_michael" (Apache 2.0). The narrator is fully synthetic and belongs to no real person. Use the SAME reference clip (ref_michael.wav) for every episode. This is the channel's voice.
- Character: male, warm, mid-low, calm, clear American English, a trusted explainer.
- Generate one sentence per call. Then trim silence and place each line on the timeline.

### 8.1 Emotion presets (exaggeration / cfg_weight)
| Preset | Use | exaggeration | cfg_weight |
|---|---|---|---|
| facts | normal narration | 0.50-0.55 | 0.50 |
| dry | sarcastic or joke lines | 0.60 | 0.40 |
| tension | build-up, "so you'd pay..." | 0.70 | 0.35 |
| question | act-ending questions | 0.80 | 0.30 |
| beat | short punches ("Gone.", "On a promise.") | 0.85-0.90 | 0.25 |

### 8.2 Gaps after lines
After a normal line 0.25-0.35 s. Before a punch 0.15 s. After a punch 0.9 s. After an act question 1.0 s, then the chapter card. End of video 1.6 s.

### 8.3 Voice polish chain (ffmpeg)
highpass 70 Hz, +2.5 dB at 180 Hz, +1.5 dB at 3.5 kHz, light de-esser, compressor (threshold -20 dB, 3:1, attack 5 ms, release 80 ms). No reverb.
- Abbreviations: write "A.I." (tested: heard as "AI"). Spaced "A. I." was garbled. Test any new abbreviation once. If a name is misread, give the voice a phonetic spelling in the line's "say" field (Gekko is said as "Gecko"); captions keep the real spelling. Write numbers as words.
- Re-generate any line that sounds off (a wrong word, odd emphasis, artefacts). Checking every line is mandatory.
- Drafts only: edge-tts Andrew (no commercial licence, never publish).

---------------------------------------------------------------------
## 9. SOUND MIX: VOICE FIRST
| Layer | Level | Notes |
|---|---|---|
| Voice | RMS -17 dB during speech | anchor |
| Music | 15-18 dB under the voice | ducks a further 4 dB while the voice speaks |
| Ambient beds (crowd, rain, factory) | 22-27 dB under the voice | felt, not heard |
| SFX hits | peaks 8-14 dB under the voice peak | max 1 every 6-8 s, only on actions and numbers |
| Final master | -14 LUFS integrated, -1.5 dBTP | |
- Music changes by part: cold open (tension or curious), Dream (curious), Machine (sneaky), Fall (dark or sombre), Lesson (calm). 2-3 tracks per episode is fine.
- 1 s of near-silence before the twist and before act questions.
- No cartoon SFX (boing, gulp, slide whistle). No music with vocals.
- Music: Kevin MacLeod (incompetech.com, CC BY 4.0, credit in the description) or other CC0/CC BY. SFX: CC0 from Freesound only.

---------------------------------------------------------------------
## 10. CAPTIONS AND TYPE
- Burned-in captions: Anton 62 px, uppercase, white with a 6 px black stroke, the active word in gold. 3-4 words per chunk, broken at punctuation. Positioned at y = 925 of 1080.
- Word timing from Whisper (word timestamps) on the final voice track. Caption text matches the spoken words exactly (the "text" field; the "say" field is only for the voice).
- Fonts: Anton (titles, numbers, captions), DejaVu Sans Mono Bold (sources, labels, datelines), DejaVu Serif Bold (headline cards). All OFL or free.
- Hidden captions on chapter cards. Never cover a number on screen with a caption.

---------------------------------------------------------------------
## 11. THUMBNAIL AND TITLE
- Title under 60 characters: a number plus a curiosity gap ("The $480 Billion Illusion").
- Thumbnail: 1 character in a strong pose, 1 number or 2-3 big words, 1 red element. 3 elements max. Same editorial style.
- Title and thumbnail say different things. Make 2 thumbnails and run YouTube's Test & Compare.

---------------------------------------------------------------------
## 12. TRUST, LEGAL AND POLICY
- Fraud claims only from regulator decisions, court records or major outlets. Two sources per key number. A proposed penalty is "proposed"; a warning is not a fine.
- Description: sources with links, music credits (CC BY), "Scenes are dramatised. Characters are fictional." Pinned comment with sources.
- Correction policy: pin corrections, and fix them in the description.
- YouTube AI disclosure: not needed for stylised animation. Keep the DRAMATISATION tag.
- Inauthentic-content risk (YouTube, July 2026): every episode must have original research, its own story, its own cast and fresh visuals. Never mass-produce from one template.
- Copyright: never name living artists or publications in image prompts. No real logos or likenesses. Pop culture in words only.

---------------------------------------------------------------------
## 13. SCORECARD (QA, target 9/10 on every angle before upload)
Story clarity | Hook (0:30) | Say-it-show-it sync | Evidence and sources | Voice emotion and errors | Mix (voice clearly on top) | Visual consistency | Pace (no dead air, no rush) | Tone (dry, not cringe) | Thumbnail and title | Trust and policy.
Any angle under 9 gets fixed before upload. Watch once at normal speed; anywhere you'd reach for your phone, cut or tighten.

---------------------------------------------------------------------
## 14. PER-EPISODE CHECKLIST
1. Pick a real case with a human angle and a regulator or court record.
2. Research doc: 15-20 facts, each with a link and date. Two sources for key numbers.
3. Cast sheet (2-4 characters) and set list (4-6 sets).
4. Script in the row format (3.1): the 5 parts, 8-10 dry lines, 3-5 pop references, three hook versions (pick one).
5. Word count (2,100-2,200) and a read-aloud.
6. Shot list = the script's VISUAL column. Check Rule 1 line by line.
7. Images: master sheets, poses, plates (prompts in the AI instructions).
8. Voice: Chatterbox line by line, listen to each line, re-generate bad ones.
9. Timeline from the real line timings, then Whisper word timing for captions.
10. Render, then mix to section 9 levels and master to -14 LUFS.
11. QA with the scorecard and the mute test.
12. 2 thumbnails, title, description (sources, credits, dramatisation note), chapters.
13. Upload in the weekly slot. Pin the sources comment.
