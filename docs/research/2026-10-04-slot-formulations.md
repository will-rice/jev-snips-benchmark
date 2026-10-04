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
  point, so differences under one point are not meaningful.
- Formulations marked **benchmark** are implemented in `src/jevsnips/` and
  have test-set results in the README. The rest were throwaway scripts.

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
- Row 5 was tuned on half the dev set and is reported on the other half.

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

- **12** is the **benchmark** span scheme. Test: 48.3 with names, 72.2 with
  descriptions.
- Row 17 was estimated from saved answers by removing spans, without
  re-resolving overlaps, so it is a lower bound; its token figure is an
  estimate.
- Wording for 12: `The intent is {intent}. Which span of the utterance is
the {slot}? {description} Answer none if the utterance has no {slot}.`

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
  question with the word and its context as labelled fields gained 8.5
  points (rows 5 and 6). The docs say Jev is trained on structure and reads
  instructions literally.
- **Feeding earlier labels back did not help.** It gave a small gain while
  `none` was broken (rows 1 and 7) and hurt once it was fixed (rows 3 and 9,
  10 and 11). It also costs one request per word.
- **Hiding the words to the right hurts.** A word like "the" cannot be
  labelled without what follows (rows 3 and 10).
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
- **The span scheme's errors are mostly sibling confusions.** Each slot is
  asked separately, so `city` and `state` both claim "mt" and code picks a
  winner. On the test set it proposed a span for a slot the utterance does
  not have in 27% of such questions. Moving or describing `none` did not
  change this (rows 13–15).

## Not tried

- Chunk first (a yes/no per gap between words), then one `Choice` per chunk.
- A yes/no presence gate per slot before the span question.
- `what` / `not_for` rubrics on the span scheme, where sibling confusion is
  the main error. They were only tried on the token scheme.
- `examples` in the option rubrics.
- Example values from the training split in the descriptions (few-shot).
- Using the top-k reading for confident slots and the span question for the
  rest.
