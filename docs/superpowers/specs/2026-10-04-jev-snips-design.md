# Jev on SNIPS: zero-shot intent detection and slot filling

## Goal

Measure how TypeSafe AI's Jev (a non-generative "System One" decision model)
performs zero-shot on the SNIPS NLU benchmark, on both intent detection and
slot filling, using metrics comparable to published supervised results.

Success: one command evaluates the 700-utterance SNIPS test set and reports
intent accuracy, slot F1, and semantic-frame accuracy, with per-utterance
predictions saved for later analysis.

## Background

- Jev takes a `state` and a map of typed questions and returns typed answers
  with probabilities in one parallel pass. It has no span-extraction primitive.
- A `Choice` question takes `instructions` and `criteria` (option name to
  optional description, at most 255 options) and returns `choice`,
  `probabilities` (sum to 1), and `confidence`.
- Access is the official `typesafe-sdk` package:
  `TypeSafeClient().system_one(state, questions)`, authenticated by
  `TYPESAFE_API_KEY`, with built-in retry and backoff on 429/529.
- Data is `bkonkle/snips-joint-intent` on the Hugging Face Hub: `test.csv` with
  columns `input,intent,slots` (whitespace-separated tokens and BIO tags),
  plus `intent_labels.txt` and `slot_labels.txt`.
- Verified on the test split: 700 rows, 7 intents, 39 slot types, 1790 slot
  spans, at most 24 tokens, no token/tag misalignment, and no two adjacent
  spans of the same slot type.
- Each intent uses a small subset of the slot types: between 2
  (`SearchCreativeWork`) and 14 (`BookRestaurant`). Every slot type that an
  intent uses in test also appears with that intent in train.

## Scope

In scope: zero-shot evaluation of Jev on the SNIPS test split.

In scope: two slot-filling schemes compared under otherwise identical
conditions (see Questions).

Out of scope: label descriptions, few-shot examples, gold-intent (oracle)
slot filling, and baselines. Each
would be a separate ablation; any prompt development for them must use train,
never test.

The train split is used only to derive each intent's slot schema. No train
utterance is sent to the model.

## Design

### Package layout

Rename `agent_harness` to `jevsnips` and delete the template's `Agent`,
`Task`, `Harness`, and `Result`. They score one task to a float and convert
exceptions into `score=0.0`; slot F1 is corpus-level and an API failure must
stop the run instead of being recorded as a wrong answer.

| Module           | Responsibility                                                        |
| ---------------- | --------------------------------------------------------------------- |
| `config.py`      | Constants: `MODEL`, `MAX_WORKERS`, `SPLIT`, `DATASET_REPO`, `NONE`    |
| `models.py`      | Pydantic models for parsed data and saved predictions                 |
| `data.py`        | Download a split and the label files and parse them into models       |
| `jev.py`         | Build questions for one utterance, call Jev, decode both slot schemes |
| `metrics.py`     | Intent accuracy, slot F1, semantic-frame accuracy                     |
| `scripts/run.py` | Entry point: load, predict concurrently, save predictions, score, log |

### Models

All parsed data and all saved output are frozen pydantic models, so invalid
rows fail at construction and the JSONL output has one schema.

- `Utterance`: `tokens`, `intent`, `tags`. A validator rejects a row whose
  token and tag counts differ, so a misaligned utterance cannot exist.
- `SlotPrediction`: one scheme's result for one utterance: `tags`,
  `probabilities` (question name to option probabilities), `input_tokens`.
  A validator on `Prediction` requires each scheme's `tags` to match the
  utterance length.
- `Prediction`: the saved record: the `Utterance`, `intent` (predicted),
  `intent_probabilities`, `intent_input_tokens`, `token` and `span` (`SlotPrediction` each), and
  `model` (the version the API returned).

Records are written with `model_dump_json` and can be reloaded with
`model_validate_json`.

### Data

`data.py` downloads files with `hf_hub_download` and parses each row into an
`Utterance`: tokens (`input.split()`), an intent, and gold BIO tags
(`slots.split()`).

The slot schema maps each intent to the slot types that occur with it in the
train split, read from the `intent` and `slots` columns with the `B-`/`I-`
prefix removed. This is the assistant's schema (which slots an intent
accepts), the same information a deployed NLU system is configured with.
Train has one row whose token and tag counts differ; the schema reads tags
only, so the alignment check applies to the evaluated split.

The intent inventory is the schema's keys. The dataset is pinned to a commit
so the benchmark is reproducible.

### Questions

Three requests per utterance, all with the utterance text as `state`: one for
the intent, then one per slot scheme. Both schemes are conditioned on the same
predicted intent, so they differ only in how slots are asked and decoded.

