# Slot-filling formulations tried with Jev

A record of every way we posed SNIPS slot filling to Jev, with its score,
including the ones that are not in the benchmark code.

## Setup

- **Dev set:** 700 utterances sampled from the SNIPS training split (seed 0,
  aligned rows only). Used for every comparison here so the test set was not
  tuned on.
- **Condition:** label descriptions on, gold intent given, so the numbers
  isolate slot filling. They are comparable with each other, not with the
  README's test figures, which use the predicted intent.
- **Metric:** span-level micro slot F1 (`seqeval`). "All slots right" is the
  share of utterances with every tag correct. Tokens are mean input tokens
  per utterance.
- **Model:** `jev-1.13.0`. Single runs; run-to-run noise is about half a
  point, so differences under one point are not meaningful. Formulation 6
  was run several times as the reference for later experiments: its two
  dev halves scored 76.2 and 77.8 in one run and 75.3 and 77.7 in another.
  Each table quotes the run made alongside that experiment.
- The **benchmark** runs formulation 6, token classification, and nothing
  else. Everything else here was a throwaway script, except formulation 12,
  which was a second benchmark method until it was removed.

## Results

### One question per word, options are slot types

Each word gets a `Choice` over the intent's slot types plus `none`. Adjacent
words with the same type form one span.

| #   | Formulation                                                            | Dev slot F1 | All slots right | Tokens |
| --- | ---------------------------------------------------------------------- | ----------- | --------------- | ------ |
| 1   | Word marked with brackets in a sentence; `none` last, undescribed      | 31.9        | 2%              | 2,445  |
| 2   | As 1, `none` listed first                                              | 32.9        | 2%              | —      |
| 3   | As 1, `none` given a description                                       | 60.0        | 24%             | 2,734  |
| 4   | As 3, `none` listed first                                              | 58.6        | 22%             | 2,734  |
| 5   | As 3, gaps of up to two words between same-type words filled           | 67.9        | 32%             | 2,734  |
| 6   | **Word and context as labelled fields, `none` described, gaps filled** | **76.4**    | **50%**         | 3,013  |

- **1** was the first benchmark version. Test: 26.0 slot F1 with names, 32.1
  with descriptions.
- **6** is the current **benchmark** token scheme. Test: 59.7 with names,
  76.4 with descriptions.
- Row 5 was tuned on half the dev set and is reported on the other half,
  where row 6 scores 77.8. Like for like, labelled fields gain about 10
  points over row 5, not 8.5.

Question wording:

- Rows 1–5: `The intent is {intent}. Which slot does the bracketed word fill
in: "add sabrina [salerno] to the playlist"? Answer none if it fills no
slot.`
- Row 6: instructions are the object `{intent, words_before, word,
words_after, question}` with the question ``Which slot does `word` fill in
`utterance`? Answer none if it fills no slot.`` and state
  `{"utterance": ...}`.
- `none` description: "The word is not part of any slot value: a command
  word, an article, a preposition, or other filler."

### One question per word, left to right

The same per-word question, asked one word at a time in sequence, so each
question can be shown what came before. One request per word.

| #   | Formulation                                                                          | Dev slot F1 | All slots right | Tokens |
| --- | ------------------------------------------------------------------------------------ | ----------- | --------------- | ------ |
| 7   | Whole utterance with the word bracketed, earlier labels shown; `none` undescribed    | 34.9        | 3%              | 4,874  |
| 8   | Only the words so far, last word bracketed, earlier labels shown; `none` undescribed | 45.3        | 13%             | 4,756  |
| 9   | As 8, `none` described and first                                                     | 52.5        | 21%             | 5,040  |
| 10  | Only the words so far, no bracket, "the last word"; `none` described; no labels      | 47.0        | 18%             | 4,680  |
| 11  | As 10, earlier labels shown                                                          | 22.2        | 6%              | 4,912  |

Earlier labels were shown as `The words before it are labelled: add (none),
sabrina (artist).`

### One question per slot, options are spans

