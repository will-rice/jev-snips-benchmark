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
  description, 60 once `none` was described, and 76 once the word and its
  context were given as labelled fields. See [Method](#method).
- **It is still well short of a trained tagger** (roughly 96–97% slot F1).
  With descriptions, the token scheme is weakest on titles and names that
  only context can tell apart: `object_part_of_series_type` (17), `album`
  (27), `track` (41), `entity_name` (42), `playlist` (51).

Jev's slot answers are not identical between runs, which is why each
condition is run three times. The ranges above are under one point, so the
differences between rows are far outside the noise.

Input tokens per run:

| Condition    | Intent  | Token scheme | Span scheme |
| ------------ | ------- | ------------ | ----------- |
| Names        | 252,703 | 1,122,639    | 3,612,495   |
| Descriptions | 336,703 | 2,113,624    | 3,654,086   |

## Method

Each utterance gets three requests, all with the utterance as state.

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
  description, and `none` has one too ("not part of any slot value");
  without it, more than half the words outside any slot were given a slot.
  In the span scheme, where the options are spans, it is added
  to the question. Slots are described per intent, because one slot name can
  mean different things (`object_type` is a kind of book under `RateBook` and
  a showtime listing under `SearchScreeningEvent`).

Both conditions are zero-shot. The descriptions were written from the label
names and the training split only, before any description run on the test
set, and they contain no example values.

### How the token question was developed

The form of the token question, the `none` description, and the gap of two
words were chosen on a dev set of 700 utterances held out from the training
split, not on the test set. Each dev figure below is slot F1 with
descriptions and the gold intent:

| Per-word question                                           | Dev slot F1 |
| ----------------------------------------------------------- | ----------- |
| Word marked with brackets in a sentence, `none` undescribed | 31.9        |
| The same, labelling words left to right with earlier labels | 34.9        |
| The same, `none` described                                  | 60.0        |
| The same, short gaps filled                                 | 67.9        |
| Word and its context as labelled fields, `none` described   | 76.4        |

The span scheme scored 75.5 on the same dev set. Reading the top few words
from one question per slot scored 67.9 at a quarter of the span scheme's
tokens.

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
probabilities of every question's options, and the input tokens used. Records
are `jevsnips.models.Prediction` objects:

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
├── models.py        # Utterance, SlotPrediction, Prediction
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
