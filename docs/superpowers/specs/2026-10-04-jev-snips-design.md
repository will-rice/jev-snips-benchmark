# Jev on SNIPS: design

This describes the benchmark as it is now. How it got here, including the
formulations that were tried and dropped, is in
`docs/research/2026-10-04-slot-formulations.md`. The original implementation
plan in `docs/superpowers/plans/` is historical.

## Goal

Measure how TypeSafe AI's Jev, a non-generative "System One" decision model,
performs on the SNIPS NLU benchmark for intent detection and slot filling,
without training, using metrics comparable to published supervised results.

One command evaluates a condition on the 700-utterance SNIPS test set three
times and reports intent accuracy, slot F1, and semantic-frame accuracy,
with per-utterance predictions saved for later analysis.

## Background

- Jev takes a `state` and a map of typed questions and returns typed answers
  with probabilities in one parallel pass. Questions in a request are
  answered independently. It has no span-extraction primitive.
- A `Choice` question takes `instructions` and `criteria` (option name to
  optional description) and returns `choice`, `probabilities`, and
  `confidence`. Instructions, criteria values, and state may each be a
  string or a JSON structure.
- Access is the `typesafe-sdk` package:
  `TypeSafeClient().system_one(state, questions)`, authenticated by
  `TYPESAFE_API_KEY`, with built-in retry and backoff.
- Jev's answers vary slightly between identical requests, and it reports
  probabilities to two decimals.
- The state is ingested once per request and every question is evaluated
  against it, so text in the state is billed once and text in a question's
  options is billed per question.
- `MODEL` is pinned to `jev-1.13.0`. The `jev-latest` alias moves when a new
  release ships.

## Data

- `bkonkle/snips-joint-intent` on the Hugging Face Hub, pinned to a
  revision: `train.csv` and `test.csv` with columns `input,intent,slots`
  (whitespace-separated tokens and BIO tags).
- Test: 700 rows, 7 intents, 39 slot types, 1,790 slot spans, no token/tag
  misalignment.
- Train: 13,084 rows, one of which has mismatched token and tag counts.
- 64 training rows have the same text as one of 25 test utterances.

`data.py` provides:

- `load_utterances(split)`: the split as `Utterance` models.
- `load_slot_schema()`: each intent's slot types, read from the training
  split's intent and tag columns. This is the assistant's schema; the intent
  inventory is its keys.
- `load_example_pool()`: every aligned training utterance whose text does
  not appear in the evaluated split, per intent. Nothing shown to the model
  as an example comes from outside this pool, so a test utterance is never
  shown with its own labels.
- `load_examples()`: `FEWSHOT_EXAMPLES = 32` utterances per intent, sampled
  from the pool once with `FEWSHOT_SEED`.

## Method

Slot filling is token classification: each word gets one class, a slot type
of the predicted intent or `none`. `jev.predict` makes two requests per
utterance.

1. **Intent.** One `Choice` named `intent` over the 7 intents. State is the
   utterance text. Outside `names`, each option's description is
   `{"what": the intent's definition, "slots": its slots' definitions}`
   (`jev.intent_definitions`).
2. **Slots.** One `Choice` named `token_{i}` per word over the predicted
   intent's slot types plus `none`, in one request. Instructions are an
   object with the keys `intent`, `words_before`, `word`, `words_after`, and
   `question`. Without examples, the state is `{"utterance": text}` and the
   question is "Which slot does `word` fill in `utterance`? Answer none if
   it fills no slot." The example conditions change both; see below.

Slots are conditioned on the predicted intent, never the gold intent, so an
intent error costs the slots as well.

### Conditions

`Condition` is one of four values.

- `names`: option descriptions are `None`.
- `descriptions`: every intent and slot option carries its definition from
  `descriptions.py`, keyed by intent and slot, and `none` carries that
  intent's entry in `NONE_DESCRIPTIONS`. A slot's definition says what a
  single word must be to count as part of the slot, names typical words, and
  states SNIPS's boundary conventions. They were written and revised against
  training utterances only (200 per intent, confirmed on 700 others and on
  the dev set).
- `fewshot`: the intent request is as in `descriptions`. The slot request's
  state holds `utterance`, `slot_definitions` (each slot's definition, and
  `none`'s), and `labelled_examples` (the fixed sample for the predicted
  intent). Its options carry no descriptions, and its question is "Which
  slot does `word` fill in `utterance`? The slots are defined in
  `slot_definitions`. Label it the way matching words are labelled in
  `labelled_examples`. Answer none if it fills no slot."
