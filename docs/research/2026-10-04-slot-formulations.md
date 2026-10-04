# Slot-filling formulations tried with Jev

A record of every way we posed SNIPS intent detection and slot filling to
Jev, with its score, including the ones that are not in the benchmark code.

## Summary

The benchmark ended up with token classification (formulation 6), examples
shown with a label for every word (41), retrieved by TF-IDF similarity for
the slot request (46) and for the intent request (57), with the slot
definitions in the state and the question pointing at the examples (65),
a definition for every slot written about one word at a time (72), and
intent options that carry their slots' definitions (78). On the test set
that takes slot F1 from 59.7 with label names alone to 86.8 with
definitions and 91.2 with retrieved examples.

The path there, in the order it was walked:

| Step                                                                          | Test slot F1 |
| ----------------------------------------------------------------------------- | ------------ |
| Per-word question with a bracketed word, label names only                     | 26.0         |
| The same with label descriptions                                              | 32.1         |
| Per-slot question over candidate spans, with descriptions                     | 72.2         |
| Per-word question as labelled fields, `none` described, gaps filled           | 76.4         |
| 32 fixed examples, slots shown as whole values                                | 79.7         |
| 32 fixed examples, every word labelled                                        | 83.5         |
| 8 examples retrieved by similarity, for the slot request                      | 86.2         |
| Retrieved examples for the intent request as well                             | 86.9         |
| Slot definitions in the state, question pointing at the examples              | 89.4         |
| Every definition rewritten, word by word, with a `none` definition per intent | 90.7         |
| Intent options that include their slots' definitions                          | 91.2         |

Things that were tried and did not help: feeding earlier labels back,
hiding the words to the right, `what` / `not_for` rubrics, a `stated` yes/no
per slot in place of a `none` option, reading the top few words of a per-slot question, repairing span
boundaries after the fact, more than eight retrieved examples,
deduplicating the retrieval pool, embedding similarity, reordering the slot
options, a yes/no per adjacent word pair, and rewording the question.

The largest single gain came late and from the least exotic change: writing
the slot definitions properly. With no examples shown, slot F1 on test went
from 76.4 to 86.1.

The sections below are grouped by kind of formulation, not by date.

## Setup

- **Dev set:** 700 utterances sampled from the SNIPS training split (seed 0,
  aligned rows only). Used for every comparison here so the test set was not
  tuned on.
- **Condition:** unless a section says otherwise, label descriptions on and
  gold intent given, so the numbers isolate slot filling. They are
  comparable with each other, not with the README's test figures, which use
  the predicted intent.
- **Metric:** span-level micro slot F1 (`seqeval`). "All slots right" is the
  share of utterances with every tag correct. Tokens are mean input tokens
  per utterance.
- **Model:** `jev-1.13.0`. Single runs; run-to-run noise is about half a
  point, so differences under one point are not meaningful. Formulation 6
  was run several times as the reference for later experiments: its two
  dev halves scored 76.2 and 77.8 in one run and 75.3 and 77.7 in another.
  Each table quotes the run made alongside that experiment.
- The **benchmark** code contains formulations 57, 65, 67, 72 (6 with
  rewritten definitions), and 78 (intent options with their slots).
  Everything else here was a throwaway script, except formulations that
  were in the benchmark for a time and then removed: 12 (a second slot
  method), 81 and 84 (span formulations added as conditions and removed
  the same day), 35 and 41 (earlier few-shot formats), and 46 (the
  retrieved slot request before 65). Their test figures below are from
  when they were current.
- The dev set is drawn from the same split as the few-shot examples, and it
  overstated every example-based gain. Each change was confirmed on the test
  set before it was kept; test figures are given where they exist.

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
  76.4 with the one-sentence descriptions it was first run with (86.8 with
  the current definitions, 72 and 78).
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

- **12** takes its question shape from the docs' value-extraction cookbook:
  Jev picks one of the candidates or `none`. In the cookbook, code finds
  the candidates with a pattern such as a regular expression. SNIPS slots
  have no such pattern, so here the candidates were every span of words.
  That substitution is ours; the docs do not describe it. 12 was a second
  benchmark method and was removed. Test at the time, three runs: 48.3
  slot F1 with names, 72.2 with descriptions (frame accuracy 19.3 and
  40.5), at 3.65M input tokens per run against 2.11M for token
  classification.
