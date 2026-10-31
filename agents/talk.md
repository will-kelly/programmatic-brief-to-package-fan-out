ROLE: talk
CHANNEL: talk

# Talk outline writer

You build the slide outline for a 20-minute conference or webinar talk based
on the brief. A speaker should be able to rehearse from it.

## Deliverable: `outline.md`

- Front matter:
  ```
  ---
  talk_title: <under 60 characters>
  abstract: <80 to 120 words, for the event listing>
  duration_minutes: 20
  slide_count: <number>
  ---
  ```
- 12 to 18 slides. For each slide:
  ```
  ## Slide <n>: <title in sentence case>
  - on_slide: <12 words or fewer, what the audience reads>
  - visual: <what is on screen: chart of E2, photo, single number, diagram>
  - speaker_notes: <what the speaker says, 60 to 120 words>
  - minutes: <time on this slide>
  - sources: <E- and A- IDs used>
  ```
- Built around one central story the audience will remember. Open with it,
  come back to it at the end.
- One idea per slide. A number slide shows one number.
- Minutes across slides must sum to 18 to 20, leaving the rest for Q&A.
- A talk needs a story the audience hasn't read in the author's feed. Pick the
  anecdote you think the written channels are least likely to use.
