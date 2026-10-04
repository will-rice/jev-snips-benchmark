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

| Condition    | Scheme | Intent accuracy  | Slot F1          | Frame accuracy   |
| ------------ | ------ | ---------------- | ---------------- | ---------------- |
| Names        | Token  | 94.3 (94.3–94.3) | 59.7 (59.5–59.9) | 30.1 (29.9–30.3) |
| Names        | Span   | 94.3 (94.3–94.3) | 48.3 (47.9–49.1) | 19.3 (19.0–19.6) |
| Descriptions | Token  | 95.1 (94.9–95.3) | 76.4 (76.3–76.5) | 49.9 (49.7–50.0) |
| Descriptions | Span   | 95.1 (94.9–95.3) | 72.2 (72.1–72.4) | 40.5 (40.3–40.7) |

Intent accuracy is shared by both schemes within a condition: they use the
same predicted intent.

What the numbers say:

- **Intent detection needs almost nothing.** Names alone give 94.3%, and
  descriptions add under a point. Supervised models trained on the 13,084
  SNIPS training utterances reach roughly 98–99%.
- **Labelling each word is the better formulation.** With descriptions it
  reaches 76.4 slot F1 against 72.2 for picking spans, gets half of all
  utterances entirely right against 40%, and uses 58% of the tokens. Each
  word gets exactly one label and the slot types compete for it in one
  distribution, which is the shape of the task.
- **One-sentence descriptions are worth 17 points of slot F1** for the token
  scheme and 24 for the span scheme. The gain is in the slots, not the
  intent: on utterances where both conditions got the intent right, token
  slot F1 goes from 61.5 to 78.7.