Each slot type gets a `Choice` over the utterance's contiguous word spans
plus `none`. Overlapping answers are resolved by probability.

| #   | Formulation                                                        | Dev slot F1 | All slots right | Tokens |
| --- | ------------------------------------------------------------------ | ----------- | --------------- | ------ |
| 12  | **Sentence question, `none` last, undescribed**                    | 75.5        | 45%             | 5,084  |
| 13  | As 12, `none` listed first                                         | 77.2        | 47%             | —      |
| 14  | As 12, `none` described                                            | 75.6        | 45%             | —      |
| 15  | As 12, `none` first and described                                  | 76.2        | 45%             | —      |
| 16  | Instructions as labelled fields (`intent`, `field`, `question`)    | 76.2        | 41%             | 5,359  |
| 17  | As 12, asked only for slots a word-level question says are present | 75.3        | —               | ~4,000 |

- **12** follows the docs' extraction cookbook (code supplies candidates,
  Jev picks one or `none`). It was a second benchmark method and was
  removed. Test, three runs: 48.3 slot F1 with names, 72.2 with
  descriptions (frame accuracy 19.3 and 40.5), at 3.65M input tokens per
  run against 2.11M for token classification.
- Row 17 was estimated from saved answers by removing spans, without
  re-resolving overlaps, so it is a lower bound; its token figure is an
  estimate.
- Wording for 12: `The intent is {intent}. Which span of the utterance is
the {slot}? {description} Answer none if the utterance has no {slot}.`

### The function-calling cookbook's pattern

