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

Out of scope: label descriptions, few-shot examples, the candidate-span
extraction scheme, gold-intent (oracle) slot filling, and baselines. Each
would be a separate ablation; any prompt development for them must use train,
never test.

The train split is used only to derive each intent's slot schema. No train
utterance is sent to the model.

## Design

### Package layout

Rename `agent_harness` to `jev_snips` and delete the template's `Agent`,
`Task`, `Harness`, and `Result`. They score one task to a float and convert
exceptions into `score=0.0`; slot F1 is corpus-level and an API failure must
stop the run instead of being recorded as a wrong answer.

| Module           | Responsibility                                                         |
| ---------------- | ---------------------------------------------------------------------- |
| `config.py`      | Constants: `MODEL`, `MAX_WORKERS`, `SPLIT`, `DATASET_REPO`, `NONE`     |
| `data.py`        | Download and parse a split and the label files                         |
| `jev.py`         | Build questions for one utterance, call Jev, decode answers            |
| `metrics.py`     | Intent accuracy, slot F1, semantic-frame accuracy                      |
| `scripts/run.py` | Entry point: load, predict concurrently, save predictions, score, log |

### Data

`data.py` downloads files with `hf_hub_download` and parses each row into
tokens (`input.split()`), an intent, and gold BIO tags (`slots.split()`). It
raises if a row's token and tag counts differ.

The intent inventory comes from `intent_labels.txt`, dropping `PAD` and
`UNK`.

The slot schema maps each intent to the slot types that occur with it in the
train split, read from the `intent` and `slots` columns with the `B-`/`I-`
prefix removed. This is the assistant's schema (which slots an intent
accepts), the same information a deployed NLU system is configured with.
Train has one row whose token and tag counts differ; the schema reads tags
only, so the alignment check applies to the evaluated split.

### Questions

Two requests per utterance, both with the utterance text as `state`.

1. Intent: one `Choice` named `intent` whose options are the 7 intent names.
2. Slots, given the predicted intent: one `Choice` named `token_{i}` per
   token index `i`, whose options are that intent's slot types plus `none`.
   The instructions name the intent and show the utterance with token `i` in
   brackets, for example `add sabrina [salerno] to the grime instrumentals
   playlist`, so repeated words are unambiguous.

Slots are conditioned on the predicted intent, never the gold intent, so no
label leaks into the slot or frame metrics. An intent error therefore offers
the wrong slot options and usually costs the slots too, which is how a real
pipeline behaves.

All option descriptions are `None`: the model sees label names only. This is
the zero-shot condition and nothing is tuned against the test set.

### Decoding

- Intent: the `choice` of the `intent` answer.
- Slots: the `choice` of each token answer. `none` becomes `O`. Otherwise a
  token gets `B-type` if the previous token's type differs and `I-type` if it
  is the same.

Merging adjacent equal types cannot represent two back-to-back spans of the
same type. That never occurs in the test split, so it costs nothing here.

### Metrics

- Intent accuracy: fraction of utterances with the correct intent.
- Slot F1: span-level micro F1 from `seqeval`, the conlleval-equivalent used
  in the SNIPS literature.
- Semantic-frame accuracy: fraction of utterances with the correct intent and
  an exactly matching tag sequence.

### Run

`scripts/run.py` loads `.env`, builds one `TypeSafeClient`, and maps the
prediction function over the split with a `ThreadPoolExecutor` and `tqdm`.

Output is `results/{split}.jsonl`, one record per utterance: tokens, gold
intent and tags, predicted intent and tags, per-question probabilities, token
usage summed over both requests, and the model version the API returned. Metrics, token totals, and the
returned model version are logged to wandb and with `logging.info`.

One optional argument, `--limit N`, evaluates the first N rows for a cheap
smoke run. `results/` is git-ignored.

### Errors

No fallbacks. SDK retries handle rate limits; any other API error, a missing
key, or a misaligned row raises and stops the run. A run is cheap enough to
repeat, so there is no resume logic.

## Testing

pytest, functional style, no mocks:

- Question building: the intent question lists the 7 intents; the slot
  questions give one question per token, offering only the given intent's
  slot types plus `none`, with the bracketed token in the instructions.
- Decoding: single-token spans, multi-token runs, `none`, and a type change
  between adjacent tokens.
- Metrics: hand-built gold and predicted sequences with known scores.
- Data: the real test file parses to 700 aligned rows with 7 intents, and
  the schema derived from train covers every gold slot type in test for its
  intent.

The live API path is verified by a `--limit` smoke run, not by tests.

## Dependencies

Add `typesafe-sdk`, `huggingface-hub`, `seqeval`, `tqdm`, `wandb`.
Replace the API key names in `.env.example` with `TYPESAFE_API_KEY` and
`WANDB_API_KEY`.