- Row 17 was estimated from saved answers by removing spans, without
  re-resolving overlaps, so it is a lower bound; its token figure is an
  estimate.
- Wording for 12: `The intent is {intent}. Which span of the utterance is
the {slot}? {description} Answer none if the utterance has no {slot}.`

### A `stated` yes/no per slot, after the function-calling cookbook

The docs' function-calling cookbook treats a request as a function call. For
each argument it asks a `stated` yes/no ("does the user say anything about
this?") and a value `Choice` whose question is written about the idea, not
the parameter name. Its arguments take values from fixed lists, and it gives
free text, numbers, and dates no question at all. Formulation 26 borrows
the two questions and applies them to SNIPS slots, which are mostly free
text, with the utterance's spans as the options and no `none`. That is our
adaptation, not the cookbook's pattern. A slot is filled when `stated` is
at least 0.5; overlaps go to the higher of min(`stated`, value
probability).

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
  descriptions, so the result reflects that wording as well as the formulation.
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

- **41** was the benchmark's `fewshot` condition until 67 replaced it. Test,
  three runs: 83.5 slot F1 (83.4–83.6), 61.9 frame accuracy (61.6–62.3),
  6.61M slot input tokens per run. `object_location_type` was back to 87,
  and the first word of a multi-word slot was labelled `none` in 118 of 780
  cases in run 1.
- For 41, the test gain over descriptions was 7.1 points; the dev set
  predicted 8.8.
- Bare pairs (43) are worse than whole values. The labelled keys carry the
  meaning; the docs say Jev is trained on structure.
- An example in 41 is the utterance text plus a `words` list with one
  `{"word": "the", "slot": "album"}` entry per word.

### Choosing the examples

Prompted by the in-context example selection literature (KATE, Liu et al.
2021; retrieval for few-shot intent and slot filling, Yu et al. 2021), which
finds that examples similar to the input beat a fixed or random set.

Formulation 41 with the examples chosen per utterance: the `k` training
utterances of the intent most similar to it, by TF-IDF cosine over words and
adjacent word pairs. The pool is every aligned training utterance of the
intent that is not in the dev set (about 1,750 per intent). Mean of the two
dev halves.

| #   | Formulation                                                                   | Dev slot F1 | All slots right | Tokens |
| --- | ----------------------------------------------------------------------------- | ----------- | --------------- | ------ |
| 41  | 32 fixed utterances (for reference)                                           | 85.3        | 64%             | 9,250  |
| 45  | 4 most similar utterances                                                     | 87.6        | 70%             | 3,739  |
| 46  | **8 most similar utterances**                                                 | 89.5        | 75%             | 4,474  |
| 47  | 16 most similar utterances                                                    | 89.4        | 75%             | 5,981  |
| 48  | 32 most similar utterances                                                    | 89.6        | 75%             | 9,048  |
| 49  | 8 most similar utterances, no descriptions                                    | 89.0        | 75%             | 3,059  |
| 50  | 32 fixed utterances, no descriptions                                          | 84.7        | 63%             | 7,834  |
| 51  | No Jev: copy each word's most common label from the 8 most similar utterances | 72.0        | 29%             | 0      |

- **46** was the slot half of the benchmark's `retrieved` condition until
  65 replaced it. Test, three runs with the intent predicted from
  descriptions alone: 86.2 slot F1 (85.9–86.5), 68.2 frame accuracy
  (67.9–68.6), 3.14M slot input tokens per run. With retrieved examples for
  the intent as well (row 57), it was 86.9 and 69.5. The pool on test is the
  12,833 distinct aligned training utterances whose text is not a test
  utterance.
- For 46 against 41, the test gain over fixed few-shot was 2.7 points; the
  dev set predicted 4.2. Dev utterances come from the same split as the pool, so their nearest
  neighbours are closer than a test utterance's.
- On dev the nearest example has a mean cosine of 0.51 with the utterance,
  and 4% of utterances have one at 0.8 or above, so this is not copying from
  exact near-duplicates. Row 51 confirms it: label copying from the same
  examples is 17.5 points behind.
- SNIPS utterances are templated, though. On test, 86 of the 700 utterances
  (12%) retrieve at least one example exactly one word away ("what movies
  are playing at mann theatres" against "... amc theatres"), and most of
  those examples have the same tag sequence. The top-1 cosine on test has
  mean 0.50, with 4.4% at 0.8 or above and none at 1.0.
- **Repeated texts in the pool made no measurable difference.** The
  training split repeats 147 utterance texts (186 extra copies), so at
  first 18% of test utterances were shown the same example twice among
  their 8. Indexing only the first copy of each text gives everyone 8
  distinct examples. On test, three runs each: 86.2 slot F1 before
  (86.1–86.3) and after (85.9–86.5), frame accuracy 68.0 before and 68.2
  after. The benchmark keeps the deduplicated index, since it is what "the
  8 most similar" should mean. One repeated text has copies with different
  labels; the first copy's labels are the ones shown. The dev-set rows above
  were measured before this change.

### Retrieved examples for the intent

Every change above was to the slot request. The intent request was the
zero-shot one in all conditions. This shows it examples too: the `k`
training utterances most similar to the utterance, from all intents, each as
`{"utterance", "intent"}`, in a `labelled_examples` list beside the
utterance. Intent descriptions are kept. Dev set, 700 utterances.

| #   | Intent question                                      | Dev intent accuracy | Wrong | Tokens |
| --- | ---------------------------------------------------- | ------------------- | ----- | ------ |
| 55  | Descriptions only (all conditions until now)         | 96.1                | 27    | 481    |
| 56  | Descriptions and the 4 most similar utterances       | 98.7                | 9     | 623    |
| 57  | **Descriptions and the 8 most similar utterances**   | 98.7                | 9     | 750    |
| 58  | Descriptions and the 16 most similar utterances      | 98.7                | 9     | 1,006  |
| 59  | No Jev: the most common intent of the 8 most similar | 93.7                | 44    | 0      |

- **57** is the intent half of the benchmark's `retrieved` condition. Test,
  three runs, with slot request 46: intent accuracy 96.1 (27 wrong of 700,
  identical in all three runs) against 95.1 without examples; slot F1 86.9
  (86.7–87.2) against 86.2; frame accuracy 69.5 (69.0–70.4) against 68.2. Intent input tokens rise
  from 336,703 to 524,801 per run.
- The dev set overstated the gain again: 2.6 points there, 1.0 on test.
- Of the 27 intent errors left on test, 26 are among three intents that
  overlap in meaning: `SearchScreeningEvent` read as `SearchCreativeWork`
  (10), `SearchCreativeWork` read as `PlayMusic` (8) or as
  `SearchScreeningEvent` (6), and `PlayMusic` read as `SearchCreativeWork`
  (2).
- How much the examples give away, on test: 88% of the retrieved examples
  carry the utterance's gold intent, and for 66% of utterances all 8 share
  one intent (the gold one in all but 3 cases). A majority vote among the 8
  is right for 93.6% of utterances. Where the majority was wrong (45
  utterances), Jev was still right in 26. No retrieved example is a test
  utterance; 12% of utterances retrieve one that differs by a single word.
- Jev with examples beats both Jev alone and a vote among the examples (row
  59), so it is weighing them, not copying.

### Rewriting every definition

Until this point every experiment used the first set of definitions: one
sentence per slot saying what the slot is ("The title of the album to
play."), and one `none` definition shared by all intents. They had been
written once and never revisited.

**Setup.** New training-only splits, disjoint from the dev set and the test
set: per intent, 200 "search" utterances to write against and 100 "check"
utterances to confirm on. The per-word question is unchanged. Scores use
the gold intent.

**Question wording first.** Seven wordings of the per-word question were
scored on 500 training utterances. None beat the current one (79.0): the
alternatives scored 64.7 to 78.0. Four wordings of the shared `none`
definition ranged from 77.5 to 80.0.

**A partial rewrite.** Rewriting 14 definitions for the most confused slots
scored 82.9 on dev and 82.1 slot F1 and 60.8 frame accuracy on test. It was
not kept, because it left the other 39 definitions as first drafts.

**The full pass.** For each intent: read the word-level errors on its
search utterances, write a definition for every slot and a `none`
definition for that intent, score, and revise once more against the errors
that remained. The definitions follow three rules that came out of the
errors:

- Say what one word must be, since the question is about one word: "A word
  of the title of an album", not "The title of the album".
- Name typical words, and the words that look similar but do not count:
  `music_item` is "song, track, album ... Not the general words music,
  songs, tunes".
- State SNIPS's boundary conventions: "The word playlist or list that
  follows the name is not part of it"; "In this current book only current
  counts".

Slot F1 and share of utterances with every word right, on each intent's 200
search utterances:

| Intent               | One-sentence definitions | First full pass | Second pass |
| -------------------- | ------------------------ | --------------- | ----------- |
| AddToPlaylist        | 64.4, 34%                | 81.1, 64%       | 83.3, 67%   |
| BookRestaurant       | 84.0, 63%                | 87.4, 67%       | 88.9, 72%   |
| GetWeather           | 84.7, 70%                | 92.7, 85%       | 93.5, 86%   |
| PlayMusic            | 76.9, 39%                | 89.2, 76%       | 91.3, 81%   |
| RateBook             | 87.5, 59%                | 92.7, 77%       | 93.1, 78%   |
| SearchCreativeWork   | 76.6, 62%                | 85.7, 73%       | 86.2, 73%   |
| SearchScreeningEvent | 62.6, 37%                | 90.1, 78%       | 89.8, 78%   |

On utterances not used for writing, all intents together, gold intent:

| #   | Definitions                                       | Check set (700) | Dev set (700) | Tokens |
| --- | ------------------------------------------------- | --------------- | ------------- | ------ |
| 6   | One sentence per slot, shared `none`              | 78.2, 52%       | 76.3, 50%     | 3,013  |
| 70  | 14 definitions rewritten                          | —               | 82.9, 62%     | 3,398  |
| 72  | **Every definition rewritten, `none` per intent** | 90.3, 76%       | 89.5, 76%     | 5,791  |
| 73  | 72 held once in the state, options bare           | —               | 88.5, 72%     | 2,172  |

- **72** is the benchmark's definitions. Test, three runs each, against the
  previous definitions:

  | Condition    | Slot F1      | Frame accuracy | Slot input tokens      |
  | ------------ | ------------ | -------------- | ---------------------- |
  | Descriptions | 76.4 to 86.1 | 49.9 to 68.6   | 2,113,624 to 4,065,054 |
  | Few-shot     | 84.4 to 87.2 | 64.8 to 72.4   | 5,905,086 to 6,113,746 |
  | Retrieved    | 89.4 to 90.7 | 75.7 to 78.6   | 2,440,043 to 2,649,167 |

- With definitions alone the benchmark now scores about what 32 fixed
  examples used to add, and fixed examples add little on top (86.1 to
  87.2). Retrieved examples still add 4.6 points.
- The descriptions condition nearly doubles in tokens, because longer
  definitions are sent with every word. Holding them in the state (73) costs
  a point of slot F1 and four of frame accuracy for 62% fewer tokens; the
  benchmark keeps them on the options when no examples are shown.
- What still resists, by the search-set errors: telling an album title from
  a track title with nothing in the utterance to say which; whether a
  leading "the" belongs to a title, which SNIPS labels both ways; places
  that could be a city or a point of interest.
- The definitions were written against labelled training utterances and
  contain typical values and dataset conventions. The descriptions condition
  shows no example utterances, but it is not free of knowledge of the data.

### Intent definitions that describe the slots

The intent request had kept its first definitions, one sentence per intent,
while the slots got full ones. What separates neighbouring intents is mostly
which slots an utterance fills, so the intent options were given the slot
definitions too. Zero-shot intent request, accuracy on the training-only
search (1,400) and check (700) utterances:

| #   | Intent option                                                          | Search | Check |
| --- | ---------------------------------------------------------------------- | ------ | ----- |
| —   | One sentence per intent (as before)                                    | 96.57  | 96.43 |
| 74  | `{"what": sentence, "slots": the first one-sentence slot definitions}` | 96.50  | —     |
| 75  | `{"what": sentence, "slots": [slot names]}`                            | 96.43  | —     |
| 76  | One paragraph: the sentence, then the slots listed in prose            | 97.00  | —     |
| 77  | `{"what": sentence, "slots": the full slot definitions}`               | 97.36  | 97.29 |
| 78  | **77 with `what` rewritten to say what tells the intent apart**        | 97.86  | 97.57 |
| 79  | The rewritten `what` alone                                             | 97.71  | 97.00 |

- Slot names, or one-sentence slot definitions, do nothing (74, 75). The
  full word-level definitions do (77): they say which words signal a slot.
- The rewritten `what` states the boundary with the neighbouring intents,
  for example `SearchCreativeWork`: "Choose this when the request gives only
  a title, with or without its kind, even if it says play, listen or watch,
  and names no artist, streaming service, cinema or showtime."
- **78** is in the benchmark. Test, three runs each, against one sentence
  per intent:

  | Condition    | Intent accuracy | Slot F1      | Frame accuracy | Intent input tokens  |
  | ------------ | --------------- | ------------ | -------------- | -------------------- |
  | Descriptions | 95.1 to 95.6    | 86.1 to 86.8 | 68.6 to 69.5   | 336,703 to 2,470,303 |
  | Few-shot     | 95.0 to 95.6    | 87.2 to 87.7 | 72.4 to 73.0   | 336,703 to 2,470,303 |
  | Retrieved    | 96.2 to 96.9    | 90.7 to 91.2 | 78.6 to 79.4   | 524,801 to 2,658,401 |

- The gain on test is about half the gain on the training splits, and it
  costs 2.1M input tokens per run, because the seven options now hold all
  53 slot definitions.
- What is left is mostly `SearchScreeningEvent` read as `SearchCreativeWork`
  ("find fish story") and `SearchCreativeWork` read as `PlayMusic`. Several
  of these are ambiguous or mislabelled in SNIPS.

### Span formulations as benchmark conditions, added and removed

Formulations 12 and 26 had been run with throwaway scripts. For a day they
were conditions of the benchmark, named `extraction` and `function_calling`
and described as the Jev docs' patterns. They were removed: the benchmark's
method is token classification, and the description was wrong. As noted
under 12 and 26, the docs' cookbooks pick among candidates found by pattern
or among fixed lists; offering every span of words is our substitution. The
code and its saved runs are in the repository's history at commit
`bdad347`. Each slot had a one-sentence definition from the first set of
definitions and the question pair written for formulation 26.

In the table, "pick or none" is formulation 12's shape and "stated" is
26's. Wordings were compared on the dev set with the gold intent before the
test runs:

| #   | Shape        | Value question                                                                  | Dev slot F1 | All slots right | Tokens |
| --- | ------------ | ------------------------------------------------------------------------------- | ----------- | --------------- | ------ |
| 80  | Pick or none | The question about the idea only ("Which musician or band ...?")                | 67.6        | 29%             | 4,999  |
| 81  | Pick or none | **Formulation 12's sentence: intent, slot name, definition, "Answer none ..."** | 75.1        | 46%             | 5,224  |
| 82  | Pick or none | Labelled fields `{"question", "definition"}`                                    | 69.7        | 31%             | 5,171  |
| 83  | Pick or none | Idea question, definition, "Answer none if the utterance does not say."         | 71.5        | 36%             | 5,156  |
| 84  | Stated       | **Idea question followed by the definition, plus `stated`**                     | 70.7        | 32%             | 5,046  |
| 85  | Stated       | Formulation 12's sentence without the `none` clause, plus `stated`              | 71.6        | 37%             | 5,107  |

- **81** and **84** were the two conditions. 85 scores a point higher than
  84 but names the question after the slot, which the function-calling
  cookbook advises against for its own questions.
- Naming the slot and defining it is worth 7.5 points to the pick-or-none
  question (80 against 81). The cookbook's advice to ask about the idea and
  not the parameter name fits its closed sets, where each option has its
  own description. With spans as options the question is the only place a
  definition can go.
- Test, three runs each, with the benchmark's intent request:

  | Condition                           | Slot F1          | Frame accuracy   | Slot input tokens |
  | ----------------------------------- | ---------------- | ---------------- | ----------------- |
  | Descriptions (token classification) | 86.8 (86.6–86.9) | 69.5 (69.3–69.9) | 4,062,064         |
  | Pick or none over spans (81)        | 72.7 (72.5–72.8) | 41.5 (41.1–41.7) | 3,750,174         |
  | Stated plus a span question (84)    | 69.6 (69.2–69.9) | 32.5 (31.7–33.0) | 3,626,549         |

- A first test run of both with the bare idea question (80, and 26
  as originally written) scored 66.8 and 66.9.
- On utterances with the intent right, the decoded output leaves 18.5%
  (81) and 22.2% (84) of the slot types an utterance
  uses unfilled, and fills 4.4% and 5.7% of the ones it does not use. Token
  classification: 4.2% and 2.7%.
- The efforts are not equal. The per-word definitions were revised against
  training utterances; the span questions' definitions are the first drafts.
  With those same first drafts token classification scored 76.4 on test, so
  about 4 points of the gap is the formulation and the rest is the
  definitions. Nobody has written span-level definitions with the same
  care.
- Saved probabilities leave out options scored 0.00, a change made when a
  span question's 255 options made a run's file about 10 MB. It was kept
  after the span conditions were removed; the saved runs are in that form.

### A full read of the Jev docs

All 58 pages of the Jev documentation, and the vendor's agent skill, were
read against the implementation. Most guidance was already followed. These
are the ideas that were new, each tried on the whole dev set with 8
retrieved examples (formulation 46) unless noted.

| #   | Formulation                                                                                           | Dev slot F1 | All slots right | Tokens |
| --- | ----------------------------------------------------------------------------------------------------- | ----------- | --------------- | ------ |
| 46  | 8 most similar utterances (re-run)                                                                    | 88.8        | 73%             | 4,481  |
| 60  | Slot options in reversed order                                                                        | 88.9        | 73%             | 4,481  |
| 61  | Slot options shuffled per utterance                                                                   | 88.9        | 73%             | 4,481  |
| 62  | Probabilities averaged over four option orders                                                        | 88.8        | 73%             | 17,924 |
| 63  | The question also says to label the word "the way matching words are labelled in `labelled_examples`" | 90.3        | 77%             | 4,616  |
| 64  | Slot definitions once in the state under `slot_definitions`, options bare, question names that key    | 90.6        | 78%             | 3,343  |
| 65  | **63 and 64 together**                                                                                | 91.4        | 80%             | 3,478  |
| 66  | 65 without any slot definitions                                                                       | 89.6        | 75%             | 3,201  |
| 67  | **65 with the 32 fixed examples** (41 re-run scores 84.4)                                             | 86.1        | 67%             | 8,395  |
| 68  | 64 without examples (formulation 6 re-run scores 77.1, 50% all right)                                 | 76.4        | 46%             | 1,874  |
| 69  | 46 plus a yes/no per adjacent word pair, joined words take the neighbour's slot                       | 88.8        | 73%             | 5,297  |

- **65 and 67** are the benchmark's `retrieved` and `fewshot` slot requests.
  Test, three runs each. Retrieved: 89.4 slot F1 (89.1–89.5) and 75.7 frame
  accuracy (75.1–76.1), from 86.9 and 69.5, with slot input tokens down from
  3.14M to 2.44M per run. Few-shot: 84.4 (84.4–84.5) and 64.8 (64.6–65.1),
  from 83.5 and 61.9, with tokens down from 6.61M to 5.91M.
- **Option order (60–62).** The docs list it as a failure mode and say to
  reorder and check. About 1% of words get a different answer; no score
  moves. The results do not depend on option order.
- **Definitions in the state (64, 68).** The state is billed once per
  request, and the docs put shared reference text there. With examples it is
  both cheaper and more accurate. Without examples it is cheaper but loses
  frame accuracy, so the `descriptions` condition keeps definitions on the
  options.
- **Word pairs (69).** Modelled on the docs' structure-recovery cookbook,
  which asks a yes/no per adjacent pair of lines. The judgement is too
  unreliable here: of 1,507 pairs that belong together it finds 1,381, but
  it also joins 596 of the 4,100 that do not. No threshold beats leaving the
  labels alone.
- **The intent question** was tried with the same two changes: pointing at
  the examples (10 wrong of 700, against 9) and definitions in the state
  (7 wrong). Neither is outside the noise, so it is unchanged.
- **Housekeeping from the docs:** the model is pinned to `jev-1.13.0`
  instead of the `jev-latest` alias, which "moves when a new release ships",
  and the question wording is collected in one place in `jev.py`.
- **Not adopted:** the docs recommend one request with every question,
  ignoring answers that do not apply. The slot request's options,
  definitions, and examples depend on the predicted intent, which is the
  exception the docs allow, and a single request would cost about seven
  times the slot tokens.

### How similarity is measured

Formulation 46 with a different similarity for choosing the 8 examples.
Embeddings are of the utterance text, L2-normalised, compared by cosine.
The hybrid adds the embedding cosine to the TF-IDF cosine. The pool is
deduplicated. Both dev halves are shown, since the differences are small.

| #   | Similarity                                           | Dev slot F1, half A / B | All slots right, A / B |
| --- | ---------------------------------------------------- | ----------------------- | ---------------------- |
| 46  | **TF-IDF over words and word pairs** (the benchmark) | 88.6 / 90.3             | 72% / 77%              |
| 52  | Embedding, `sentence-transformers/all-MiniLM-L6-v2`  | 87.7 / 88.8             | 70% / 73%              |
| 53  | Embedding, `BAAI/bge-base-en-v1.5`                   | 88.4 / 88.5             | 72% / 73%              |
| 54  | Hybrid of 46 and 52                                  | 87.7 / 90.3             | 70% / 77%              |

- Embedding similarity is about a point below TF-IDF, which is close to the
  noise on this dev set. It is not better, and it would add a model download
  and a PyTorch dependency, so it was not adopted or run on test.
- Retrieval for the slot request is already restricted to one intent, so
  candidates share a topic. Embeddings were not tried for the intent
  request, which retrieves across intents. What makes an example useful is the wording around the slot, which
  word-pair overlap matches directly.

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
| 6   | One-sentence descriptions (then the benchmark)                                                                  | 77.8        | 51%             | 2,954  |
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
- **Which examples matters more than how many.** Eight examples chosen by
  similarity to the utterance beat 64 chosen at random, at about a quarter
  of the tokens (rows 46 and 42), and descriptions become nearly redundant.
  This uses the whole training split as a retrieval pool.
- **Tell the question what the state is for.** With examples and slot
  definitions in the state, naming them in the question with backticks added
  2.5 points of slot F1 and 6 of frame accuracy on test, and moving the
  definitions there cut slot tokens by 22% (rows 63–65).
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
- **Asking per slot is the span formulations' weakness.** Both (rows 12 and
  26, later 81 and 84) ask about each slot type on its own. With the same
  one-sentence definitions, token classification beat them on test by 4
  and 7 points of slot F1 at about 60% of the tokens; with its current
  definitions it is 14 and 17 points ahead.
- **The docs have no recipe for open-text slots.** Their extraction
  cookbooks pick among candidates that code finds by pattern, or among
  fixed lists of values. Neither exists for a song title. The span
  formulations were our attempt to fill that gap and were wrongly labelled
  as the docs' patterns for a time.
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

- Span-level definitions for the span formulations written and revised
  with the care the per-word definitions got.
- The value-extraction cookbook as written: a code-side finder for the
  slots that have a pattern (numbers, times), with Jev picking among what
  it finds.
- The intent options' slot definitions held once in the state. The intent
  request has one question, so it would not save tokens.
- A beam over the top two or three intents, keeping the intent whose slot
  answers are most confident (the docs' hierarchical-classification
  cookbook does this for taxonomies).
- Several wordings of the per-word question in one request, averaged.
- A verification pass over decoded spans ("is this value incomplete?", "is
  it the wrong field?"), as in the docs' extraction-cascade cookbook.
- `what` / `not_for` rubrics on the span scheme, where sibling confusion is
  the main error. They were only tried on the token scheme.
- `examples` in the option rubrics.
- Several example samples on test, to measure how much fixed few-shot
  depends on which utterances are drawn.
- Retrieval with a smaller pool (for example 50 or 200 examples per intent),
  to see how much of the gain needs the whole training split.
- `names` and `fewshot`/`retrieved` without descriptions on test, for a
  full two-by-two of descriptions and examples.
- Using the top-k reading for confident slots and the span question for the
  rest.
- Treating slots with a few fixed values (`rating_unit`, `object_select`,
  `music_item`) as closed sets, as the function-calling cookbook does. It
  needs value lists from the training split.
- Rules about specific function words at span edges (for example always
  attaching a leading "the"). SNIPS is not consistent about these, so it
  would be tuning to the annotation.
