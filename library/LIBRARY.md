# Wisdrop channel library (the visual language)

Make once, reuse forever. A new episode only pays for what the library lacks.

## 1. Repertory cast (recurring fictional "actors")
- 8 to 10 fictional characters, each with ONE master sheet (full body, plain mid-grey
  background) and a pose library of 10 to 12 poses made from the master with
  Qwen-Image-Edit-2509 (same face, same outfit). Cutouts (transparent PNG) made on CPU.
- An episode casts from the repertory (the same tailor can be a saver in ep01 and a
  shop owner in ep07). Outfit tweaks are a new master variant, not a new person.
- Standard pose set (names fixed so render code can ask for them):
  front_neutral, three_quarter_left, three_quarter_right, walking, seated_phone_worried,
  seated_laptop, arms_crossed, hand_on_mouth_shock, pointing, head_in_hands,
  holding_document, back_view_looking_away.
- Real people are never drawn. A real figure is an empty spotlight, a silhouette
  doorway, or a document card.

## 2. Set library
- Each set has a base prompt and time/light variants (dawn, day, overcast, dusk, night,
  rain). Variants share seed and composition text so they read as the same place.
- Starter sets: tailor_shop, kitchen, event_stage, dev_flat, airport_hall,
  courthouse_ext, office_open_plan, bank_lobby, trading_floor, city_street,
  hotel_ballroom, police_interview, newsroom.
- Plates leave clear floor space where cast cutouts stand.

## 3. Props and evidence
- Evidence (numbers, quotes, headlines, documents, charts, maps, timelines) is drawn
  by code in render templates: free, sharp, always on-brand, always with SOURCE line.
- Small prop images (a coin, a phone, a suitcase) only when code can't draw them.

## 4. Motion grammar (code, no AI video)
- Push-in 4-8 %, slow lateral parallax (plate vs cutout), breathing 0.6 %, lamp flicker,
  rain, dust, film grain, light leaks; evidence: count-up 1.1 s, card slide 0.75 s,
  strike-through, highlighter. Cut at line start +0.04 s, 0.22 s eased cross-dip.

## 5. Sound palette (free, licensed in kit/)
- Music: kit/music (see ATTRIBUTION.txt). SFX: kit/sfx. Hits only on actions and numbers.
- Mix: voice -17 dB RMS, music ducks 4 dB under voice, master -14 LUFS / -2 dBTP.

## Files
- library/library.json: every cast member, pose, set and variant with its prompt and seed.
- Pictures live in Modal volume `wisdrop-assets` under lib/<kind>/<id>/<name>__<hash>.png.
  The hash covers model, LoRA, style text, prompt, seed and size, so a picture is only
  ever made again when one of those changes.
