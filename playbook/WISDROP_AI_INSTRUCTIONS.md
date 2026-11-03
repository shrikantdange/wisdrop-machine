# WISDROP: INSTRUCTIONS FOR AN AI PRODUCER (v1, 2026-11-03)

> v3 note (2026-11-03): render_template.py / mix_template.py and per-episode render.py / mix.py are retired.
> Episodes are drawn from shots.json by machine/engine/shots_render.py and mixed by machine/engine/automix.py (see docs/SHOTS.md).
You are producing a video for the YouTube channel Wisdrop. Read WISDROP_PLAYBOOK.md first: it holds the creative rules. This file tells you HOW to build the video, step by step, with the tools and code in the starter kit.
Follow both files exactly. When something is unclear, ask the channel owner. Do not improvise new styles, voices or formats.

---------------------------------------------------------------------
## A. WHAT YOU NEED
| Need | What | Notes |
|---|---|---|
| Computer | Linux or Mac, Python 3.11-3.12, ffmpeg | A GPU is optional but makes the voice about 20x faster |
| Image generator | Any strong text-to-image model that accepts a reference image (for example Gemini image, GPT image, Flux Kontext, Midjourney with --cref) | For character consistency it MUST accept a reference image |
| Voice | Chatterbox TTS (pip) | MIT licence |
| Captions timing | faster-whisper (pip) | word timestamps |
| Cutouts | rembg with the isnet-general-use model | transparent PNGs of characters |
| Starter kit | wisdrop_starter_kit.zip | code, fonts, voice reference, music, SFX, style references |

Starter kit contents:
```
docs/      WISDROP_PLAYBOOK.md, WISDROP_AI_INSTRUCTIONS.md
voice/     ref_michael.wav (THE channel voice reference, never change), gen_vo.py
render/    edhelpers.py (shared look: grade, grain, vignette, paste, glow, dust, rain, zoom)
           render_template.py (example episode renderer: shots, evidence cards, captions)
           build_vo.py (trim lines, place on timeline, polish, timeline.json)
           whisper_words.py (word timing for captions + voice check)
           mix_template.py (voice-first mix + master)
fonts/     Anton.ttf (+ use DejaVu Sans Mono Bold / DejaVu Serif Bold from the system)
music/     Kevin MacLeod tracks (CC BY 4.0), ATTRIBUTION.txt
sfx/       CC0 Freesound effects
style_ref/ example plates and character cutouts in the locked editorial style, plus one finished sample video
```

---------------------------------------------------------------------
## B. ONE-TIME SETUP
```bash
# 1. system tools
sudo apt install ffmpeg fonts-dejavu-core   # mac: brew install ffmpeg

# 2. voice environment (separate venv, it is large)
python3 -m venv venv_cb && source venv_cb/bin/activate
pip install chatterbox-tts torchaudio
# first run downloads about 3 GB of models (set HF_HOME to a disk with space)
deactivate

# 3. render / tools environment
python3 -m venv venv_tools && source venv_tools/bin/activate
pip install numpy pillow "rembg[cpu]" faster-whisper
```
GPU (recommended): on Google Colab or any CUDA machine, `pip install chatterbox-tts` and load with `device="cuda"`. A 12-minute episode then takes about 10-20 minutes. On a 2-core CPU it takes about 60-100 s per sentence (a whole episode is several hours, so run it overnight).

---------------------------------------------------------------------
## C. FOLDER LAYOUT PER EPISODE
```
epNN-<slug>/
  research.md        facts with links and dates
  cast.md            cast sheet (playbook 5.2)
  script.md          row-format script (playbook 3.1)
  lines.json         [{"id":0,"text":"...","preset":"facts","gap":0.3,"shot":"s_kitchen_iron"}, ...]
  img/plates/        set backgrounds (16:9)
  img/chars/         master sheets + pose images
  img/cut/           transparent cutouts
  vo/                l00.wav, l01.wav ...
  timeline.json      produced by build_vo.py
  render.py          copied from render_template.py and edited
  mix.py             copied from mix_template.py and edited
  out/               final mp4, thumbnails, description.txt
```

---------------------------------------------------------------------
## D. STEP BY STEP
### Step 1. Research
- Find the case in regulator releases (SEC, CSRC, FCA, SEBI, DOJ and so on), court filings and major outlets (Reuters, Bloomberg, FT, WSJ, Caixin, Nikkei).
- Write 15-20 facts: fact | number | source outlet | date | URL. Two sources for each key number.
- Mark proposed vs final penalties, and warning vs fine.

### Step 2. Cast and sets
- Design 2-4 NEW fictional characters for this story (playbook section 5). Fill the cast sheet.
- List 4-6 sets the script needs.

### Step 3. Script
- Write in the row format (playbook 3.1). 5 parts, about 2,100-2,200 words.
- For every line, write the VISUAL first and make sure it literally shows the line (playbook Rule 1).
- Convert to lines.json: one entry per sentence or short punch, with its preset and gap (playbook 8.1, 8.2).

### Step 4. Images
Use these prompt templates. Always put the STYLE BLOCK in. Never add text, logos, real people, or artist or publication names.

**STYLE BLOCK (paste into every prompt):**
> Editorial flat-vector illustration for a serious finance documentary. Calm, adult, believable. Restrained realism: realistic proportions and hands, simple flat colour shapes with 2-3 tones per surface, crisp hard-edged shadows, soft cinematic lighting from a window or lamp, subtle paper grain texture. Muted palette of deep navy, charcoal, warm amber and off-white, with small accents only. Low or eye-level cinematic camera, 16:9 composition. No text, no letters, no logos, no watermarks.

