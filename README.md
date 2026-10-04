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
| Names        | Token  | 94.3 (94.3–94.3) | 26.0 (25.9–26.2) | 0.9 (0.7–1.0)    |
| Names        | Span   | 94.3 (94.3–94.3) | 48.2 (47.7–48.8) | 19.2 (18.4–20.1) |
| Descriptions | Token  | 94.9 (94.9–95.0) | 32.1 (31.7–32.4) | 2.0 (2.0–2.0)    |
| Descriptions | Span   | 94.9 (94.9–95.0) | 72.3 (72.1–72.5) | 40.7 (40.4–41.0) |

Intent accuracy is shared by both schemes within a condition: they use the
same predicted intent.

What the numbers say:

- **Intent detection needs almost nothing.** Names alone give 94.3%, and
  descriptions add about half a point. Supervised models trained on the
  13,084 SNIPS training utterances reach roughly 98–99%.
- **Asking for a span beats labelling words.** The span scheme scores about
  double the token scheme in both conditions. Labelling each word
  independently pulls neighbouring function words into slots and breaks span
  boundaries.
- **One-sentence descriptions are worth 24 points of slot F1** in the span
  scheme (48.2 to 72.3) and double frame accuracy. The gain is largest on
  slots whose names say little: `best_rating` (16 to 95), `geographic_poi`
  (30 to 96), `object_location_type` (36 to 98), `state` (13 to 75).
- **The gain is in the slots, not the intent.** On the utterances where both
  conditions got the intent right, span slot F1 goes from 49.7 to 74.5.
- **It is still well short of a trained tagger** (roughly 96–97% slot F1).
  `object_select` scores 0 in the span scheme under both conditions, and
  `playlist`, `track`, and `current_location` stay below 45.

Jev's slot answers are not identical between runs, which is why each
condition is run three times. The ranges above are under one point, so the
differences between rows are far outside the noise.

Input tokens per run:

| Condition    | Intent  | Token scheme | Span scheme |
| ------------ | ------- | ------------ | ----------- |
| Names        | 252,703 | 925,789      | 3,612,495   |
| Descriptions | 336,703 | 1,715,101    | 3,659,296   |

## Method

Each utterance gets three requests, all with the utterance as state.

1. **Intent.** One `Choice` over the 7 intents.
2. **Token scheme.** One `Choice` per word, asking which slot type the
   bracketed word fills (`add sabrina [salerno] to the ...`). Adjacent words
   with the same type are merged into one span.
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
  description; in the span scheme, where the options are spans, it is added
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

| Limitation                                                    | Scheme | Spans affected |
| ------------------------------------------------------------- | ------ | -------------- |
| Two adjacent spans of the same type merge into one            | Token  | 0              |
| A slot type can fill only one span per utterance              | Span   | 0              |
| A span whose text also occurs earlier resolves to the earlier | Span   | 1              |

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
