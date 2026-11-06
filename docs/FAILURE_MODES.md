# WISDROP FAILURE MODES (FM-* register)

Version 1, written 2026-11-06. Everything we know that can go wrong in a Wisdrop episode, from the
first search to the upload, written as rules. Each rule has an ID, the **symptom** (what you see),
the **cause**, a **prevention** rule, and a **check**. Used by `docs/DIRECTOR_PROMPT.md` and by
`machine/fm_check.py`.

**Check tags.**
`[CODE]` = an existing tool checks it (named). `[CODE-TODO]` = cheap to code; stub exists in
`machine/fm_check.py` (some already implemented, see the script's header). `[HUMAN]` = a person or
the AI must look; the item is on the self-review list in DIRECTOR_PROMPT section 6.

**Severity.** **(stop)** = blocks the gate/upload until fixed. Others = fix before final render.

Sources [n] are listed at the end; [R] read in full, [S] search/excerpt only (principle, not a number
on screen). Owner rules are marked **(owner)**; inferences **(proposal)**.

ID prefixes: R research and facts, L legal and ethics, P platform, S story, W script/writing,
V voice, G visuals, A audio, C chapter sync and continuity, X render and pipeline, K packaging,
O owner/process.

---

## R - Research and facts

- **FM-R01 Unsourced number (stop).** *Symptom:* a figure on screen or in narration has no row in research.md. *Cause:* number remembered or copied from an earlier draft. *Prevent:* every line stating a fact carries `src` F-ids; every on-screen figure comes from a shots.json field whose `source` is set. *Check:* `[CODE-TODO]` fm_check R01 (digits/number words in `text` but empty `src`); `[CODE]` craft_check sources.
- **FM-R02 Key number single-sourced or sources disagree (stop).** *Symptom:* "key?=yes" row with one URL, or two sources give different values. *Cause:* second source not found, or one source rounds or covers a different period. *Prevent:* two independent sources for key numbers; if they disagree, show the lower/qualified figure ("more than $4 billion") and note both in research.md; ask the owner if the gap is more than rounding. *Check:* `[CODE-TODO]` fm_check R02 (key rows need two URLs).
- **FM-R03 Two sources that are really one.** *Symptom:* both "sources" quote the same press release. *Cause:* syndication. *Prevent:* pair a primary record (court filing, government page) with an independent report (wire, major outlet with its own reporting). *Check:* `[HUMAN]`.
- **FM-R04 Outdated status (stop).** *Symptom:* "still at large", "awaiting trial" when it has changed. *Cause:* research done weeks before render. *Prevent:* research.md "Status check" with date checked; re-check every person on the day of the final render and the day of upload. *Check:* `[CODE-TODO]` fm_check R04 (status check date older than 7 days at final render -> REVIEW).
- **FM-R05 Rumour stated as fact (stop).** *Symptom:* "she is believed dead" said flatly. *Cause:* forum/tabloid claims, documentary speculation. *Prevent:* rumours live in research.md "Rumour and disputed claims"; on air they are attributed ("a BBC investigation reported...") or left out. *Check:* `[HUMAN]`.
- **FM-R06 Computed figure wrong.** *Symptom:* per-victim average, total or conversion that no source states. *Cause:* arithmetic, mixed periods, double counting. *Prevent:* "Computed figures" section with formula, inputs, date, rounding; say "about" on air; prefer a sourced figure over a computed one. *Check:* `[CODE-TODO]` fm_check R06 (recompute formulas written as `= a * b` in research.md).
- **FM-R07 Currency or unit mix-up.** *Symptom:* euros shown as dollars, "billion" vs "million", short vs long scale. *Cause:* sources in different currencies. *Prevent:* show the currency the source used; any conversion goes in Computed figures with the rate and its date. *Check:* `[CODE-TODO]` fm_check R07 (shots.json prefix/suffix vs the F-row's currency symbol).
- **FM-R08 Date mix-up.** *Symptom:* wrong year, US/EU day-month swap, publish date used as event date. *Cause:* reading the article date instead of the event date. *Prevent:* ISO dates in research.md; event date and source date in separate columns. *Check:* `[CODE-TODO]` fm_check R08 (dates in lines vs timeline rows).
- **FM-R09 Quote altered.** *Symptom:* a quote on a card differs from the source. *Cause:* trimming for length. *Prevent:* quotes verbatim with ellipsis marks; never change meaning; RCFP notes altered quotes that change meaning are a libel risk [29]. *Check:* `[HUMAN]` (compare against saved capture).
- **FM-R10 Dead or changed source URL.** *Symptom:* link in description 404s. *Cause:* sites move. *Prevent:* save captures/archive links at research time. *Check:* `[CODE-TODO]` fm_check R10 (optional `--net` HEAD check on research URLs).
- **FM-R11 Context missing.** *Symptom:* a true number that misleads (cumulative vs yearly, gross vs net). *Cause:* cherry-picking for drama. *Prevent:* every key figure has its period and basis written beside it on screen (small dateline). *Check:* `[HUMAN]`.
- **FM-R12 Wikipedia as source.** *Symptom:* only source is an encyclopedia. *Cause:* convenience. *Prevent:* use it to find the citations, then cite those. *Check:* `[CODE-TODO]` fm_check R12 (wikipedia.org as a source URL for a key row -> FAIL).
- **FM-R13 Map or place wrong.** *Symptom:* pin in the wrong city/country, wrong border. *Cause:* coordinates typed by hand. *Prevent:* coordinates from a gazetteer, place named in an F-row. *Check:* `[HUMAN]` + FM-G09.

## L - Legal and ethics

General principle: truth is the core defence; attribution to official records and fair, accurate
reporting of them lowers risk; precise words for the legal stage of a case; give the subject a
chance to respond; edit without creating a false impression [29][30][31]. This is not legal advice:
for a high-risk episode, the owner decides whether to get a media lawyer's review [29].

- **FM-L01 Defamation of an unconvicted person (stop).** *Symptom:* narration says "X stole" when X is only charged or never charged. *Cause:* writing the story's conclusion as fact. *Prevent:* brief.md legal status table; for anyone not convicted use attribution ("prosecutors say", "according to the indictment") and "alleged"; RCFP: if a person has only been charged, the reporting must say so [29]. *Check:* `[CODE-TODO]` fm_check L01 (guilt words near names marked unconvicted in bible.md without an attribution verb in the same line).
- **FM-L02 Wrong offence or stage.** *Symptom:* "felon" for a misdemeanour, "convicted" for a plea not yet entered. *Prevent:* exact offence, court and date from the record [29]. *Check:* `[HUMAN]`.
- **FM-L03 Drawing a real person (stop).** *Symptom:* AI or vector likeness of a real person, or a silhouette clearly modelled on them. *Cause:* "just a stylised portrait". *Prevent:* never bend rule; real people only as names/documents; YouTube also treats AI likeness of real people as realistic content requiring disclosure and can be misleading [20]. *Check:* `[CODE]` worker_images people QC; `[HUMAN]`.
- **FM-L04 Guilt-implying words in visuals.** *Symptom:* "WANTED"/"SCAMMER" stamp on an unconvicted person's name; mugshot-style card. *Prevent:* stamps and posters only for official statuses (e.g. an official wanted listing) with source; bible.md "words we never use". *Check:* `[CODE-TODO]` fm_check L04 (stamp/wanted text vs bible.md banned list).
- **FM-L05 Victim privacy (stop).** *Symptom:* a private victim's name, face, town, employer identifiable. *Cause:* using a victim's social posts. *Prevent:* use only victims who told their story publicly in a major outlet, named as that outlet named them; otherwise fictional composites tagged DRAMATISATION; blur/omit identifying details [29]. *Check:* `[HUMAN]`.
- **FM-L06 No right of reply.** *Symptom:* accused party's denial or plea missing. *Prevent:* include the public response ("pleaded not guilty", "did not respond"); offering a response and including it shows fairness [29][31]. *Check:* `[HUMAN]`.
- **FM-L07 Ongoing case prejudice.** *Symptom:* episode about a live trial states conclusions. *Prevent:* stick to the public record; avoid publishing during a jury trial in jurisdictions with contempt rules (UK, India, Australia) **(proposal)**; ask owner. *Check:* `[HUMAN]`, brief.md status.
- **FM-L08 Republication liability.** *Symptom:* repeating a third party's defamatory claim ("a forum said he laundered money"). *Cause:* thinking quoting is safe. *Prevent:* repeating a defamatory statement can carry the same liability; repeat only from official records/proceedings with attribution (fair report privilege, where it applies) [29][30]. *Check:* `[HUMAN]`.
- **FM-L09 Misleading edit.** *Symptom:* juxtaposition implies something the record does not say (e.g. silence inserted after a question). *Prevent:* RCFP's "edit with care" lesson: do not create a false impression even with true pieces [29]. *Check:* `[HUMAN]` seam review.
- **FM-L10 Opinion presented as fact.** *Symptom:* "he was obviously lying". *Prevent:* opinion only when based on disclosed facts and clearly framed as opinion [29][30]. *Check:* `[HUMAN]`.
- **FM-L11 Identifiable small group.** *Symptom:* "the company's compliance team knew" (a team of 3). *Prevent:* a statement about a small group can identify each member [29]; name the source or narrow to the person in the record. *Check:* `[HUMAN]`.
- **FM-L12 Trade libel.** *Symptom:* a real product/company called worthless without record. *Prevent:* company claims need the same sourcing as personal ones [29]. *Check:* `[HUMAN]`.
- **FM-L13 Trademark/logo misuse.** *Symptom:* a real company logo used as if endorsing or as an accusation stamp. *Prevent:* logos only when the entity is the subject, shown as in its documents; never altered. *Check:* `[HUMAN]`.
- **FM-L14 Graphic or distressing detail.** *Symptom:* suicide or violence details shown or described graphically. *Prevent:* say it plainly once, no imagery, add help-line note in description **(proposal)**. *Check:* `[HUMAN]`.
- **FM-L15 Financial-advice tone.** *Symptom:* "you should buy/sell". *Prevent:* lessons are about spotting fraud, never investment advice; YouTube does not monetise AI personas giving financial guidance [21]. *Check:* `[CODE-TODO]` fm_check L15 (phrases "you should invest|buy|sell").

## P - Platform (YouTube)

- **FM-P01 Inauthentic / mass-produced look (stop for channel).** *Symptom:* episodes feel templated: same music, same AI imagery, script read over slides. *Cause:* automation without editorial voice. *Prevent:* YouTube does not monetise generic/repetitive or templated AI content and lists "exact same background music and repetitive AI generated imagery across many videos, each reading an AI script" as spam [21][22]; each episode has its own story, research, look accents and asset mix; rotate music beds; never reuse a cold-open structure twice in a row. *Check:* `[CODE-TODO]` fm_check P01 (music list and template mix compared to previous episode; >70 % identical -> REVIEW) **(proposal)**.
- **FM-P02 Reused content.** *Symptom:* long clips of news footage or other creators. *Prevent:* reused material only with significant original commentary/modification; permission does not exempt it [21]. We use stills and documents, transformed into our collage. *Check:* `[HUMAN]`.
- **FM-P03 AI disclosure wrong (stop).** *Symptom:* realistic AI scene (a real place, an event that looks real) uploaded with "AI use: No". *Prevent:* disclose when content looks realistic: a realistic scene that did not happen, altered real footage/places, a real person doing something they did not [20]; our AI story stills of real places count as realistic -> Yes (recommendation; owner decides). Non-realistic animation and script/thumbnail help do not need disclosure [20]. *Check:* `[CODE-TODO]` fm_check P03 (any AI picture tagged realistic and package lacks `ai_disclosure: yes`).
- **FM-P04 Clickbait mismatch (stop).** *Symptom:* thumbnail/title promise not in the video, or not in the first 30 s. *Prevent:* YouTube spam policy bans maliciously misleading titles/thumbnails [22]; titles and thumbnails must accurately represent content [23]; thumbnail claim appears in the first 30 s (RETENTION.md). *Check:* `[CODE-TODO]` fm_check P04 (thumb_text words each match a line/shot text in the first ~30 s).
- **FM-P05 Thumbnail policy.** *Symptom:* gore, shock, or misleading imagery; impersonation. *Prevent:* follow the Thumbnails policy [24]; no real faces (our rule anyway). *Check:* `[HUMAN]` + thumbnail.py score.
- **FM-P06 Copyright on images (stop).** *Symptom:* photo without a licence on our list. *Prevent:* Commons with CC0/PD/CC BY/BY-SA only, via fetch_media; credits.json complete. Fair use is a case-by-case four-factor defence with no safe percentage [27]; we do not rely on it. *Check:* `[CODE]` fetch_media licence filter; `[CODE-TODO]` fm_check P06 (every media file has a credits.json entry).
- **FM-P07 Attribution incomplete.** *Symptom:* "Photo: Wikimedia" only. *Prevent:* TASL: title, author, source link, licence link [28]; BY-SA derivative note. *Check:* `[CODE-TODO]` fm_check P07 (credits.json entries have all four).
- **FM-P08 Music Content ID claim.** *Symptom:* claim after upload; ads go to the claimant or the video is blocked [26]. *Cause:* track also registered in Content ID by a third party, or not from the kit. *Prevent:* kit/music only, with ATTRIBUTION; CC-licensed tracks are not eligible as Content ID references [26] but third parties sometimes claim anyway: keep the licence URL ready for dispute; upload as private first and wait for checks. *Check:* `[HUMAN]` pre-publish private upload.
- **FM-P09 AI music.** *Symptom:* AI-generated music bed. *Prevent:* AI music that is the main focus needs disclosure [20]; we use kit music only. *Check:* `[HUMAN]`.
- **FM-P10 Advertiser-unfriendly.** *Symptom:* yellow icon. *Cause:* graphic detail, profanity in quotes. *Prevent:* bleep/omit profanity in quotes, no gore; keep tone factual. *Check:* `[HUMAN]`.
- **FM-P11 Misleading metadata in description/tags.** *Symptom:* unrelated keywords. *Prevent:* tags only for the case and its people/places [22]. *Check:* `[HUMAN]`.

## S - Story

- **FM-S01 Weak hook.** *Symptom:* intro retention low; first 30 s explains instead of shows. *Prevent:* H1-H3 (shock fact/visual <= 5 s, question <= 8 s, promise <= 15 s); open on the fall. *Check:* `[CODE]` craft_check H1/H2, score_script --hooks.
- **FM-S02 Sagging middle.** *Symptom:* retention slope steepens around 40-60 %. *Prevent:* mid-point twist near 40 % with board change and higher stakes; each chapter has one peak visual. *Check:* `[CODE-TODO]` fm_check S02 (a line with `preset: tension` or `trans` within 35-45 % of lines).
- **FM-S03 Open loop never closed.** *Symptom:* a question asked and never answered. *Prevent:* beats.md loop ledger; every opened loop has a closing row. *Check:* `[CODE-TODO]` fm_check S03 (loops in beats.md opened vs closed).
- **FM-S04 No payoff / flat ending.** *Symptom:* video stops after the sentencing. *Prevent:* return to the cold open with new meaning; quotable last line; one usable lesson. *Check:* `[HUMAN]`.
- **FM-S05 Too many names.** *Symptom:* viewers lose track. *Prevent:* <= 5 named real people on screen per episode (proposal); role label every time; others as roles ("a London lawyer"). *Check:* `[CODE-TODO]` fm_check S05 (count `name` shots + capitalised names in bible.md list).
- **FM-S06 Repetition.** *Symptom:* the same fact said twice. *Prevent:* each F-id is the main point of at most one line (it can be referenced again only as a callback). *Check:* `[CODE-TODO]` fm_check S06 (same F-id as sole src on > 2 lines -> REVIEW).
- **FM-S07 Chapter seam feels like a restart.** *Symptom:* re-introductions, music restart, "welcome back". *Prevent:* treat the episode as one film [13]; handoff shots; no recap longer than one line. *Check:* `[HUMAN]` seam review (chapters.md).
- **FM-S08 Chronology confusion.** *Symptom:* flash-forward not signalled. *Prevent:* every time jump gets a dateline card or flapboard date; flashback flag in shots.json. *Check:* `[HUMAN]`.
- **FM-S09 Explaining before caring.** *Symptom:* 60 s of mechanism before a human stake. *Prevent:* a person (composite) or a consequence before each explanation block. *Check:* `[HUMAN]`.
- **FM-S10 Jargon unexplained.** *Symptom:* "MLM", "blockchain" used bare. *Prevent:* explain the first use on screen. *Check:* `[CODE]` score_script jargon.
- **FM-S11 Moralising / outrage tone.** *Symptom:* narrator calls people names. *Prevent:* let documents land; dry lines, never two in a row. *Check:* `[HUMAN]`.
- **FM-S12 Thin case.** *Symptom:* not enough assets or sources for 8 minutes. *Prevent:* brief.md asset check (10+ licence-safe assets). *Check:* `[HUMAN]` at Stage 0.
- **FM-S13 Runtime out of band.** *Symptom:* < 8 or > 12 min. *Prevent:* 165 wpm estimate in script.md; check after voice. *Check:* `[CODE]` wis check; `[CODE-TODO]` fm_check S13 (word count / 165 + gaps).
- **FM-S14 Promise drift.** *Symptom:* the video answers a different question than the title asks. *Prevent:* brief.md question is pasted at the top of beats.md and script.md. *Check:* `[HUMAN]`.

## W - Script (writing for TTS)

- **FM-W01 Mispronounced names.** *Symptom:* TTS says a Bulgarian name wrongly, or differently each time. *Prevent:* bible.md pronunciation list; `say` field; same spelling every time. *Check:* `[CODE-TODO]` fm_check W01 (names in bible.md pronunciations appear in `text` without a `say` on that line).
- **FM-W02 Numbers/dates read wrong.** *Symptom:* "$4B" read as "four B"; "2017" as "two zero one seven". *Prevent:* numbers and dates as words in `text`; figures only on screen. *Check:* `[CODE-TODO]` fm_check W02 (digits, $, %, symbols in `text`).
- **FM-W03 Sentences too long.** *Symptom:* breathless voice, one picture for 8 s. *Prevent:* <= 20 words per line (AGENTS rule 10). *Check:* `[CODE]` motion_check N2; `[CODE-TODO]` fm_check W03.
- **FM-W04 No pauses.** *Symptom:* questions run into answers. *Prevent:* gap >= 0.5 s after a question; ~1 s before the twist. *Check:* `[CODE]` motion_check N3; fm_check W04.
- **FM-W05 Acronyms.** *Symptom:* "FBI" read as a word. *Prevent:* write "F.B.I." or a `say`. *Check:* `[CODE-TODO]` fm_check W05 (all-caps words of 2-5 letters in `text`).
- **FM-W06 Homographs.** *Symptom:* "lead", "live", "record" stressed wrong. *Prevent:* rephrase or `say`. *Check:* `[HUMAN]` listen.
- **FM-W07 Captions differ from voice.** *Symptom:* caption shows words not spoken. *Prevent:* captions come from `text`, keywords only; `say` never shown. *Check:* `[CODE]` v5 keywords.
- **FM-W08 Banned openers.** *Symptom:* "let's get into it", "in this video", greetings. *Prevent:* AGENTS rule 10. *Check:* `[CODE-TODO]` fm_check W08.
- **FM-W09 Quote voiced as narrator's claim.** *Symptom:* listener can't tell a quote from narration. *Prevent:* "In his words:" before quotes; quote card on screen. *Check:* `[HUMAN]`.

## V - Voice

- **FM-V01 Artefacts.** *Symptom:* clicks, robotic warble, cut-off word, breath noise. *Prevent:* vo_qc + whisper word timing; redo only failed lines. *Check:* `[CODE]` worker_voice vo_qc.json.
- **FM-V02 Level drift between chapters.** *Symptom:* chapter 4 voice louder than chapter 2. *Cause:* lines voiced in different runs. *Prevent:* per-line loudness normalisation before mix; measure on the joined episode; Netflix keeps dialogue loudness range within 10 LU as best practice [16]. *Check:* `[CODE-TODO]` fm_check V02 (per-line LUFS spread from vo_qc > 3 LU -> REVIEW) **(proposal)**.
- **FM-V03 Emotion mismatch.** *Symptom:* cheerful read on a tragic line. *Prevent:* `preset` matches the beat (tension/dry/beat/question/facts). *Check:* `[HUMAN]` listen to every tension and beat line.
- **FM-V04 Reference drift.** *Symptom:* voice timbre changes. *Cause:* reference changed or a different engine. *Prevent:* never change ref_michael.wav; no edge-tts. *Check:* `[CODE-TODO]` fm_check V04 (sha256 of the reference against the recorded hash).
- **FM-V05 Wrong pace.** *Symptom:* > 180 or < 140 wpm on a line (proposal band). *Prevent:* re-voice; edit text. *Check:* `[CODE-TODO]` fm_check V05 (word timings).
- **FM-V06 Word timing off.** *Symptom:* keyword captions land early/late. *Prevent:* whisper_words alignment; re-align after any redo. *Check:* `[CODE]` assemble/shotspec.

## G - Visuals

- **FM-G01 Empty frame.** *Symptom:* big flat areas, lonely object. *Prevent:* flat area <= 35 %; depth layers on every board. *Check:* `[CODE]` frame_fill.py.
- **FM-G02 Repeated assets.** *Symptom:* the same photo twice, same shot type 3x in a row. *Prevent:* P4; each media key used once unless it is a motif listed in bible.md. *Check:* `[CODE]` craft_check P4/repeats; `[CODE-TODO]` fm_check G02 (media key reuse across chapters).
- **FM-G03 Style drift across chapters.** *Symptom:* chapter 5 looks like a different channel. *Cause:* new templates added late, different seeds. *Prevent:* bible.md palette; only SHOTS.md templates; chapter-1 look approved by owner and frozen. *Check:* `[HUMAN]` side-by-side contact sheet; `[CODE]` motion_check theme contrast.
- **FM-G04 Unreadable text.** *Symptom:* small, low-contrast, moving text. *Prevent:* 76/36/25 px; 4.5:1; read time 1 s per 13 characters (T1). *Check:* `[CODE]` motion_check L2/contrast, craft_check T1.
- **FM-G05 AI artefacts.** *Symptom:* extra fingers, melted objects, impossible signage. *Prevent:* faceless/no-people prompts, CPU QC, look at every AI picture at full size; redo with new seed. *Check:* `[CODE]` worker_images qc; `[HUMAN]`.
- **FM-G06 Text inside generated pictures (stop).** *Symptom:* gibberish letters on signs. *Prevent:* prompts forbid text; words drawn by code. *Check:* `[CODE]` worker_images text QC.
- **FM-G07 Too many AI pictures.** *Symptom:* > 6 per episode. *Prevent:* reuse via parallax/crops; code templates first. *Check:* `[CODE]` craft_check.
- **FM-G08 Fake-looking evidence.** *Symptom:* a recreated document/app screen mistaken for real. *Prevent:* tag ILLUSTRATIVE / RECREATED on every recreation (SHOTS.md tags); never fake a real outlet's headline layout without the real text and source. *Check:* `[CODE-TODO]` fm_check G08 (shots with `recreated`/`illustrative` types lacking the tag).
- **FM-G09 Wrong map or flag.** *Symptom:* wrong country highlighted, outdated border, wrong flag. *Prevent:* ISO-3 codes from a list; map shows change (route, fill, date, 2+ pins); never two map flights in a row. *Check:* `[CODE]` motion_check E1; `[CODE-TODO]` fm_check G09 (highlight codes valid ISO-3; pins have lat/lon in range).
- **FM-G10 Invented clock times.** *Symptom:* CCTV or flapboard shows a precise time that no source gives. *Prevent:* "--:--" or running counters only (T29/T32). *Check:* `[CODE-TODO]` fm_check G10 (time strings HH:MM in flapboard/cctv rows).
- **FM-G11 Accent overuse / red-green meaning.** *Prevent:* accent <= 15 %; never red vs green alone. *Check:* `[CODE]` motion_check C2.
- **FM-G12 Flashing.** *Prevent:* <= 3 flashes per second. *Check:* `[CODE]` motion_check M10.
- **FM-G13 Picture before voice.** *Prevent:* AGENTS rule 1. *Check:* `[CODE]` motion_check N4.
- **FM-G14 Still too long.** *Prevent:* nothing still > 2.5 s. *Check:* `[CODE]` craft_check P1.
- **FM-G15 Safe area / UI overlap.** *Symptom:* key text under the YouTube progress bar or end-screen elements. *Prevent:* keep key text out of the bottom 10 % and the end-screen zones in the last 20 s **(proposal)**. *Check:* `[CODE-TODO]` fm_check G15.
- **FM-G16 Photo quality.** *Symptom:* blurry, signage-heavy, empty-middle photos. *Check:* `[CODE]` photo_score.

## A - Audio

- **FM-A01 SFX lag.** *Symptom:* whoosh after the movement. *Prevent:* sounds within 2 frames of their event. *Check:* `[CODE]` automix S5.
- **FM-A02 Music fights the voice.** *Symptom:* words masked. *Prevent:* static bed 22 dB under the voice, band 18-25 dB; alert when a line is < 8 dB over the bed **(owner)**. *Check:* `[CODE]` automix audio_qc.
- **FM-A03 Banned sounds.** *Prevent:* no coin/ding/cash/game-UI **(owner)**. *Check:* `[CODE]` automix S2.
- **FM-A04 Loudness jump at chapter joins.** *Symptom:* step in level at a seam. *Cause:* chapters mixed separately. *Prevent:* mix and master the joined episode once; one loudness pass. *Check:* `[CODE-TODO]` fm_check A04 (short-term loudness 3 s either side of each chapter start differs > 3 LU -> REVIEW) **(proposal)**.
- **FM-A05 Clipping / true peak.** *Prevent:* master -14 LUFS integrated, true peak <= -1 dBTP (repo master.py/automix; matches YouTube-playback practice and AES streaming peak guidance [18]; Netflix's own spec is -27 LKFS dialogue-gated, -2 dBTP [16]). *Check:* `[CODE]` automix audio_qc `ok`.
- **FM-A06 Dynamic range too wide.** *Symptom:* quiet voice, loud stings. *Prevent:* keep loudness range moderate; Netflix best-practice LRA 4-18 LU for programme [16]; our LRA target 11 (master.py). *Check:* `[CODE]` master loudnorm print.
- **FM-A07 Ambience left running.** *Symptom:* airport hum under a courtroom scene. *Prevent:* `amb` per shot ends with the scene; fades <= 0.5 s **(proposal)**. *Check:* `[CODE-TODO]` fm_check A07 (amb spans across a chapter card).
- **FM-A08 Silence holes.** *Symptom:* dead air > 1.5 s without intent. *Prevent:* only planned silences (before twist). *Check:* `[CODE-TODO]` fm_check A08 (gaps > 1.5 s not on a beat/question line).
- **FM-A09 Music ends mid-part.** *Symptom:* bed runs out and loops audibly. *Prevent:* bed length >= part length or a planned loop point on a bar. *Check:* `[CODE-TODO]` fm_check A09.
- **FM-A10 Uncredited sound.** *Prevent:* kit/sfx + ATTRIBUTION only. *Check:* `[HUMAN]`.

## C - Chapter sync and continuity

- **FM-C01 Counter jumps or goes backwards.** *Symptom:* "$4B" in chapter 3, "$2B" in chapter 4 for the same metric. *Prevent:* bible.md counter ledger; chapter exit value = next entry value; every value an F-id figure. *Check:* `[CODE-TODO]` fm_check C01 (counter_to values monotonic unless marked `reset`).
- **FM-C02 Colour change inside a part.** *Prevent:* board/accent change only at a chapter card that starts a part. *Check:* `[CODE-TODO]` fm_check C02 (`color`/`mood` board changes not on a `chapter` shot).
- **FM-C03 Character look changes.** *Symptom:* composite's coat colour or shape changes. *Prevent:* bible.md look; same seed family and prompt stem. *Check:* `[HUMAN]` contact sheet; `[CODE-TODO]` fm_check C03 (cast prompts share stem).
- **FM-C04 Name/role label changes.** *Symptom:* "co-founder" then "partner". *Prevent:* bible.md labels. *Check:* `[CODE-TODO]` fm_check C04 (name shots: same name, different role).
- **FM-C05 Music key/tempo clash at joins.** *Symptom:* audible key change or tempo jump mid-part. *Prevent:* one bed per part; changes only on chapter cards; `music` list length = parts. *Check:* `[CODE-TODO]` fm_check C05 (len(music) == number of chapter cards + 1).
- **FM-C06 Accidental jump cut at seams.** *Prevent:* handoff shot defined in chapters.md. *Check:* `[HUMAN]` seam review.
- **FM-C07 Same template across a seam 3x.** *Prevent:* P4 across chapter boundaries too. *Check:* `[CODE]` craft_check P4 (runs on whole shots.json).
- **FM-C08 Line ids shift after edits.** *Symptom:* shots point at the wrong line after inserting a line. *Prevent:* never renumber; insert with new ids or update `at` in one scripted pass. *Check:* `[CODE-TODO]` fm_check C08 (every `at` exists in lines.json; ids unique).
- **FM-C09 Recap duplication.** *Prevent:* recap <= one line at a part start. *Check:* `[HUMAN]`.
- **FM-C10 Time-of-day/season inconsistency in story stills.** *Prevent:* bible.md notes for each recurring set. *Check:* `[HUMAN]`.

## X - Render and pipeline

- **FM-X01 Cache staleness.** *Symptom:* old picture/line appears after an edit. *Cause:* cache key missing a changed input. *Prevent:* job_hash includes prompt, seed, size, model; shot cache includes spec + inputs; redo_* flags. *Check:* `[CODE]` worker hashing; `[HUMAN]` spot-check edited shots.
- **FM-X02 Non-determinism.** *Symptom:* re-render differs. *Prevent:* crc32 seeds only. *Check:* `[CODE]` motion_check W1, determinism probe W2.
- **FM-X03 Out of memory.** *Symptom:* worker killed mid-render. *Prevent:* render_batch in parallel chunks; frames streamed to ffmpeg; heavy lock. *Check:* `[CODE]` summary.json status.
- **FM-X04 Partial render shipped.** *Symptom:* video shorter than the timeline; missing chapter. *Prevent:* join step verifies frame count = timeline length. *Check:* `[CODE-TODO]` fm_check X04 (video duration vs timeline end, > 0.5 s gap -> FAIL).
- **FM-X05 Audio/video drift.** *Symptom:* lips-free but SFX drift late in the video. *Prevent:* one timeline, 30 fps constant. *Check:* `[CODE-TODO]` fm_check X05 (ffprobe stream durations differ > 0.1 s).
- **FM-X06 Wrong format.** *Prevent:* 1920x1080, 30 fps (edhelpers). *Check:* `[CODE-TODO]` fm_check X06 (ffprobe).
- **FM-X07 Missing font/glyph.** *Symptom:* boxes instead of characters. *Prevent:* kit fonts only; normaliser for special characters. *Check:* `[CODE-TODO]` fm_check X07 (characters outside font coverage in shots text).
- **FM-X08 Cost overrun.** *Prevent:* max_gpu_seconds guard; test first; cost_report per run. *Check:* `[CODE]` cost.py guard.
- **FM-X09 Redo everything.** *Symptom:* full GPU run for a one-line fix. *Prevent:* redo_lines / redo_images only. *Check:* `[HUMAN]` plan line.
- **FM-X10 Paying for a broken plan.** *Prevent:* free checks + local frames before any spend. *Check:* `[CODE]` FAIL stops before money.
- **FM-X11 Same error loop.** *Prevent:* same error 3 times -> stop, open issue `[blocked] <ep> <step>`. *Check:* `[HUMAN]`.
- **FM-X12 Secret leak (stop).** *Symptom:* token in a file, log, commit or prompt. *Prevent:* GitHub secrets only; never echo env. *Check:* `[CODE-TODO]` fm_check X12 (regex scan for token patterns in tracked files) - implemented.
- **FM-X13 Heavy files in git.** *Prevent:* .gitignore for wav/mp4; outputs on branches/artifacts. *Check:* `[CODE-TODO]` fm_check X13 (tracked files > 20 MB).
- **FM-X14 Invalid JSON.** *Prevent:* parse before commit. *Check:* `[CODE-TODO]` fm_check X14 - implemented.
- **FM-X15 Model/tool version change.** *Symptom:* look or voice changes after an update. *Prevent:* pin versions in workflows; note changes in git log. *Check:* `[HUMAN]`.

## K - Packaging

- **FM-K01 Title overpromises.** *Prevent:* only facts from `title_facts` (sourced); <= 60 characters (package.py K3). *Check:* `[CODE]` package.py.
- **FM-K02 Thumbnail unreadable on a phone.** *Prevent:* phone mock score; <= 3 words. *Check:* `[CODE]` thumbnail.py score.
- **FM-K03 Title and thumbnail repeat each other.** *Prevent:* they say one promise together, different words (THUMBNAILS.md). *Check:* `[CODE-TODO]` fm_check K03 (word overlap).
- **FM-K04 Description missing sources/credits.** *Prevent:* sources with URLs, TASL credits, music credits, dramatisation and AI note. *Check:* `[CODE-TODO]` fm_check K04 (package/description has F-id URLs, every credits.json entry).
- **FM-K05 Chapters broken.** *Symptom:* chapters do not show. *Prevent:* first timestamp 00:00, >= 3 timestamps ascending, each >= 10 s [25]. *Check:* `[CODE-TODO]` fm_check K05 - implemented on package/chapters.txt or description.
- **FM-K06 Chapter titles mislead.** *Prevent:* a chapter label is a promise about its section; match content. *Check:* `[HUMAN]`.
- **FM-K07 End screen dead stretch.** *Prevent:* end screen in the last 20 s, no "thanks for watching" before it (RETENTION.md). *Check:* `[CODE]` endscreen shot exists; `[HUMAN]`.
- **FM-K08 Wrong AI-disclosure setting at upload.** *Prevent:* PUBLISH_CHECKLIST line; see FM-P03. *Check:* `[HUMAN]`.
- **FM-K09 Captions file missing or wrong.** *Prevent:* upload the script-based SRT, not auto captions. *Check:* `[HUMAN]`.
- **FM-K10 Publish without owner approval (stop).** *Prevent:* FINAL REVIEW PR merged by the owner. *Check:* `[CODE]` gates.yml state.

## O - Owner and process

- **FM-O01 Approving for the owner (stop).** *Prevent:* never merge gate PRs. *Check:* `[CODE]` gates.yml.
- **FM-O02 Late big feedback.** *Symptom:* owner changes the look after full render. *Prevent:* chapter-1 look approved before the other chapters are built. *Check:* `[HUMAN]` chapters.md sign-off line.
- **FM-O03 Unrecorded decisions.** *Symptom:* next AI run undoes an owner choice. *Prevent:* owner decisions written at the top of the relevant doc with date. *Check:* `[HUMAN]`.
- **FM-O04 Asking too much.** *Symptom:* owner gets 10 questions. *Prevent:* ask only the DIRECTOR_PROMPT section 7 list, one question with a recommendation. *Check:* `[HUMAN]`.
- **FM-O05 Drift from the repo rules.** *Symptom:* AI follows its own taste over AGENTS.md. *Prevent:* repo docs win; conflicts flagged. *Check:* `[HUMAN]`.

---

**Count: 134 rules** (R 13, L 15, P 11, S 14, W 9, V 6, G 16, A 10, C 10, X 15, K 10, O 5).

## Sources

[1]-[15], [20], [22], [23], [25], [28], [29], [31], [32]: see `docs/DIRECTOR_PROMPT.md` (Johnny Harris interviews, Vox producer and art-director interviews, Netflix docuseries editor interviews, Murch, YouTube Help pages, Creative Commons, RCFP, Ashurst).
[16] Netflix Partner Help Center, "Netflix Sound Mix Specifications & Best Practices v1.6" (-27 LKFS +/-2 LU dialog-gated; peaks <= -2 dBTP; limiter -2.3 dBFS; programme LRA 4-18 LU; dialog LRA <= 10 LU), https://partnerhelp.netflixstudios.com/hc/en-us/articles/360001794307-Netflix-Sound-Mix-Specifications-Best-Practices-v1-6 [R, 2026-11-06]
[17] Netflix Partner Help Center, "Loudness and True Peaks: How to Measure and When to Flag" (QC tolerance -1 dBTP), https://partnerhelp.netflixstudios.com/hc/en-us/articles/360050414014-Loudness-and-True-Peaks-How-to-Measure-and-When-to-Flag [S]
[18] AES TD1008, "Recommendations for Loudness of Internet Audio Streaming and On-demand Distribution" (speech -18 LUFS; max true peak -1 dBTP), https://aes2.org/wp-content/uploads/2024/01/20210924_TD1008_v3.13.pdf [S]
[19] EBU R 128 (programme loudness -23 LUFS; true-peak descriptor), https://tech.ebu.ch/publications/r128/ [S]
[21] YouTube Help, "YouTube channel monetization policies" (inauthentic/generic content, reused content, AI personas on finance), https://support.google.com/youtube/answer/1311392 [R, 2026-11-06]
[24] YouTube Help, "Thumbnails policy", https://support.google.com/youtube/answer/9229980 [S]
[26] YouTube Help, "How Content ID works" https://support.google.com/youtube/answer/2797370 and "Content eligible for Content ID" (CC-licensed and public-domain material ineligible as references) https://support.google.com/youtube/answer/2605065 [S]
[27] U.S. Copyright Office, "More Information on Fair Use" (four factors) https://www.copyright.gov/fair-use/more-info.html and Fair Use FAQ (no fixed amount) https://www.copyright.gov/help/faq/faq-fairuse.html [S]
[30] Digital Media Law Project, "Fair Report Privilege" http://www.dmlp.org/legal-guide/fair-report-privilege and "Opinion and Fair Comment Privileges" http://www.dmlp.org/legal-guide/opinion-and-fair-comment-privileges [S]
Also used: PBS Standards, "Media Law 101: Defamation", https://www.pbs.org/standards/media-law-101/defamation/ [S]; Storybench interview with Vox art director (see [9]).
