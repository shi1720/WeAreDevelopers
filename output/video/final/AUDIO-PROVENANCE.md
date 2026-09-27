# Proofline narration provenance

Generated on 27 September 2026 through the official Google Cloud Text-to-Speech synchronous API. This is a stock synthetic narrator, not an imitation of Shivam Gupta or any other real person.

- Model and voice: `en-US-Chirp3-HD-Kore`, English (US), speaking rate 0.95.
- Endpoint: `https://texttospeech.googleapis.com/v1/text:synthesize`.
- Approved billing project: `gen-lang-client-0444960702`.
- Source: `proofline-narration.txt`, 384 words. Script credit: Proofline submission production, with Shivam Gupta credited for product direction and factory configuration.
- Output: 177.226667 seconds, 48 kHz mono PCM WAV; 192 kbps MP3 listening copy.
- Captions: 41 complete-sentence cues. Sentence timings are measured from synthesized PCM clips after boundary-silence trimming and deliberate transition gaps. No word-level forced alignment is claimed. `narration-timing.json` records raw durations, exact trim amounts, and cumulative start/end times.
- Requests: 41 initial sentence synthesis requests, two short stock-voice auditions, and one targeted replacement sentence, 44 total. A total of 3,054 characters was submitted. At the documented $30 per million character list rate this is about $0.09162 before allowance, tax and any other charges. Actual invoiced spend is not available.

## Targeted articulation revision

An independent unprompted automatic speech-recognition review flagged the original sentence “Engineer repaired the history validation.” as potentially ambiguous. This could have been recognition error rather than a synthesis fault. Only that sentence was regenerated as “The Engineer seat fixed the history validation.” using the same voice and speaking rate. All other 40 raw sentence clips were reused unchanged. The previous full package is preserved privately in `.private/video-before-articulation-fix/`. New timing differs by 3.333 ms; audio, captions and video were rebuilt from the measured clips. A targeted independent automatic recognition pass recovered all intended replacement words, differing only in punctuation and case. Its private result is `.private/narration-replacement-asr.json`. This supports word articulation but does not claim a listening review or certify naturalness.

## Processing and QA

Original API-returned WAVs and input/audio hashes remain in `../.build/`. API access tokens were acquired in memory and were not written to files or logs. There were no billing or cloud-configuration changes in this production step.

The assembly removes only boundary silence below a conservative RMS threshold, retaining 80 ms before the first detected audio and 140 ms after the last. It retains all internal pauses. Complete sentences are separated by 240 ms; paragraph transitions use 480 ms. No speech is time-stretched. FFmpeg loudness normalization creates the editing master.

Measured final integrated loudness is -16.5 LUFS, true peak -1.5 dBFS, and loudness range 2.9 LU. There are no clipped PCM samples. Caption times are positive and ordered without overlap. Each cue has at most two lines. The widest line measures 1,321 px at 44 px Arial in a 1,920 px frame. A representative longest caption was rendered and visually inspected. SRT is the portable upload track; ASS provides a suggested 1080p visual style.

Auditory QA limit: this agent's tools did not provide audio input. Voice selection used stock voice availability and measured pacing. Pronunciation, prosody, exact correspondence of speech to script and inter-sentence continuity have not been listened to by this agent. A listening pass is required before public publication. No claim that the final video has been reviewed or uploaded is made here.

## Reproduction

Use the bundled Python environment with NumPy and Pillow. `../.build/synthesize.py` calls the official API. `../.build/build_narration.py` synthesizes missing sentence clips and assembles WAV, MP3, SRT and timing JSON. `../.build/finish_audio.py` creates ASS, caption QA and file checksums. Existing raw clips are reused; delete only deliberately selected raw clips to resynthesize. Additional synthesis can incur charges. The fixed source currently lives at `.private/voiceover-narration.txt` in the repository root; the final source is copied alongside this document.

## Sources

- [Google Chirp 3 HD model and voice documentation](https://docs.cloud.google.com/text-to-speech/docs/chirp3-hd)
- [Google Cloud Text-to-Speech quotas and request limits](https://docs.cloud.google.com/text-to-speech/quotas)
- [Google Cloud Text-to-Speech pricing](https://cloud.google.com/text-to-speech/pricing)
- Original graded facts: `evidence/final/verification.md`, `evidence/stage-3/review-01.md`, `evidence/stage-3/verification.md`, and `evidence/dispatch.json` in the project repository.