- `retrieved`: the intent request keeps the option descriptions, and its
  state becomes `{"utterance", "labelled_examples"}` with the
  `RETRIEVED_EXAMPLES = 8` most similar pool utterances of any intent and
  the question "What is the intent of `utterance`?". The slot request is as
  in `fewshot`, with the 8 most similar pool utterances of the predicted
  intent as its examples.

Example shapes:

- Slot request: `{"utterance": text, "words": [{"word", "slot"}, ...]}`,
  one entry per word, `none` for words outside any slot.
- Intent request: `{"utterance": text, "intent": name}`.

### Retrieval

`retrieval.py` builds one TF-IDF index per intent, and one over all intents
under the key `ALL_INTENTS`, with scikit-learn. Features are an utterance's
words and adjacent word pairs. Only the first copy of a repeated text is
indexed. `retrieve` returns the examples with the highest cosine similarity
to the utterance, best first.

### Decoding

`decode_tokens` converts the per-word choices to BIO tags. Adjacent words
with the same type form one span. Up to `MAX_GAP = 2` unlabelled words
between two words of the same type take that type.

## Metrics

`metrics.evaluate` returns:

- `intent_accuracy`: fraction of utterances with the correct intent.
- `slot_f1`: span-level micro F1 from `seqeval` (conlleval).
- `frame_accuracy`: fraction of utterances with the correct intent and an
  exactly matching tag sequence.

`metrics.summarize` reduces repeated runs to mean, minimum, and maximum.

## Models

Frozen pydantic models in `models.py`:

- `Utterance`: `tokens`, `intent`, `tags`; rejects mismatched token and tag
  counts.
- `SlotPrediction`: `tags`, `probabilities` (question name to option
  probabilities, without the options scored 0.00), `input_tokens`.
- `Prediction`: the `Utterance`, `condition`, predicted `intent`,
  `intent_probabilities`, `intent_input_tokens`, `slots`, and `model` (the
  version the API returned). It rejects slot tags that do not cover every
  token, and has a computed `parse`.
- `Parse`: the predicted intent with its probability and the predicted slots
  in the shape of a Snips NLU result (`intent.intentName`,
  `intent.probability`, `slots[].value`, `entity`, `slotName`). The dataset
  gives one label per slot value, so `entity` equals `slotName`, and values
  are utterance text, not resolved values.

## Scripts

- `run <condition> [--limit N]`: runs the condition `RUNS = 3` times over
  the test split with a thread pool, writes each run to
  `results/test-{condition}-run{n}.jsonl`, and logs each metric's mean and
  range. A limited run writes to `...-first{N}.jsonl`, which is git-ignored,
  so it cannot overwrite a full run. A non-positive limit raises before any
  request.
- `report`: loads every condition's saved runs and logs the metrics overall,
  on utterances where every condition got the intent right, and slot F1 per
  slot type.

Full-run results are committed, because Jev's answers vary between runs and
the reported numbers could not otherwise be checked.

## Errors

No fallbacks. SDK retries handle rate limits; any other API error, a missing
key, a response without usage, or a misaligned row raises and stops the run.
There is no resume logic.

## Testing

pytest, functional style, no mocks:

- Models: alignment and length validation, JSON round trip, the parse.
- Data: the real test split, the schema, the example pool and fixed sample,
  and that neither contains a test utterance.
- Questions and decoding: the intent question in both wordings, the intent
  definitions, the slot
  request's state and questions with and without examples, example payloads,
  and tag decoding including gap filling.
- Retrieval: ranking, per-intent and cross-intent search, and distinct
  results.
- Metrics and result paths.

`predict` and the scripts' `main` functions call the live API and are
verified by a `--limit` run, not by tests.

## Known limitations

- Two spans of the same slot type within two words of each other merge. No
  gold span in the test set is affected.
- Slot values are utterance text; nothing resolves dates or numbers.
- Only the intent response's model version is saved per utterance.
- On a near-tie, the saved tag is the API's choice and cannot always be
  re-derived from the two-decimal probabilities.

## Dependencies

`typesafe-sdk`, `huggingface-hub`, `seqeval`, `scikit-learn`, `scipy`,
`tqdm`, `pydantic`, `python-dotenv`.