The docs' function-calling cookbook treats the intent as a function and each
slot as an argument. Per slot it asks a `stated` yes/no ("does the user say
anything about this?") and a value `Choice` whose question is written about
the idea, not the parameter name. Its arguments are closed sets; here the
options are the utterance's spans, with no `none`. A slot is filled when
`stated` is at least 0.5; overlaps go to the higher of
min(`stated`, value probability).

| #   | Formulation                                         | Dev slot F1 | All slots right | Tokens |
| --- | --------------------------------------------------- | ----------- | --------------- | ------ |
| 26  | `stated` yes/no plus a plainly worded span question | 66.7        | 25%             | 4,970  |

- Scored on the second half of the dev set, where formulation 12 scores
  74.8 and formulation 6 scores 77.8.
- Test, three runs with the benchmark's predicted intents: 66.9 slot F1
  (66.4–67.2), 29.1 frame accuracy (28.3–29.6), 3.58M input tokens per run.
- `stated` says yes for 13.9% of slot types the utterance does not use
  (formulation 12 answers with a span instead of `none` for 27%), but says
  no for 12.5% of the ones it does use (about 2% for formulation 12).
- The 53 question pairs were written for this test and replaced the slot
  descriptions, so the result reflects that wording as well as the pattern.
- Example, `city` under `GetWeather`: value question "Which city or town
  does the user want the weather for?", stated question "Does the user name
  a city or town, as opposed to a state or a country?"

### Combining two formulations

| #   | Formulation                                                                          | Dev slot F1 | All slots right | Tokens |
| --- | ------------------------------------------------------------------------------------ | ----------- | --------------- | ------ |
| 27  | Labels from 6; where a span from 12 holds only that type's words, use its boundaries | 79.8        | 55%             | 8,097  |
| 28  | As 27, with spans from 26 instead of 12                                              | 77.5        | 51%             | 7,983  |

Scored on the second half of the dev set (formulation 6: 77.8). On the first
half, 27 scores 78.9 against 76.2. The rule has no tuned parameters.

### Repairing boundaries after token classification

Formulation 6 gets 1,416 of the dev set's 1,804 gold spans exactly right. Of
the 388 it misses: 142 have some word given another slot type, 121 have the
right type but lack an edge word, 110 have the right type but are split by
unlabelled words in the middle, and 15 are missed entirely. The slot words
it labels `none` are mostly function words ("the" 99 of 301, "in" 33, "of"
23), and it is confident about them: median probability 0.88 for `none` and
0.09 for the correct slot.

| #   | Formulation                                                                             | Dev slot F1 | Tokens |
| --- | --------------------------------------------------------------------------------------- | ----------- | ------ |
| 6   | The benchmark decoder (gaps of up to two words filled)                                  | 77.7        | 3,013  |
| 29  | A `none` word next to a slot joins it when that slot's probability for the word is high | 77.7        | 3,013  |
| 30  | Most probable label sequence with a bonus for repeating the previous label (Viterbi)    | 77.7        | 3,013  |
| 31  | A yes/no per `none` word touching a predicted slot: "is it part of that value?"         | 77.7        | 3,657  |

- Second half of the dev set; settings tuned on the first half. In all three
  the tuning chose the setting that changes nothing. Any active setting
  scored lower: row 31 at a 0.5 threshold scores 68.4.
- Rows 29 and 30 use only the saved per-word probabilities. They cannot help
  because the missed words are not close calls.
- Row 31's yes/no was asked 2,207 times, 148 of which should be yes. At 0.5
  it says yes to 114 of those and to 314 that should be no.

### Few-shot examples

Formulation 6 plus examples drawn from training utterances that are not in
the dev set. Mean of the two halves of the dev set, where formulation 6
scores 76.5 (75.3 and 77.7).

| #   | Formulation                                       | Dev slot F1 | All slots right | Tokens |
| --- | ------------------------------------------------- | ----------- | --------------- | ------ |
| 32  | 3 labelled utterances of the intent in the state  | 78.0        | 51%             | 3,256  |
| 33  | 8 labelled utterances                             | 80.8        | 56%             | 3,671  |
| 34  | 16 labelled utterances                            | 81.6        | 57%             | 4,302  |
| 35  | **32 labelled utterances**                        | 83.3        | 60%             | 5,564  |
| 36  | 64 labelled utterances                            | 83.9        | 62%             | 8,184  |
| 37  | 3 example values in each slot option's `examples` | 79.0        | 54%             | 5,101  |
| 38  | 8 example values per slot option                  | 81.7        | 57%             | 6,992  |
| 39  | 16 example values per slot option                 | 81.8        | 58%             | 9,621  |

- **35** was the benchmark's first `fewshot` condition. Test, three runs
  with the predicted intent: 79.7 slot F1 (79.5–79.9), 54.3 frame accuracy
  (53.9–54.9), 3.92M slot input tokens per run. It was replaced by 41
  below.
- For 35, the test gain over descriptions is 3.3 points, about half the 6.8
  on dev.
  The two differ in the example sample (one seed each), in the dev set using
  the gold intent, and in the dev set being drawn from the same split as the
  examples. Only one example sample was run on test, so how much the result
  depends on which examples are drawn is not measured.
- A labelled utterance is `{"utterance": "play the best of abba", "slots":
[{"slot": "album", "value": "the best of"}, {"slot": "artist", "value":
"abba"}]}`, in a `labelled_examples` list in the state.
- Per slot on test, formulation 35 against descriptions: large gains where a slot
  takes a few fixed words (`object_part_of_series_type` 17 to 86,
  `current_location` 62 to 100, `movie_type` 75 to 99, `music_item` 62 to
  79); little change on titles (`album`, `track`, `entity_name`,
  `movie_name`); a large drop on `object_location_type` (85 to 46).
- SNIPS's training split contains 64 rows whose text equals one of 25 test
  utterances, with the same labels. They are excluded from the examples.

### Few-shot example format

Formulation 35 dropped `object_location_type` on test from 85 to 46 slot F1.
The cause was one boundary error: in "movie house" and "movie theatre" it
labelled the second word and left "movie" as `none` (probability of `none`
for that word 0.23 with descriptions, 0.58 with examples). The effect was
general: in run 1 on test, the first word of a multi-word slot was labelled
`none` in 123 of 780 cases with descriptions and 170 with formulation 35.

The examples in 35 show whole slot values, while the question asks about
one word. These variants change only how the same sampled utterances are
shown. Mean of the two dev halves; "first word" counts multi-word gold slots
on the whole dev set whose first word was labelled `none`.

| #   | Formulation                                                  | Dev slot F1 | First word | Tokens |
| --- | ------------------------------------------------------------ | ----------- | ---------- | ------ |
| 35  | 32 utterances, slots as whole values (re-run)                | 83.0        | 141        | 5,564  |
| 40  | 16 utterances, every word as `{"word", "slot"}`              | 83.4        | 128        | 6,158  |
| 41  | **32 utterances, every word as `{"word", "slot"}`**          | 85.3        | 118        | 9,250  |
| 42  | 64 utterances, every word as `{"word", "slot"}`              | 85.7        | 110        | 15,764 |
| 43  | 32 utterances, every word as a bare `[word, label]` pair     | 81.2        | 126        | 6,169  |
| 44  | 32 utterances, whole values and bare per-word pairs together | 85.3        | 117        | 8,840  |

- **41** is the benchmark's `fewshot` condition. Test, three runs: 83.5 slot
  F1 (83.4–83.6), 61.9 frame accuracy (61.6–62.3), 6.61M slot input tokens
  per run. `object_location_type` is back to 87, and the first word of a
  multi-word slot is labelled `none` in 118 of 780 cases in run 1.
- The test gain over descriptions is 7.1 points; the dev set predicted 8.8.
- Bare pairs (43) are worse than whole values. The labelled keys carry the
  meaning; the docs say Jev is trained on structure.
- An example in 41: `{"utterance": "play the best of abba", "words":
[{"word": "play", "slot": "none"}, {"word": "the", "slot": "album"}, ...]}`.

### One question per slot, options are words

Each slot type gets a `Choice` over the numbered words plus `none`
(`Which words of the utterance are the {slot}?`), and the answer is read
from the probabilities instead of the top choice alone.

| #   | Formulation                                                                          | Dev slot F1 | Tokens |
| --- | ------------------------------------------------------------------------------------ | ----------- | ------ |
| 18  | Top word only                                                                        | 48.6        | 1,303  |
| 19  | Top 2 words, span from first to last                                                 | 56.0        | 1,303  |
| 20  | Top 3 words, span from first to last                                                 | 48.5        | 1,303  |
| 21  | Top 5 words, span from first to last                                                 | 43.9        | 1,303  |
| 22  | Top 3 words with at least 10% of the top word's probability, span from first to last | 67.9        | 1,303  |
| 23  | Top word as anchor, then a second `Choice` over the spans that contain it            | 61.3        | 2,890  |

- Rows 18–22 are reported on the held-out half of the dev set; row 22's
  settings were tuned on the other half.
- The top word lies inside the gold span for 92.4% of present slots.

### Option rubrics for the token scheme

Formulation 6 with each slot option's description replaced by an object, as
in the docs' "Advanced: structure" page. `not_for` lines were written from
the label names, train values, and the word-level confusions on the first
half of the dev set; all three rows are scored on the second half.

| #   | Formulation                                                                                                     | Dev slot F1 | All slots right | Tokens |
| --- | --------------------------------------------------------------------------------------------------------------- | ----------- | --------------- | ------ |
| 6   | One-sentence descriptions (the benchmark)                                                                       | 77.8        | 51%             | 2,954  |
| 24  | `what` plus `not_for` naming the sibling slots                                                                  | 77.1        | 50%             | 4,354  |
| 25  | As 24, plus "every word counts" on multi-word slots and a `not_for` on `none` for words inside names and titles | 75.8        | 49%             | 5,128  |

Word-level errors on the second half of the dev set:

| #   | Word outside a slot given a slot | Slot word labelled `none` | Slot word given another slot |
| --- | -------------------------------- | ------------------------- | ---------------------------- |
| 6   | 78                               | 212                       | 83                           |
| 24  | 70                               | 211                       | 97                           |
| 25  | 107                              | 110                       | 101                          |

Example of a rubric option (row 25), for `object_name` under `RateBook`:
`{"what": "The title of the work being rated. Every word of it counts,
including small words such as articles and prepositions.", "not_for": "A
word that points to the work without naming it, or the kind of work."}`

## What we learned

- **Per-word labelling is the right shape, once it is posed well.** Each word
  has exactly one class and the slot types compete for it in one
  distribution. It ends up ahead of the span scheme on F1 and on fully
  correct utterances, at about 60% of the tokens (rows 6 and 12).
- **`none` needs a description.** With every slot described and `none` bare,
  55% of the words outside any slot were given a slot. Describing `none` cut
  that to 13% and nearly doubled F1 (rows 1 and 3). Where it sits in the
  list made no difference (rows 2 and 4).
- **Brackets inside a sentence are a poor way to point at a word.** The same
  question with the word and its context as labelled fields gained about
  10 points on the same half of the dev set (rows 5 and 6). The docs say Jev is trained on structure and reads
  instructions literally.
- **Feeding earlier labels back did not help.** It gave a small gain while
  `none` was broken (rows 1 and 7) and hurt once it was fixed (rows 3 and 9,
  10 and 11). It also costs one request per word.
- **Hiding the words to the right hurts.** A word like "the" cannot be
  labelled without what follows (rows 3 and 10).
- **The remaining boundary errors cannot be repaired after the fact.** Jev
  is confident that "the" or "of" inside a name is filler, so neither the
  saved probabilities nor a follow-up yes/no about the word recovers it
  (rows 29–31).
- **Examples teach what a description cannot, if they look like the
  question.** Utterances with every word labelled add 7 points on test;
  the same utterances shown as whole slot values add 3 and make Jev drop
  the first word of a phrase. The gain is mostly on slots with a few fixed
  values. Examples in the state are billed once per request: listed with
  their slot values they cost far less than example values repeated on
  every option (rows 35 and 38); with every word labelled they cost about
  as much as 16 example values per option (rows 41 and 39).
- **A `Choice` over words finds a slot but not its extent.** Probability
  concentrates on one head word, so long titles are truncated (rows 18–22).
  It is the cheapest formulation by a wide margin.
- **Splitting extraction into locate-then-extend lost to both simpler
  formulations** (row 23).
- **`what` / `not_for` rubrics did not help the token scheme.** Sibling
  confusions were never its main error: on the dev set, slot words labelled
  `none` (mostly small words inside titles) outnumber sibling mix-ups by more
  than two to one. Naming the siblings in `not_for` left every error type
  about where it was and cost 47% more tokens (row 24). Telling Jev that
  every word of a title counts halved the missed title words but pulled
  more outside words into slots, for a net loss (row 25).
- **The docs' patterns ask per field, and that is their weakness here.**
  Both cookbook patterns (rows 12 and 26) ask about each slot type on its
  own. On the test set, token classification beats them by 4 and 10 points
  of slot F1 at about 60% of the tokens.
- **A `stated` gate trades false proposals for misses** and loses overall
  (row 26).
- **Two formulations together beat either alone** (row 27), at 2.7 times the
  tokens of token classification. Not adopted.
- **The span question's errors are mostly sibling confusions.** Each slot is
  asked separately, so `city` and `state` both claim "mt" and code picks a
  winner. On the test set it proposed a span for a slot the utterance does
  not have in 27% of such questions. Moving or describing `none` did not
  change this (rows 13–15).

## Not tried

- Chunk first (a yes/no per gap between words), then one `Choice` per chunk.
- `what` / `not_for` rubrics on the span scheme, where sibling confusion is
  the main error. They were only tried on the token scheme.
- `examples` in the option rubrics.
- Several example samples on test, to measure how much few-shot depends on
  which utterances are drawn, and choosing examples similar to the utterance
  instead of at random.
- Using the top-k reading for confident slots and the span question for the
  rest.
- Treating slots with a few fixed values (`rating_unit`, `object_select`,
  `music_item`) as closed sets, as the function-calling cookbook does. It
  needs value lists from the training split.
- Rules about specific function words at span edges (for example always
  attaching a leading "the"). SNIPS is not consistent about these, so it
  would be tuning to the annotation.
