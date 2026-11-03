# THUMBNAILS (designed, never frame grabs)

Owner verdict 2026-11-03: every frame-grab thumbnail was bad. From now on thumbnails are DESIGNED by
`machine/thumbnail.py` (workflow **thumbs**) and approved by the owner before upload.

## Rules (checked by the auto score where possible)
1. One dominant focal subject: a FICTIONAL person with one strong emotion, or one striking object (coin, empty briefcase, burning cash). Never a real person, never a likeness (no Ruja Ignatova).
2. At most 3 words (thumbnail.py refuses more). Huge: caps >= 14 px tall when shrunk to 168x94.
3. High contrast: dark board + one glow colour; text yellow/cream with black stroke; accent word in one red box.
4. Readable at 168x94 and 360x202: check `phone_mock.png` before sending to the owner.
5. Curiosity gap: the thumbnail says what the title does not (title = topic, thumbnail = tension). Never repeat the title.
6. Red arrow or circle sparingly: at most one, only when it points at the thing that makes the gap.
7. Consistent brand frame: yellow WISDROP tag top-left, yellow bar at the bottom, same board every episode. Nothing important bottom-right (timestamp).
8. Every number on a thumbnail is sourced in research.md; a DERIVED number is flagged for the owner.
9. At most 2 GPU pictures per episode (Qwen-Image, cached, max_gpu_seconds 240); words always drawn by code.
10. Make 3 DIFFERENT concepts and use YouTube "Test & compare" (up to 3) after upload.

## Why (sources actually opened 2026-11-03)
- YouTube Help, Thumbnail & title tips (https://support.google.com/youtube/answer/12340300): 90 % of best-performing videos use custom thumbnails; casual viewers respond to "actions and emotions ... like a shocked face"; rule of thirds; easy-to-read font; "try not to make the design too complex"; keep the image as large as possible because devices differ.
- YouTube Help, Add custom thumbnails (https://support.google.com/youtube/answer/72431): 16:9; JPG/PNG; recommended 3840x2160, min width 640; under 2 MB on mobile upload; no violence/harmful content (strike risk). We render 1280x720 for review; upscale export to 3840x2160 is a later option.
- YouTube Help, A/B test titles & thumbnails (https://support.google.com/youtube/answer/13861714, via search excerpt): up to 3 thumbnails, winner = most watch time; test diverse options. (Excerpt only, open before relying on details.)
- Growwly playbook on MagnatesMedia (https://growwly.co/youtube-playbooks/@MagnatesMedia): thumbnails use 2-4 all-caps words ("DARK TRUTH") over red/black/yellow palettes, brand logos with an ominous twist; curiosity-gap title + scandal thumbnail.
- Thumbnail Bench study, 11,223 covers, Sep 2026 (https://thumbnailbench.com/resources/youtube-thumbnail-study-2026): Finance covers have text 94 %, a number 39 %, arrows 25 %; median 4 words; shocked face only 12 % of finance faces; bigger channels use fewer arrows/screenshots; winners repeat the title slightly less.
- Not verified this run (search excerpts only, not fetched): Coffeezilla, Vox, Johnny Harris, Patrick Boyle, ColdFusion, Wendover, Business Casual specifics. Business Casual excerpt (growwly) says two-tone all-caps text with one accent word; treat as a lead.

## Ep01 concepts (episodes/ep01-onecoin/thumbs/concepts.json)
- A "$4B GONE" + empty briefcase (GPU picture). $4B = DOJ SDNY 2023-09-12 + Reuters (F04).
- B "1¢ BACK" + fictional shocked man holding one coin (GPU picture). DERIVED: >$40M remission pool (F29) vs >$4B taken (F04), about 1 cent per dollar. Owner must approve the wording.
- C "VANISHED" + code-drawn coin dissolving into pixels (no GPU).

## Run
GitHub Actions -> thumbs -> ep. Output on branch `thumbs`: thumb_*.jpg, phone_mock.png, score.json, cost.json.
Score = contrast (35) + text size at 168x94 (35) + focal clarity (30); REVIEW below 75. The score is a floor, the owner decides.