1. Intent: one `Choice` named `intent` whose options are the 7 intent names.
2. Token scheme: one `Choice` named `token_{i}` per token index `i`, whose
   options are the predicted intent's slot types plus `none`. The
   instructions name the intent and show the utterance with token `i` in
   brackets, for example `add sabrina [salerno] to the grime instrumentals
playlist`, so repeated words are unambiguous.
3. Span scheme: one `Choice` per slot type of the predicted intent, named
   after the slot type, asking which span of the utterance fills that slot.
   The options are the texts of the utterance's contiguous word spans plus
   `none`.

Span options are deduplicated by text, and a text refers to its first
occurrence in the utterance. A `Choice` takes at most 255 options, so span
length is capped per utterance at the largest length whose spans plus `none`
fit. Utterances of up to 22 tokens offer every span; the longest test
utterance (24 tokens) offers spans of up to 14 words, above the longest gold
span in test (10 words).

Slots are conditioned on the predicted intent, never the gold intent, so no
label leaks into the slot or frame metrics. An intent error therefore offers
the wrong slot options and usually costs the slots too, which is how a real
pipeline behaves.

All option descriptions are `None`: the model sees label names and span texts
only. This is the zero-shot condition and nothing is tuned against the test
set.

### Decoding

Intent is the `choice` of the `intent` answer.

Token scheme: take the `choice` of each token answer. `none` becomes `O`.
Otherwise a token gets `B-type` if the previous token's type differs and
`I-type` if it is the same.

Span scheme: each slot type whose `choice` is not `none` proposes one span.
Proposals are accepted in descending order of the chosen option's
probability, skipping any that overlaps an accepted span. Accepted spans are
written as `B-type I-type ...`; all other tokens are `O`.

Known ceilings, all measured on the test split:

| Limitation                                                    | Scheme | Gold spans affected |
| ------------------------------------------------------------- | ------ | ------------------- |
| Two adjacent spans of the same type merge into one            | Token  | 0 of 1790           |
| A slot type can fill only one span per utterance              | Span   | 0 of 1790           |
| A span whose text also occurs earlier resolves to the earlier | Span   | 1 of 1790           |

### Metrics

- Intent accuracy: fraction of utterances with the correct intent.
- Slot F1: span-level micro F1 from `seqeval`, the conlleval-equivalent used
  in the SNIPS literature, reported per scheme.
- Semantic-frame accuracy: fraction of utterances with the correct intent and
  an exactly matching tag sequence, reported per scheme.

### Run

`scripts/run.py` loads `.env`, builds one `TypeSafeClient`, and maps the
prediction function over the split with a `ThreadPoolExecutor` and `tqdm`.

Output is `results/{split}.jsonl`, one `Prediction` per line. Metrics, token
totals per scheme, and the returned model version are logged with
`logging.info`.

One optional argument, `--limit N`, evaluates the first N rows for a cheap
smoke run and writes to `results/{split}-first{N}.jsonl` so it cannot
overwrite a full run. A non-positive limit raises before any request. `results/` is git-ignored.

### Errors

No fallbacks. SDK retries handle rate limits; any other API error, a missing
key, or a misaligned row raises and stops the run. A run is cheap enough to
repeat, so there is no resume logic.

### Probe results

One 24-token `BookRestaurant` utterance was sent to `jev-latest` before
planning. The API returned model `jev-1.13.0`. All 14 span questions with 246
options each fit in one request (45,400 input tokens, 0.5 s); the token
scheme used 4,436 input tokens and the intent question 375. Each answer's
`probabilities` is keyed by option name and includes the chosen option.

A token equal to the `none` option would collide with it in the span scheme.
No test utterance contains one, and building span options for such an
utterance raises.

## Documentation

`README.md` is rewritten for this project: what is measured, the results
table, the method for both schemes, setup, usage, the output format, and the
known limitations.

## Testing

pytest, functional style, no mocks:

- Question building: the intent question lists the 7 intents. The token
  scheme gives one question per token, offering only the given intent's slot
  types plus `none`, with the bracketed token in the instructions. The span
  scheme gives one question per slot type of the intent, with deduplicated
  span texts plus `none`, and never more than 255 options.
- Token decoding: single-token spans, multi-token runs, `none`, and a type
  change between adjacent tokens.
- Span decoding: a multi-word span, `none`, and two overlapping proposals
  where the higher-probability one wins.
- Metrics: hand-built gold and predicted sequences with known scores.
- Models: an `Utterance` with mismatched token and tag counts raises, and a
  `Prediction` survives a JSON round trip unchanged.
- Data: the real test file parses to 700 aligned rows with 7 intents, and
  the schema derived from train covers every gold slot type in test for its
  intent.

The live API path is verified by a `--limit` smoke run, not by tests.

## Dependencies

Add `typesafe-sdk`, `huggingface-hub`, `seqeval`, `tqdm`. Replace the API key
names in `.env.example` with `TYPESAFE_API_KEY`. Experiment tracking is not
used: the run produces a few final numbers, which are logged and can be
recomputed from the saved predictions.
