# RETENTION (how we keep viewers, and how we read the graph)

## Read the graph (YouTube Help, [Measure key moments for audience retention](https://support.google.com/youtube/answer/9314415), opened 2026-11-03)
- Data takes 1-2 days; key moments need a video >= 60 s with >= 100 views.
- **Intro** = share still watching after the first 30 s. Low intro: the first 30 s did not match the thumbnail/title promise -> fix packaging or the opening.
- **Flat** line = watched start to finish. **Gradual decline** = normal taper. **Spikes** = rewatched/shared (or unclear). **Dips** = skipped or quit.
- **Top moments** late in the video -> move that material earlier next time.
- Compare against your 10 latest videos of similar length (typical retention); segment new vs returning, subscribers vs not.

## Our rules (the machine checks most of them)
1. Hook: shock fact or striking visual inside 5 s (craft_check H1); question by 8 s (H2, owner script decision; hooks.md).
2. Thumbnail promise is paid off in the first 30 s (the intro metric above).
3. A visual change every <= 3 s in the first minute (P2); nothing still > 2.5 s anywhere (P1).
4. One open loop per part, closed later (score_script); each chapter card re-hooks with a question.
5. Best material early: if a top moment shows up late in analytics, reorder the next episode's outline.
6. v4 fx are punctuation, not wallpaper: glitch only on crypto beats (max 4), light leak only between parts, parallax/line-art for story photos.
7. End screen in the last 20 s, never a "thanks for watching" dead stretch before it.

## After each episode (5 minutes, owner or AI)
- Note intro %, average view duration, the biggest dip (timestamp -> which shot in shots.json), the top moment.
- Write one line per finding in `episodes/<ep>/qa/retention_notes.md` and one rule change in docs/EDITING_CRAFT.md if a pattern repeats twice.
