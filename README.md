# Jev on SNIPS

Zero-shot evaluation of [Jev](https://docs.typesafe.ai), TypeSafe AI's
"System One" decision model, on the SNIPS natural language understanding
benchmark: intent detection and slot filling.

Jev does not generate text. It takes some state and a set of typed questions
and returns typed answers with probabilities. This project asks how far that
gets on a task normally solved by a trained tagger, without showing the model
a single labelled example.

## Results

SNIPS test set, 700 utterances, model `jev-1.13.0`, zero-shot.

| Metric                  | Token scheme | Span scheme |
| ----------------------- | ------------ | ----------- |
| Intent accuracy         | 94.3%        | 94.3%       |
| Slot F1                 | 26.0%        | 49.1%       |
| Semantic-frame accuracy | 0.9%         | 20.6%       |
| Input tokens            | 926,053      | 3,614,597   |

Intent accuracy is shared: both schemes use the same predicted intent, which
took a further 252,703 input tokens.

Supervised models trained on the 13,084 SNIPS training utterances reach
roughly 98–99% intent accuracy and 96–97% slot F1; nothing here is trained.
Zero-shot intent detection from intent names alone is close to that. Slot
filling from slot names alone is not: letting the model choose a whole span
nearly doubles slot F1 over labelling words independently, but both remain
far below a trained tagger.

## Method

Each utterance gets three requests, all with the utterance as state.

1. **Intent.** One `Choice` over the 7 intent names.
2. **Token scheme.** One `Choice` per word, asking which slot type the
   bracketed word fills (`add sabrina [salerno] to the ...`). Adjacent words
   with the same type are merged into one span.
3. **Span scheme.** One `Choice` per slot type, asking which span of the
   utterance fills it. The options are the utterance's contiguous word spans.
   When two slot types pick overlapping spans, the more probable one is kept.

Both slot schemes offer only the slot types of the **predicted** intent, the
way an assistant's schema restricts which slots an intent accepts. The gold
intent is never used, so an intent error costs the slots as well.

The condition is strictly zero-shot: the model sees intent names, slot names,
and span texts, with no descriptions and no examples. The mapping from intent
to slot types is read from the training split's labels; no training utterance
is sent to the model.

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

Add your `TYPESAFE_API_KEY` to `.env`, and log in to Weights & Biases or add
`WANDB_API_KEY`.

## Usage

Evaluate the full test set:

```bash
uv run run
```

Evaluate the first 20 utterances as a quick check:

```bash
uv run run --limit 20
```

Metrics are logged to the console and to the `jev-snips` wandb project.

## Output

`results/test.jsonl` holds one record per utterance: the tokens and gold
labels, the predicted intent and its probabilities, and for each scheme the
predicted tags, the probabilities of every question's options, and the input
tokens used. Records are `jevsnips.models.Prediction` objects:

```python
from pathlib import Path

from jevsnips.models import Prediction

lines = Path("results/test.jsonl").read_text().splitlines()
predictions = [Prediction.model_validate_json(line) for line in lines]
```

## Project structure

```
src/jevsnips/
├── config.py        # Constants: dataset, model, limits
├── models.py        # Utterance, SlotPrediction, Prediction
├── data.py          # Load utterances and the per-intent slot schema
├── jev.py           # Build questions, call Jev, decode answers
├── metrics.py       # Intent accuracy, slot F1, frame accuracy
└── scripts/run.py   # Entry point
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
