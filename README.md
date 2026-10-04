# Jev on SNIPS

Zero-shot and few-shot evaluation of [Jev](https://docs.typesafe.ai), TypeSafe AI's
"System One" decision model, on the SNIPS natural language understanding
benchmark: intent detection and slot filling.

Jev does not generate text. It takes some state and a set of typed questions
and returns typed answers with probabilities. This project asks how far that
gets on a task normally solved by a trained tagger, without showing the model
a single labelled example, how much one-sentence label descriptions help,
and how much a handful of labelled examples adds.

## Results

SNIPS test set, 700 utterances, model `jev-1.13.0`. Mean of three runs per
condition, with the range across runs in brackets.

| Condition    | Intent accuracy  | Slot F1          | Frame accuracy   |
| ------------ | ---------------- | ---------------- | ---------------- |
| Names        | 94.3 (94.3–94.3) | 59.7 (59.5–59.9) | 30.1 (29.9–30.3) |
| Descriptions | 95.1 (94.9–95.3) | 76.4 (76.3–76.5) | 49.9 (49.7–50.0) |
| Few-shot     | 95.0 (94.9–95.0) | 83.5 (83.4–83.6) | 61.9 (61.6–62.3) |
| Retrieved    | 96.1 (96.1–96.1) | 86.9 (86.7–87.2) | 69.5 (69.0–70.4) |

Names and descriptions are zero-shot. Few-shot adds a fixed 32 labelled
training utterances per intent to the descriptions condition. Retrieved
instead adds the 8 training utterances most similar to each utterance, drawn
from the whole training split, to both the intent and the slot request.

What the numbers say:

- **Intent detection needs almost nothing.** Names alone give 94.3%, and
  descriptions add under a point. Supervised models trained on the 13,084
  SNIPS training utterances reach 98.6% (Joint BERT, below).
- **One-sentence descriptions are worth 17 points of slot F1.** The gain is
  in the slots, not the intent: on utterances where every condition got the
  intent right, slot F1 goes from 61.8 to 79.0.
- **A few labelled examples add another 7 points.** Showing 32 training
  utterances of the predicted intent, with every word labelled, lifts slot
  F1 from 76.4 to 83.5 and frame accuracy from 49.9 to 61.9, for 3.1 times
  the slot tokens. Slots with a few fixed values jump
  (`object_part_of_series_type` 17 to 86, `current_location` 62 to 100,
  `movie_type` 75 to 100, `playlist` 51 to 76). Titles barely move (`track`
  41 to 43, `album` 26 to 30, `movie_name` 51 to 50).
- **Choosing examples by similarity beats a fixed sample, for half the
  tokens.** With the intent question unchanged, showing the slot request
  the 8 training utterances most like the one being labelled scored 86.2
  slot F1 against 83.5 for 32 fixed ones, and got 68% of utterances entirely
  right against 62%. (The retrieved row above is higher, 86.9 and 69.5,
  because it also retrieves examples for the intent.) It draws on all 12,833 distinct
  training utterances, though, where few-shot uses 224. SNIPS utterances
  are templated, so 12% of test utterances retrieve an example that differs
  from them by one word. Jev is still doing more than looking labels up:
  copying each word's label from the same 8 examples scores 72 on the dev
  set, where Jev with them scores 89.5.
- **Retrieved examples help the intent too.** Showing the intent question
  the 8 most similar training utterances of any intent, with their intents,
  cuts intent errors from about 34 to 27 of 700 (95.1 to 96.1). Most of what
  remains is three intents that overlap in meaning: `SearchCreativeWork`,
  `SearchScreeningEvent`, and `PlayMusic`.
- **Examples must have the shape of the question.** The same 32 utterances
  shown as whole slot values ("album: the best of") scored 79.7: Jev left
  the first word of a phrase out of its slot more often ("movie" in "movie
  house"). Labelling every word of each example fixed that.
- **Token classification beats the extraction patterns in the Jev docs** by
  4 to 10 points of slot F1, at about 60% of the tokens. See the next table.
- **How the question is posed matters as much as what is asked.** On a
  held-out dev set, the same per-word question scored 32 slot F1 when the
  word was marked with brackets inside a sentence and `none` had no
  description, 60 once `none` was described, 68 with short gaps filled, and
  76 once the word and its context were given as labelled fields. See
  [What we tried](#what-we-tried).
- **It is still well short of a trained tagger** (97.0 slot F1, below).
  In every condition with examples, the weakest slots are titles and names
  that only context can tell apart. With retrieved examples: `album` (39),
  `entity_name` (50), `movie_name` (54), `object_name` (61), `track` (64).

Jev's slot answers are not identical between runs, which is why each
condition is run three times. The ranges above are at most a point and a
half.

For reference, a supervised model fine-tuned on the full training split,
[Joint BERT](https://arxiv.org/abs/1902.10909) (Chen et al., 2019), reports
98.6 intent accuracy, 97.0 slot F1, and 92.8 frame accuracy on this test
set. The gap is the cost of not training: that model has learned SNIPS's
phrasing, slot vocabulary, and annotation conventions from 13,084 labelled
utterances, 64 of which repeat a test utterance.

Input tokens per run, mean of three runs:

| Condition    | Intent  | Slots     |
| ------------ | ------- | --------- |
| Names        | 252,703 | 1,122,639 |
| Descriptions | 336,703 | 2,113,624 |
| Few-shot     | 336,703 | 6,608,202 |
| Retrieved    | 524,801 | 3,144,857 |

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

1. **Intent.** One `Choice` over the 7 intents, with the utterance as state
   (and, in the retrieved condition, examples beside it).
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
intent to slot types is read from the training split's labels. Under names
and descriptions no training utterance is sent to the model.

### Conditions

- **Names.** The model sees intent names and slot names only.
- **Descriptions.** Every intent and slot also carries a one-sentence
  definition from `descriptions.py`, passed as the option's description.
  `none` has one too ("not part of any slot value"). Slots are described per
  intent, because one slot name can mean different things (`object_type` is
  a kind of book under `RateBook` and a showtime listing under
  `SearchScreeningEvent`).

- **Few-shot.** Descriptions, plus 32 labelled training utterances of the
  predicted intent in the slot request's state. Each is shown as its text
  and a label for every word, a slot or `none`
  (`{"word": "the", "slot": "album"}`), the same judgement the question
  asks for.
  The 224 examples (1.7% of the training split) are sampled once with a
  fixed seed. The intent question is unchanged.

- **Retrieved.** As few-shot, but the examples are chosen per utterance by
  TF-IDF cosine over words and adjacent word pairs. The intent request shows
  the 8 most similar training utterances of any intent, each with its
  intent. The slot request shows the 8 most similar of the predicted intent,
  each with every word labelled. The pool is every usable
  training utterance, with repeated texts counted once (12,833), so this
  condition uses the whole training
  split as a lookup table, without training on it.

Names and descriptions are zero-shot. The descriptions were written from the
label names and the training split only, before any description run on the
test set, and they contain no example values.

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
| **The benchmark plus examples from the training split**                   |             |        |
| 3 labelled utterances of the intent in the state                          | 78.0 ‡      | 3,256  |
| 8 labelled utterances                                                     | 80.8 ‡      | 3,671  |
| 16 labelled utterances                                                    | 81.6 ‡      | 4,302  |
| 32 labelled utterances                                                    | 83.3 ‡      | 5,564  |
| 64 labelled utterances                                                    | 83.9 ‡      | 8,184  |
| 16 utterances with every word labelled                                    | 83.4 ‡      | 6,158  |
| 32 utterances with every word labelled (**the few-shot condition**)       | 85.3 ‡      | 9,250  |
| 64 utterances with every word labelled                                    | 85.7 ‡      | 15,764 |
| 32 utterances as bare `[word, label]` pairs                               | 81.2 ‡      | 6,169  |
| 3 example values on each slot option                                      | 79.0 ‡      | 5,101  |
| 8 example values on each slot option                                      | 81.7 ‡      | 6,992  |
| 16 example values on each slot option                                     | 81.8 ‡      | 9,621  |
| 4 utterances most similar to the utterance, every word labelled           | 87.6 ‡      | 3,739  |
| 8 most similar utterances (**the retrieved condition**)                   | 89.5 ‡      | 4,474  |
| 16 most similar utterances                                                | 89.4 ‡      | 5,981  |
| 32 most similar utterances                                                | 89.6 ‡      | 9,048  |
| 8 most similar utterances by embedding similarity (two models tried)      | 88.3–88.5 ‡ | 4,520  |
| 8 most similar utterances, no descriptions                                | 89.0 ‡      | 3,059  |
| 32 fixed utterances with every word labelled, no descriptions             | 84.7 ‡      | 7,834  |
| Copy each word's label from the 8 most similar utterances, without Jev    | 72.0        | 0      |
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

‡ Mean of the two halves of the dev set, where the benchmark formulation
scores 76.5.

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
- Labelled examples help. Utterances in the state, listed with their slot
  values, are the cheap way to give them: example values on every option
  cost about twice the tokens for the same gain. Labelling every word costs
  more again (about as much as 16 example values per option) and is the
  most accurate.
- Similarity by shared words and word pairs is as good as embedding
  similarity here, and needs no model. Retrieval for the slot request is
  already limited to one intent, so what matters is the wording around the
  slot. Embeddings were not tried for the intent request.
- Which examples matters more than how many. Eight chosen by similarity
  beat 64 chosen at random, and more than eight adds nothing.
- With examples, descriptions add about half a point; without examples they
  add 17.
- Examples work best in the shape of the question. Labelling every word
  beats listing slot values by 3.8 points on test (83.5 against 79.7), and
  the labelled keys matter: the same labels as bare `[word, label]` pairs
  score lower than whole slot values.
- The remaining errors are mostly small words inside names ("the", "of")
  labelled `none`. Jev is confident about them, so neither the saved
  probabilities nor a follow-up yes/no about the word repairs them.

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

```bash
uv run run fewshot
```

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
