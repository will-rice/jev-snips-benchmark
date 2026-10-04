# Jev on SNIPS

Zero-shot evaluation of [Jev](https://docs.typesafe.ai), TypeSafe AI's
"System One" decision model, on the SNIPS natural language understanding
benchmark: intent detection and slot filling.

Jev does not generate text. It takes some state and a set of typed questions
and returns typed answers with probabilities. This project asks how far that
gets on a task normally solved by a trained tagger, without showing the model
a single labelled example, and how much one-sentence label descriptions help.

## Results

SNIPS test set, 700 utterances, model `jev-1.13.0`. Mean of three runs per
condition, with the range across runs in brackets.

| Condition    | Intent accuracy  | Slot F1          | Frame accuracy   |
| ------------ | ---------------- | ---------------- | ---------------- |
| Names        | 94.3 (94.3–94.3) | 59.7 (59.5–59.9) | 30.1 (29.9–30.3) |
| Descriptions | 95.1 (94.9–95.3) | 76.4 (76.3–76.5) | 49.9 (49.7–50.0) |

What the numbers say:

- **Intent detection needs almost nothing.** Names alone give 94.3%, and
  descriptions add under a point. Supervised models trained on the 13,084
  SNIPS training utterances reach roughly 98–99%.
- **One-sentence descriptions are worth 17 points of slot F1.** The gain is
  in the slots, not the intent: on utterances where both conditions got the
  intent right, slot F1 goes from 61.5 to 78.7.
- **Token classification beats the extraction patterns in the Jev docs** by
  4 to 10 points of slot F1, at about 60% of the tokens. See the next table.
- **How the question is posed matters as much as what is asked.** On a
  held-out dev set, the same per-word question scored 32 slot F1 when the
  word was marked with brackets inside a sentence and `none` had no
  description, 60 once `none` was described, 68 with short gaps filled, and
  76 once the word and its context were given as labelled fields. See
  [What we tried](#what-we-tried).
- **It is still well short of a trained tagger** (roughly 96–97% slot F1).
  With descriptions, the weakest slots are titles and names that only
  context can tell apart: `object_part_of_series_type` (17), `album` (27),
  `track` (41), `entity_name` (42), `playlist` (51).

Jev's slot answers are not identical between runs, which is why each
condition is run three times. The ranges above are under one point.

Input tokens per run, mean of three runs:

| Condition    | Intent  | Slots     |
| ------------ | ------- | --------- |
| Names        | 252,703 | 1,122,639 |
| Descriptions | 336,703 | 2,113,624 |

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
   plus `none`, all in one request. The instructions are labelled fields,
   not a sentence: the intent, the word, the words before it, the words
   after it, and the question "Which slot does `word` fill in `utterance`?".
   The state is the utterance under an `utterance` key.

Decoding turns the per-word classes into spans: adjacent words with the same
type form one span, and up to two unlabelled words between two words of the
same type join it, so the small words inside a title stay in its span.

Only the slot types of the **predicted** intent are offered, the way an
assistant's schema restricts which slots an intent accepts. The gold intent
is never used, so an intent error costs the slots as well. The mapping from
intent to slot types is read from the training split's labels; no training
utterance is sent to the model.

### Conditions

- **Names.** The model sees intent names and slot names only.
- **Descriptions.** Every intent and slot also carries a one-sentence
  definition from `descriptions.py`, passed as the option's description.
  `none` has one too ("not part of any slot value"). Slots are described per
  intent, because one slot name can mean different things (`object_type` is
  a kind of book under `RateBook` and a showtime listing under
  `SearchScreeningEvent`).

Both conditions are zero-shot. The descriptions were written from the label
names and the training split only, before any description run on the test
set, and they contain no example values.

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

## What we tried

Token classification with labelled fields was chosen from the formulations
below; all of them are recorded with their question wording in
[docs/research/2026-10-04-slot-formulations.md](docs/research/2026-10-04-slot-formulations.md).

The scores are slot F1 on a dev set of 700 utterances held out from the
training split, with descriptions and the gold intent, so they compare with
each other and not with the test tables above. Tokens are mean input tokens
per utterance.

| Formulation                                                               | Dev slot F1 | Tokens |
| ------------------------------------------------------------------------- | ----------- | ------ |
| **Per word, options are slot types**                                      |             |        |
| Word marked with brackets in a sentence, `none` undescribed               | 31.9        | 2,445  |
| The same, `none` described                                                | 60.0        | 2,734  |
| The same, short gaps inside a slot filled                                 | 67.9        | 2,734  |
| Word and context as labelled fields, `none` described (**the benchmark**) | **76.4**    | 3,013  |
| The benchmark with `what` / `not_for` option rubrics for sibling slots    | 77.1 †      | 4,354  |
| The same, plus "every word of a title counts" and a rubric for `none`     | 75.8 †      | 5,128  |
| **Per word, left to right**                                               |             |        |
| Whole utterance, word bracketed, earlier labels shown                     | 34.9        | 4,874  |
| Only the words so far, last word bracketed, earlier labels shown          | 45.3        | 4,756  |
| Only the words so far, no bracket, `none` described                       | 47.0        | 4,680  |
| The same, earlier labels shown                                            | 22.2        | 4,912  |
| **Per slot, options are spans (the docs' patterns)**                      |             |        |
| Extraction cookbook: sentence question, spans plus `none`                 | 75.5        | 5,084  |
| The same, instructions as labelled fields                                 | 76.2        | 5,359  |
| The same, asked only for slots a word-level question says are present     | 75.3        | ~4,000 |
| Function-calling cookbook: `stated` yes/no plus a span question           | 66.7 †      | 4,970  |
| **Per slot, options are words**                                           |             |        |
| Top word only                                                             | 48.6        | 1,303  |
| Top 3 words above 10% of the top probability, span from first to last     | 67.9        | 1,303  |
| Top word as anchor, then a second question over spans containing it       | 61.3        | 2,890  |
| **Combination**                                                           |             |        |
| The benchmark's labels with the extraction cookbook's span boundaries     | 79.8 †      | 8,097  |

† Scored on the second half of the dev set, where the benchmark formulation
scores 77.8.

What we learned:

- Each word has exactly one class, and asking for it directly is the best
  single formulation once it is posed well.
- `none` needs a description like every other option. Without one, the
  bracketed question gave a slot to 55% of the words outside any slot.
- Marking a word with brackets inside a sentence is a poor way to point at
  it. Labelled fields gained about 10 points on the same question.
- Showing earlier labels, or hiding the words to the right, did not help.
- `what` / `not_for` rubrics did not help: the main remaining error is small
  words inside titles labelled `none`, not sibling slots.
- A `stated` yes/no per slot halves the false proposals of the span question
  but misses 12% of the slots that are there, for a net loss.
- Borrowing the span question's boundaries adds two points on the dev set,
  for 2.7 times the tokens. It is not in the benchmark.

## Setup

```bash
uv sync
```

```bash
cp .env.example .env
```

Add your `TYPESAFE_API_KEY` to `.env`.

## Usage

Run a condition three times on the full test set:

```bash
uv run run names
```

```bash
uv run run descriptions
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
every word's options, and the input tokens used.

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
├── data.py          # Load utterances and the per-intent slot schema
├── descriptions.py  # One-sentence definitions of intents and slots
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