- **How the question is posed matters as much as what is asked.** On a
  held-out dev set, the same per-word question scored 32 slot F1 when the
  word was marked with brackets inside a sentence and `none` had no
  description, 60 once `none` was described, 68 with short gaps filled, and
  76 once the word and its context were given as labelled fields. See [What we tried](#what-we-tried).
- **It is still well short of a trained tagger** (roughly 96–97% slot F1).
  With descriptions, the token scheme is weakest on titles and names that
  only context can tell apart: `object_part_of_series_type` (17), `album`
  (27), `track` (41), `entity_name` (42), `playlist` (51).

Jev's slot answers are not identical between runs, which is why each
condition is run three times. The ranges above are under one point, so the
differences between rows are far outside the noise.

Input tokens per run, mean of three runs:

| Condition    | Intent  | Token scheme | Span scheme |
| ------------ | ------- | ------------ | ----------- |
| Names        | 252,703 | 1,122,639    | 3,612,495   |
| Descriptions | 336,703 | 2,113,624    | 3,654,086   |

## Method

Each utterance gets three requests, all with the utterance as state (the
token scheme passes it under an `utterance` key).

1. **Intent.** One `Choice` over the 7 intents.
2. **Token scheme.** One `Choice` per word over the intent's slot types plus
   `none`. The instructions are labelled fields, not a sentence: the intent,
   the word, the words before it, the words after it, and the question
   "Which slot does `word` fill in `utterance`?". Adjacent words with the
   same type are merged into one span, and up to two unlabelled words
   between two words of the same type join it, so the small words inside a
   title stay in its span.
3. **Span scheme.** One `Choice` per slot type, asking which span of the
   utterance fills it. The options are the utterance's contiguous word spans.
   When two slot types pick overlapping spans, the more probable one is kept.
   The API reports probabilities to two decimals, so ties are common and are
   broken by slot name.

Both slot schemes offer only the slot types of the **predicted** intent, the
way an assistant's schema restricts which slots an intent accepts. The gold
intent is never used, so an intent error costs the slots as well. The mapping
from intent to slot types is read from the training split's labels; no
training utterance is sent to the model.

### Conditions

- **Names.** The model sees intent names, slot names, and span texts only.
- **Descriptions.** Every intent and slot also carries a one-sentence
  definition from `descriptions.py`. In the token scheme it is the option's
  description, and `none` has one too ("not part of any slot value"). On
  the dev set, with the earlier bracketed question, leaving `none`
  undescribed gave a slot to more than half the words outside any slot.
  In the span scheme, where the options are spans, it is added
  to the question. Slots are described per intent, because one slot name can
  mean different things (`object_type` is a kind of book under `RateBook` and
  a showtime listing under `SearchScreeningEvent`).

Both conditions are zero-shot. The descriptions were written from the label
names and the training split only, before any description run on the test
set, and they contain no example values.

### Metrics

- **Intent accuracy:** utterances with the correct intent.
- **Slot F1:** span-level micro F1 (conlleval, via `seqeval`).
- **Semantic-frame accuracy:** utterances with the correct intent and every
  slot tag correct.

### Known limitations

Measured on the test set's 1,790 gold slot spans:

| Limitation                                                      | Scheme | Spans affected |
| --------------------------------------------------------------- | ------ | -------------- |
| Two spans of the same type within two words of each other merge | Token  | 0              |
| A slot type can fill only one span per utterance                | Span   | 0              |
| A span whose text also occurs earlier resolves to the earlier   | Span   | 1              |

A `Choice` takes at most 255 options, so utterances longer than 22 words
offer spans up to the longest length that fits (14 words for the longest
test utterance, above the longest gold span of 10).

## What we tried

The two schemes above are what the benchmark runs. Every formulation we
tried is recorded with its question wording in
[docs/research/2026-10-04-slot-formulations.md](docs/research/2026-10-04-slot-formulations.md).
The scores below are slot F1 on a dev set of 700 utterances held out from
the training split, with descriptions and the gold intent, so they compare
with each other and not with the test table above. Tokens are mean input
tokens per utterance.

| Formulation                                                               | Dev slot F1 | Tokens |
| ------------------------------------------------------------------------- | ----------- | ------ |
| **Per word, options are slot types**                                      |             |        |
| Word marked with brackets in a sentence, `none` undescribed               | 31.9        | 2,445  |
| The same, `none` described                                                | 60.0        | 2,734  |
| The same, short gaps inside a slot filled                                 | 67.9        | 2,734  |
| Word and context as labelled fields, `none` described (**token scheme**)  | **76.4**    | 3,013  |
| The token scheme with `what` / `not_for` option rubrics for sibling slots | 77.1 †      | 4,354  |
| The same, plus "every word of a title counts" and a rubric for `none`     | 75.8 †      | 5,128  |
| **Per word, left to right**                                               |             |        |
| Whole utterance, word bracketed, earlier labels shown                     | 34.9        | 4,874  |
| Only the words so far, last word bracketed, earlier labels shown          | 45.3        | 4,756  |
| Only the words so far, no bracket, `none` described                       | 47.0        | 4,680  |
| The same, earlier labels shown                                            | 22.2        | 4,912  |
| **Per slot, options are spans**                                           |             |        |
| Sentence question (**span scheme**)                                       | 75.5        | 5,084  |
| Instructions as labelled fields                                           | 76.2        | 5,359  |
| Asked only for slots a word-level question says are present               | 75.3        | ~4,000 |
| **Per slot, options are words**                                           |             |        |
| Top word only                                                             | 48.6        | 1,303  |
| Top 3 words above 10% of the top probability, span from first to last     | 67.9        | 1,303  |
| Top word as anchor, then a second question over spans containing it       | 61.3        | 2,890  |

† Scored on the second half of the dev set, where the token scheme itself
scores 77.8.

What we learned:

- Each word has exactly one class, and asking for it directly is the best
  formulation once it is posed well.
- `none` needs a description like every other option. Without one, the
  bracketed question gave a slot to 55% of the words outside any slot.
- Marking a word with brackets inside a sentence is a poor way to point at
  it. Labelled fields gained 8.5 points on the same question.
- Showing earlier labels, or hiding the words to the right, did not help.
- `what` / `not_for` rubrics did not help the token scheme: its main error
  is small words inside titles labelled `none`, not sibling slots.
- A question over words finds where a slot is (the top word is inside the
  gold span 92% of the time) but not how far it extends. It is the cheapest
  formulation by a wide margin.
- The span scheme asks about each slot separately, so sibling slots such as
  `city` and `state` both claim the same phrase.

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
intent and its probabilities, and for each scheme the predicted tags, the
probabilities of every question's options, and the input tokens used.

Each record also carries a `parse` in the shape of a Snips NLU result, built
from the predicted intent and the token scheme's slots:

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
the same, and `value` is the text from the utterance. Nothing resolves a
value such as a time expression into a structured value.

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
