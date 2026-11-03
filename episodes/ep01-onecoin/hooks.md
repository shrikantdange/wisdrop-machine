# ep01 hook bank (3 alternative openings, scored) - FOR OWNER APPROVAL

The approved script is unchanged. The current opening scores **59/100**: its shock beat lands at ~5.9 s and its first question at ~27 s (craft rule H2 wants a question by 8 s). Pick one option below (or keep the current one) and the operator updates lines.json and re-voices only the changed lines.

Scores come from `python machine/score_script.py episodes/ep01-onecoin --hooks` (shock fact <= 5 s, question <= 8 s, promise <= 15 s, short sentences, little jargon). Every fact cites research.md.

## A numbers first - score 87/100

- More than four billion dollars.  *(F04)*
- At least three and a half million people.  *(F04)*
- And a coin with no real blockchain behind it.  *(F10)*
- So how do you sell millions of people a coin that never existed?  *(F10)*
- This is the story of OneCoin, told through one saver who believed in it.

## B flight question - score 79/100

- On October twenty-fifth, twenty seventeen, a woman boarded a flight from Sofia to Athens.  *(F01)*
- Where did she go?  *(F01)*
- Five years later, she was on the F.B.I.'s Ten Most Wanted list.  *(F03)*
- Her company, OneCoin, had taken in more than four billion dollars.  *(F04)*
- This is how she did it, and who paid for it.

## C second person - score 92/100

- What if the coin you bought never existed?  *(F10)*
- For at least three and a half million people, that was OneCoin.  *(F04)*
- Together they handed over more than four billion dollars.  *(F04)*
- Then its founder boarded a flight from Sofia to Athens, and vanished.  *(F01)*
- This is how the scam worked, and why so many believed it.

Recommendation: **C** scores highest (question in the first second, shock fact at once, promise by ~17 s). **B** keeps the approved first line and adds one question, so it changes the least.