**A) Character master sheet** (one per character, plain background):
> [STYLE BLOCK] Character turnaround sheet of ONE fictional character on a plain light-grey background: front view, three-quarter view, side view, back view, and three small face close-ups (neutral, worried, hopeful). [AGE] [GENDER] [BUILD], [HAIR], wearing [OUTFIT], signature accent colour [COLOUR], holding [PROP]. Same character in every view, consistent outfit and proportions, about 7 heads tall.

**B) Single pose** (pass ONE single-figure image of the character as the reference, never the whole sheet, or the model copies the sheet):
> [STYLE BLOCK] The same character as the reference image, full body, [POSE/ACTION], [EXPRESSION] expression, on a plain flat light-grey background, even lighting, no shadow on the floor, whole figure visible with margin around it.
Then cut it out: `rembg i -m isnet-general-use in.png out.png`.

**C) Set plate** (background, no main characters):
> [STYLE BLOCK] Wide establishing shot of [SET: e.g. a modest suburban kitchen at morning / a grand old stock-exchange trading hall at night with glowing price boards and a distant crowd]. Leave clear empty floor space on the [left/right/centre] for a character to stand. [TIME OF DAY, LIGHT]. No foreground people.

**D) Full scene** (when a cutout won't look right, for example a character interacting with a table or window, pass the character reference):
> [STYLE BLOCK] [CHARACTER from reference] [ACTION from the script line] in [SET]. [CAMERA: medium shot from the side]. [LIGHT].

Image rules:
- Plates at least 1376x768. The renderer scales them to 1920x1080.
- Keep every character's look identical: always use the same reference image.
- Images over 5 MB: convert to JPEG before reading or sending.
- Reject any image with garbled text, extra fingers, a real logo, or an off-style look. Regenerate it.

### Step 5. Voice
```bash
source venv_cb/bin/activate
python voice/gen_vo.py epNN      # reads epNN/lines.json, writes epNN/vo/lNN.wav, uses voice/ref_michael.wav
```
gen_vo.py loads Chatterbox once and makes one wav per line with that line's preset (facts 0.55/0.5, dry 0.6/0.4, tension 0.7/0.35, question 0.8/0.3, beat 0.9/0.25). It skips lines already made, so you can resume.
Listen to every line. Delete and re-run any bad one (it will be regenerated with a new random take).

### Step 6. Timeline
```bash
python render/build_vo.py epNN     # (venv_tools) trims silence, applies gaps, polish chain -> vo.wav + timeline.json
```
timeline.json gives each line's exact start and end. ALL shot cuts come from it.

### Step 7. Caption timing
```bash
python render/whisper_words.py epNN    # -> epNN/words.json (script spelling, Whisper timing, line by line)
```
The renderer uses words.json automatically when it exists. Captions: 3-4 words per chunk, broken at punctuation.
**Voice check with Whisper:** also compare what Whisper HEARD with the script for each line. Any line where a word is missing or wrong gets regenerated (this catches clipped first words and garbled abbreviations, for example spaced "A. I." heard as "they got").

### Step 8. Render
- Copy render_template.py to epNN/render.py.
- Load your plates and cutouts in the PL and C dictionaries.
- Write one shot function per VISUAL (story shots use `crop_cam` or `zoom` + `paste` for characters with breathing; evidence uses `stat`, `headlines`, `chart`, `pe`).
- The SHOTS list maps each line id to its shot: `(start_of_line - 0.1, shot_fn, is_story)`. Story shots get the DRAMATISATION tag automatically.
- NO logo intro (the template's s_sting is retired, so don't use it). Chapter card `s_chap` at the start of each part.
- Check frames first: `python epNN/render.py epNN out.mp4 60,300,900` writes chk_<frame>.jpg files. Look at them against the script, then render the full video.

### Step 9. Mix
- Copy mix_template.py. Set the music per part, the beds per set, and hits only on actions and numbers.
- Levels are already coded to playbook section 9 (voice -17 dB RMS, music 18 dB under with 4 dB duck, SFX peaks 8-14 dB under the voice, master -14 LUFS).
- Mux: `ffmpeg -i vid.mp4 -i mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest final.mp4`
- Delivery copy: `-c:v libx264 -preset slow -crf 20 -movflags +faststart`

### Step 10. QA (before upload)
- Mute test: every frame makes sense with its caption.
- Sync test: every spoken number appears on screen in the same moment and form.
- Voice test: no mispronounced names, no artefacts, no robotic stress.
- Mix test on phone speakers: the voice is clearly on top all the time.
- Score every angle in playbook section 13. Fix anything under 9.

### Step 11. Packaging
- Title (under 60 characters), 2 thumbnails (1 character, 1 number, 1 red element), chapters with timestamps.
- Description: summary, sources with links, "Scenes are dramatised. Characters are fictional.", music credits from ATTRIBUTION.txt.

---------------------------------------------------------------------
## E. HARD DON'TS
- Don't change the voice reference, the fonts, the palette or the grade.
- Don't show a visual that doesn't match its line.
- Don't use a logo intro, whip pans, glitch, cartoon SFX or music with vocals.
- Don't draw real people or logos. Don't name artists or publications in prompts.
- Don't state a number without a source on screen and in the description.
- Don't call a proposed penalty final, or a warning a fine.
- Don't publish anything voiced with edge-tts or another non-commercial model (Fish S2, Higgs, Voxtral, F5, XTTS v2).

---------------------------------------------------------------------
## F. WHAT THE CHANNEL OWNER STILL DECIDES
- Which story is next.
- Approval of the cast sheet and the script before images and voice are made.
- Final approval of the video and thumbnail before upload.
