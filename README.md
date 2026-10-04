# Jev on SNIPS

An evaluation of [Jev](https://docs.typesafe.ai), TypeSafe AI's "System One"
decision model, on the SNIPS natural language understanding benchmark:
intent detection and slot filling.

Jev does not generate text. It takes some state and a set of typed questions
and returns typed answers with probabilities. This project asks how far that
gets on a task normally solved by a trained tagger: with label names alone,
with one-sentence label descriptions, and with a handful of labelled
examples.

## Results

SNIPS test set, 700 utterances, model `jev-1.13.0`. Mean of three runs per
condition, with the range across runs in brackets.

| Condition    | What Jev is shown                              | Intent accuracy  | Slot F1          | Frame accuracy   |
| ------------ | ---------------------------------------------- | ---------------- | ---------------- | ---------------- |
| Names        | Label names                                    | 94.3 (94.3–94.3) | 59.7 (59.5–59.9) | 30.0 (29.9–30.3) |
| Descriptions | Names and one-sentence descriptions            | 95.1 (94.9–95.3) | 76.4 (76.3–76.5) | 49.9 (49.7–50.0) |
| Few-shot     | Descriptions and 32 fixed examples per intent  | 95.0 (94.9–95.1) | 84.4 (84.4–84.5) | 64.8 (64.6–65.1) |
| Retrieved    | Descriptions and the 8 most similar examples   | 96.1 (96.1–96.1) | 89.4 (89.1–89.5) | 75.7 (75.1–76.1) |
| _Joint BERT_ | _Fine-tuned on all 13,084 training utterances_ | _98.6_           | _97.0_           | _92.8_           |

Names and descriptions are zero-shot. Few-shot and retrieved show Jev
labelled training utterances; nothing is trained in any condition. The last
row is a published supervised result
([Chen et al., 2019](https://arxiv.org/abs/1902.10909)) for reference.

Input tokens per run, mean of three runs:

| Condition    | Intent  | Slots     |
| ------------ | ------- | --------- |
| Names        | 252,703 | 1,122,639 |
| Descriptions | 336,703 | 2,113,624 |
| Few-shot     | 336,703 | 5,905,086 |
| Retrieved    | 524,801 | 2,440,043 |

Jev's answers are not identical between runs, which is why each condition is
run three times. The ranges are at most one point.

### What the numbers say

- **Intent detection needs almost nothing.** Names alone give 94.3%.
  Descriptions add under a point, and retrieved examples one more.
- **One-sentence descriptions are worth 17 points of slot F1.** The gain is
  in the slots, not the intent: on utterances where every condition got the
  intent right, slot F1 goes from 61.8 to 79.0.
- **A few labelled examples add another 8 points.** 32 training utterances
  of the predicted intent lift slot F1 from 76.4 to 84.4, for 2.8 times the
  slot tokens. Slots with a few fixed values jump
  (`object_part_of_series_type` 17 to 84, `current_location` 62 to 100,
  `movie_type` 75 to 100, `playlist` 51 to 75). Titles move less (`track`
  41 to 47, `movie_name` 51 to 58), and `album` falls from 26 to 18.
- **Which examples matters more than how many.** The 8 training utterances
  most similar to the one being labelled score 89.4 slot F1 against 84.4
  for 32 fixed ones, at 41% of the slot tokens. Part of that is the better
  intent, 96.1 with retrieved examples against 95.0; on utterances
  where every condition got the intent right it is 91.5 against 87.1.
- **Retrieval uses the whole training split.** It draws on 12,833 distinct
  training utterances, where few-shot uses 224. SNIPS is templated: 12% of
  test utterances retrieve an example that differs from them by one word.
  Jev is still doing more than looking labels up: copying each word's label
  from the same 8 examples scores 72 on the dev set, where Jev with them
  scores 89 to 91.
- **How the question is posed matters as much as what is asked.** Three
  times, the same information presented differently moved the score by
  more than any new information did. The per-word question went from 32 to
  76 slot F1 on a dev set once `none` was described and the word and its
  context were given as labelled fields instead of bracketed in a sentence.
  The same 32 examples scored 79.7 on test shown as whole slot values and
  83.5 with every word labelled. And telling the question to use the
  examples, with the slot definitions moved into the state beside them,
  took the retrieved condition from 86.9 to 89.4 while cutting its slot
  tokens by 22%.
- **Token classification beats the extraction patterns in the Jev docs** by
  4 to 10 points of slot F1, at about 60% of the tokens. See the next
  section.
- **It is still well short of a trained tagger.** That model has learned
  SNIPS's phrasing, slot vocabulary, and annotation conventions from 13,084
  labelled utterances, 64 of which repeat a test utterance. What Jev gets
  wrong is mostly titles and names that only context can tell apart. With
  retrieved examples: `album` (35), `movie_name` (55), `track` (58),
  `entity_name` (58), `cuisine` (59).

### Against the approaches the Jev docs recommend

The Jev docs extract values by asking one question per field, not one per
word. We ran both of their patterns on the same test set, with descriptions
and the same predicted intents, three runs each.

| Slot method                                                                       | Slot F1          | Frame accuracy   | Slot input tokens |
| --------------------------------------------------------------------------------- | ---------------- | ---------------- | ----------------- |
| **Token classification (this benchmark)**                                         | 76.4 (76.3–76.5) | 49.9 (49.7–50.0) | 2,113,624         |
| Extraction cookbook: one `Choice` per slot over candidate spans + `none`          | 72.2 (72.1–72.4) | 40.5 (40.3–40.7) | 3,654,086         |
| Function-calling cookbook: a `stated` yes/no per slot, then a `Choice` over spans | 66.9 (66.4–67.2) | 29.1 (28.3–29.6) | 3,578,493         |

- The **extraction cookbook** has code generate candidate values and asks
  Jev to pick one or `none`. SNIPS slots have no pattern to generate
  candidates from, so the candidates are all the utterance's word spans.
  This was a second method in an earlier version of this benchmark.
- The **function-calling cookbook** treats the intent as a function and each
  slot as an argument: a yes/no question decides whether the argument is
  stated at all, and a question "about the idea, not the parameter name"
  picks its value. Its arguments are closed sets; ours are open, so the
  options are again the utterance's spans.
- Both ask about each slot type separately, so sibling types such as `city`
  and `state` claim the same phrase and code has to pick a winner. Token
  classification puts the slot types in one distribution per word.

Neither docs pattern is in the code. They were run with throwaway scripts;
the wording is in the research note linked below.

## Method

Slot filling is posed as token classification: every word gets exactly one
class, a slot type or `none`. Each utterance takes two requests.

1. **Intent.** One `Choice` over the 7 intents, with the utterance as state.
2. **Slots.** One `Choice` per word over the predicted intent's slot types
   plus `none`, all in one request.

The slot question's instructions are labelled fields, not a sentence, and
the state is the utterance under an `utterance` key:

```json
{
  "intent": "AddToPlaylist",
  "words_before": "add sabrina",
  "word": "salerno",
  "words_after": "to the grime instrumentals playlist",
  "question": "Which slot does `word` fill in `utterance`? Answer none if it fills no slot."
}
```

When examples are shown (few-shot and retrieved), the slot definitions move
out of the options into the state, under `slot_definitions`, where they are
sent once instead of once per word, and the question becomes "Which slot
does `word` fill in `utterance`? The slots are defined in
`slot_definitions`. Label it the way matching words are labelled in
`labelled_examples`. Answer none if it fills no slot."

Decoding turns the per-word classes into spans: adjacent words with the same
type form one span, and up to two unlabelled words between two words of the
same type join it, so the small words inside a title stay in its span.

Only the slot types of the **predicted** intent are offered, the way an
assistant's schema restricts which slots an intent accepts. The gold intent
is never used, so an intent error costs the slots as well. The mapping from
intent to slot types is read from the training split's labels.

### Conditions

| Condition    | Intent request                                                    | Slot request                                                                                 |
| ------------ | ----------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Names        | Intent names                                                      | Slot names                                                                                   |
| Descriptions | Names with descriptions                                           | Names with descriptions, including one for `none`                                            |
| Few-shot     | As descriptions                                                   | Slot names; definitions and 32 fixed examples of the predicted intent in the state           |
| Retrieved    | As descriptions, plus the 8 most similar examples from any intent | Slot names; definitions and the 8 most similar examples of the predicted intent in the state |

- **Descriptions** are one-sentence definitions from `descriptions.py`,
  passed as each option's description, or held in the state when examples
  are shown. Slots are described per intent,
  because one slot name can mean different things (`object_type` is a kind
  of book under `RateBook` and a showtime listing under
  `SearchScreeningEvent`). They were written from the label names and the
  training split only, before any description run on the test set, and they
  contain no example values.
- **Examples** are training utterances placed in the request's state. For
  the slot request each one is its text and a label for every word, a slot
  or `none` (`{"word": "the", "slot": "album"}`), the same judgement the
  question asks for. For the intent request each one is its text and its
  intent.
- **Few-shot** examples are 32 per intent, sampled once with a fixed seed:
  224 in all, 1.7% of the training split.
- **Retrieved** examples are chosen per utterance by TF-IDF cosine over
  words and adjacent word pairs. The pool is every usable training
  utterance with repeated texts counted once (12,833), so this condition
  uses the whole training split as a lookup table, without training on it.

SNIPS repeats some test utterances in its training split: 64 training rows
have the same text as one of 25 test utterances. Those rows are never used
as examples, fixed or retrieved, so a test utterance cannot be shown with
its own labels. Supervised results on SNIPS include them in training.

### Metrics

- **Intent accuracy:** utterances with the correct intent.
- **Slot F1:** span-level micro F1 (conlleval, via `seqeval`).
- **Semantic-frame accuracy:** utterances with the correct intent and every
  slot tag correct.

### Known limitations

Two spans of the same slot type separated by two words or fewer are merged
into one. That affects none of the test set's 1,790 gold slot spans.

Slot values are the words of the utterance. Nothing resolves a value such as
a time expression into a structured value.

## Checked against the Jev docs

We read all of the Jev documentation against this implementation. Where the
docs give guidance, the benchmark follows it, with two deliberate exceptions.

- **Followed:** one narrow judgment per question; labelled fields instead of
  string templates; backticked references to the parts of the state a
  question should use; a no-match option with its own definition; reference
  material in the state; in the best condition, only relevant context in
  the state (8 retrieved examples, where few-shot shows 32 fixed ones); a
  pinned model version (`jev-1.13.0`, not the `jev-latest`
  alias); all of a word-level request's questions in one call.
- **Tested and found not to matter:** the docs warn that Jev leans toward
  the first option and say to reorder and check. Reversing or shuffling the
  slot options changes about 1% of answers and no score.
- **Exception, two requests instead of one.** The docs recommend asking
  every question in a single request and ignoring the answers that turn out
  not to apply. Here the slot request's options, definitions, and examples
  all depend on the predicted intent, which is the case the docs allow a
  second request for. A single-request version would ask the slot questions
  for all seven intents at roughly seven times the slot tokens.
- **Exception, examples in the state.** The docs show examples inside option
  descriptions or instruction fields. Whole labelled utterances in the state
  are billed once per request and scored higher here.

## What we tried

The method above was chosen from the formulations below. All of them,
including the ones that are not in the code, are recorded with their
question wording and what each showed in
[docs/research/2026-10-04-slot-formulations.md](docs/research/2026-10-04-slot-formulations.md).

The scores are slot F1 on a dev set of 700 utterances held out from the
training split, with descriptions and the gold intent, so they compare with
each other and not with the test tables above. Tokens are mean input tokens
per utterance.

| Formulation                                                                                               | Dev slot F1 | Tokens |
| --------------------------------------------------------------------------------------------------------- | ----------- | ------ |
| **Per word, options are slot types**                                                                      |             |        |
| Word marked with brackets in a sentence, `none` undescribed                                               | 31.9        | 2,445  |
| The same, `none` described                                                                                | 60.0        | 2,734  |
| The same, short gaps inside a slot filled                                                                 | 67.9        | 2,734  |
| Word and context as labelled fields, `none` described (**the benchmark**)                                 | **76.4**    | 3,013  |
| The benchmark with `what` / `not_for` option rubrics for sibling slots                                    | 77.1 †      | 4,354  |
| The same, plus "every word of a title counts" and a rubric for `none`                                     | 75.8 †      | 5,128  |
| **The benchmark plus examples from the training split**                                                   |             |        |
| 3 labelled utterances of the intent in the state                                                          | 78.0 ‡      | 3,256  |
| 8 labelled utterances                                                                                     | 80.8 ‡      | 3,671  |
| 16 labelled utterances                                                                                    | 81.6 ‡      | 4,302  |
| 32 labelled utterances                                                                                    | 83.3 ‡      | 5,564  |
| 64 labelled utterances                                                                                    | 83.9 ‡      | 8,184  |
| 16 utterances with every word labelled                                                                    | 83.4 ‡      | 6,158  |
| 32 utterances with every word labelled                                                                    | 85.3 ‡      | 9,250  |
| The same, definitions in the state and the question pointing at the examples (**the few-shot condition**) | 86.1 §      | 8,395  |
| 64 utterances with every word labelled                                                                    | 85.7 ‡      | 15,764 |
| 32 utterances as bare `[word, label]` pairs                                                               | 81.2 ‡      | 6,169  |
| 3 example values on each slot option                                                                      | 79.0 ‡      | 5,101  |
| 8 example values on each slot option                                                                      | 81.7 ‡      | 6,992  |
| 16 example values on each slot option                                                                     | 81.8 ‡      | 9,621  |
| 4 utterances most similar to the utterance, every word labelled                                           | 87.6 ‡      | 3,739  |
| 8 most similar utterances                                                                                 | 89.5 ‡      | 4,474  |
| The same, the question pointing at the examples                                                           | 90.3 §      | 4,616  |
| The same, slot definitions once in the state instead of on every option                                   | 90.6 §      | 3,343  |
| Both of those together (**the retrieved condition**)                                                      | 91.4 §      | 3,478  |
| 8 most similar, slot options reversed or shuffled                                                         | 88.9 §      | 4,481  |
| 8 most similar, plus a yes/no per adjacent word pair to join words                                        | 88.8 §      | 5,297  |
| 16 most similar utterances                                                                                | 89.4 ‡      | 5,981  |
| 32 most similar utterances                                                                                | 89.6 ‡      | 9,048  |
| 8 most similar utterances by embedding similarity (two models tried)                                      | 88.3–88.5 ‡ | 4,520  |
| 8 most similar utterances, no descriptions                                                                | 89.0 ‡      | 3,059  |
| 32 fixed utterances with every word labelled, no descriptions                                             | 84.7 ‡      | 7,834  |
| Copy each word's label from the 8 most similar utterances, without Jev                                    | 72.0        | 0      |
| **Per word, left to right**                                                                               |             |        |
| Whole utterance, word bracketed, earlier labels shown                                                     | 34.9        | 4,874  |
| Only the words so far, last word bracketed, earlier labels shown                                          | 45.3        | 4,756  |
| Only the words so far, no bracket, `none` described                                                       | 47.0        | 4,680  |
| The same, earlier labels shown                                                                            | 22.2        | 4,912  |
| **Per slot, options are spans (the docs' patterns)**                                                      |             |        |
| Extraction cookbook: sentence question, spans plus `none`                                                 | 75.5        | 5,084  |
| The same, instructions as labelled fields                                                                 | 76.2        | 5,359  |
| The same, asked only for slots a word-level question says are present                                     | 75.3        | ~4,000 |
| Function-calling cookbook: `stated` yes/no plus a span question                                           | 66.7 †      | 4,970  |
| **Per slot, options are words**                                                                           |             |        |
| Top word only                                                                                             | 48.6        | 1,303  |
| Top 3 words above 10% of the top probability, span from first to last                                     | 67.9        | 1,303  |
| Top word as anchor, then a second question over spans containing it                                       | 61.3        | 2,890  |
| **Combination**                                                                                           |             |        |
| The benchmark's labels with the extraction cookbook's span boundaries                                     | 79.8 †      | 8,097  |

† Scored on the second half of the dev set, where the benchmark formulation
scores 77.8.

‡ Mean of the two halves of the dev set, where the benchmark formulation
scores 76.5.

§ Whole dev set, in runs where 8 most similar utterances scores 88.8 and 32
fixed ones 84.4.

What we learned, beyond the findings at the top:

- `none` needs a description like every other option. Without one, the
  bracketed question gave a slot to 55% of the words outside any slot.
- Showing earlier labels, or hiding the words to the right, did not help.
- `what` / `not_for` rubrics did not help: the main remaining error is small
  words inside titles labelled `none`, not sibling slots.
- A `stated` yes/no per slot halves the false proposals of the span question
  but misses 12% of the slots that are there, for a net loss.
- Borrowing the span question's boundaries adds two points on the dev set,
  for 2.7 times the tokens. It is not in the benchmark.
- Utterances listed with their slot values are the cheapest way to give
  examples; labelling every word costs more and is the most accurate. The
  labelled keys matter: the same labels as bare `[word, label]` pairs score
  lower than whole slot values.
- More than eight retrieved examples adds nothing, and embedding similarity
  is no better than shared words and word pairs for choosing them.
- The order of the slot options does not matter: about 1% of words change
  when it is reversed or shuffled, and averaging over orders gains nothing.
- A yes/no about each adjacent pair of words ("part of the same name or
  title?") is too unreliable to rebuild spans from.
- Moving definitions into the state only helps when examples are there too.
  Without examples it saves 38% of the tokens but loses frame accuracy, so
  the descriptions condition keeps them on the options.
- With examples, descriptions add about half a point; without examples they
  add 17.
- The remaining errors are mostly small words inside names ("the", "of")
  labelled `none`. Jev is confident about them, so neither the saved
  probabilities nor a follow-up yes/no about the word repairs them.
- The dev set, drawn from the same split as the examples, overstated every
  example-based gain. Each was confirmed on the test set before it was kept.

## Setup

```bash
uv sync
```

```bash
cp .env.example .env
```

Add your `TYPESAFE_API_KEY` to `.env`.

## Usage

Run a condition three times on the full test set (`names`, `descriptions`,
`fewshot`, or `retrieved`):

```bash
uv run run retrieved
```

Compare the saved runs, overall and per slot type:

```bash
uv run report
```

Check the pipeline on the first 20 utterances:

```bash
uv run run names --limit 20
```

A limited run writes to its own files and leaves the full results in place.

## Output

Each run is committed as `results/test-{condition}-run{n}.jsonl`, one record
per utterance: the tokens and gold labels, the condition, the predicted
intent and its probabilities, the predicted slot tags, the probabilities of
every word's options, and the input tokens used. The API reports
probabilities to two decimals, so on a near-tie the saved tag is the API's
choice and cannot always be re-derived from the saved probabilities.

Each record also carries a `parse` in the shape of a Snips NLU result:

```json
{
  "intent": { "intentName": "AddToPlaylist", "probability": 1.0 },
  "slots": [
    { "value": "sabrina salerno", "entity": "artist", "slotName": "artist" },
    {
      "value": "grime instrumentals playlist",
      "entity": "playlist",
      "slotName": "playlist"
    }
  ]
}
```

SNIPS labels each slot value with one name, so `entity` and `slotName` are
the same, and `value` is the text from the utterance.

Records are `jevsnips.models.Prediction` objects:

```python
from pathlib import Path

from jevsnips.models import Prediction

lines = Path("results/test-descriptions-run1.jsonl").read_text().splitlines()
predictions = [Prediction.model_validate_json(line) for line in lines]
```

## Project structure

```
src/jevsnips/
├── config.py        # Constants: dataset, model, limits
├── models.py        # Utterance, SlotPrediction, Prediction, Parse
├── data.py          # Load utterances, the slot schema, and examples
├── descriptions.py  # One-sentence definitions of intents and slots
├── retrieval.py     # Choose examples by similarity to the utterance
├── jev.py           # Build questions, call Jev, decode answers
├── metrics.py       # Intent accuracy, slot F1, frame accuracy
└── scripts/
    ├── run.py       # Run one condition
    └── report.py    # Compare the saved runs
```

## Development

```bash
uv run pre-commit run -a
```

This formats, lints, type-checks, and runs the tests. The data tests download
the dataset from the Hugging Face Hub.

## Data

[`bkonkle/snips-joint-intent`](https://huggingface.co/datasets/bkonkle/snips-joint-intent),
pinned to a fixed revision in `config.py`. SNIPS was introduced in
[Coucke et al., 2018](https://arxiv.org/abs/1805.10190).

## License

See [LICENSE](LICENSE).
