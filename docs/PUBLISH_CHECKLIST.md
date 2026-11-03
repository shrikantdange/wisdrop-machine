# PUBLISH CHECKLIST (owner uploads; the AI prepares and checks)

Sources actually opened on 2026-11-03 are linked. Anything not from these pages is our own rule.

## Before upload (machine + AI)
- [ ] FINAL REVIEW PR merged by the owner (video + thumbnail + title + description). Never approve for the owner.
- [ ] `summary.json`: status success, failed_checks empty. `audio_qc.json` ok (-14 LUFS, true peak <= -1 dBTP).
- [ ] Every number on screen and in narration is in research.md (key numbers twice). Derived numbers (e.g. "1¢ back") approved by the owner.
- [ ] No real person drawn anywhere (cast are fictional composites; real people only as names on cards/headlines).
- [ ] Photo credits + music/SFX attribution in the description (fetch_media credits.json, kit/music/ATTRIBUTION.txt).
- [ ] Thumbnail: designed (docs/THUMBNAILS.md), 16:9, JPG/PNG, under 2 MB if uploading from a phone; recommended 3840x2160, min width 640 ([Add custom thumbnails](https://support.google.com/youtube/answer/72431)). Thumbnails must not show violence or harmful content (strike risk, same page).
- [ ] Prepare 3 different thumbnails for Test & compare (winner = most watch time). Source: [A/B test titles & thumbnails](https://support.google.com/youtube/answer/13861714) (seen as search excerpt this run; open it before relying on details).
- [ ] Title accurate, short, key words first, episode number/branding at the end; limit ALL CAPS ([Thumbnail & title tips](https://support.google.com/youtube/answer/12340300)).

## AI disclosure ([Disclosing use of GenAI content](https://support.google.com/youtube/answer/14328491))
YouTube requires disclosure of realistic AI content, e.g. a realistic scene that did not happen, or altered footage of a real place.
Not required for non-realistic/animated content or production help (script, thumbnail, infographic ideas).
Our case: the story scenes are AI illustrations of fictional composites (Rosa, Dee, Victor, Theo) in a stylised noir poster look,
and the narrator voice is synthetic. **Decision for the owner** (open item): we recommend answering **Yes** under Attributes -> "AI use"
because composite characters act out real events and the voice is synthetic; disclosure alone "won't limit a video's audience or impact
its eligibility to earn money" (same page). Never leave it ambiguous: consistent non-disclosure risks labels or penalties (same page).

## In Studio at upload
- [ ] Attributes -> AI use: as decided above.
- [ ] Audience: not made for kids (end screens are unavailable on made-for-kids videos, [Add end screens](https://support.google.com/youtube/answer/6388789)).
- [ ] Chapters: description timestamps from package/description.txt (00:00 first).
- [ ] End screen: video is >= 25 s; use the last 5-20 s; up to 4 elements on 16:9. Place Video element on the WATCH NEXT box and Subscribe on the circle (docs/SHOTS.md T28). Viewers can hide end screens; not shown on mobile web ([Add end screens](https://support.google.com/youtube/answer/6388789)).
- [ ] Custom thumbnail uploaded (account must be verified, [Add custom thumbnails](https://support.google.com/youtube/answer/72431)), then Test & compare with the other 2.

## After upload (first 24 h)
- [ ] Check CTR on Home and Suggested in the first 24 h for general audiences; Subscriptions feed CTR for subscribers ([Thumbnail & title tips](https://support.google.com/youtube/answer/12340300)).
- [ ] After 1-2 days: audience retention report (docs/RETENTION.md).
