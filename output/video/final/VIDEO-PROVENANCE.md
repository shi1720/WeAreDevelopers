# Proofline + Tablekeeper video

The final edit uses authentic computer-use recordings of the BAND Desktop production room and the accepted local stage-four application. It does not reconstruct either interface or generate intermediate UI states.

## Picture sources and editing

- `.private/video-room/frames.json`: 157 timestamped native BAND Desktop captures, 11 distinct image contents. The room is the one that generated the submitted implementation. The recording was made after completion, as labelled on screen. Source capture gaps longer than 300 ms are cut during the 41.553 to 58.937 second playback section. Short source intervals are preserved, subject to 30 fps output quantization. Other room appearances are explicit editorial holds on authentic captures. The hybrid work-board and chat layout is present in the original native capture.
- `.private/video-app/frames.json`: actual CUA-recorded accepted stage-four application in a local demonstration with synthetic data. Capture order within each chosen app scene is retained, followed by an editorial hold. There is no invented application animation. The shown EVENING1 booking moves from Window nook to Garden table while retaining 19:00 arrival, two guests, policy version 0 and 90-minute duration. A recorded after-apply screen and guest history are included. Verification context is `.private/video-app/verification.txt`.
- `assets/tablekeeper-hero.png`: original generated restaurant illustration used only for editorial opening and closing title cards.
- Review and result title cards are authored summaries of `evidence/stage-3/review-01.md`, `evidence/stage-3/verification.md`, and `evidence/final/verification.md`. They are not presented as captured app screens.

Full source images are scaled to fit with surrounding layout margins. During the moving BAND handoff section, captures from frame 57 onward use a fixed native crop `(830, 900, 2390, 1610)` to make the actual chat text readable. No text inside the recorded interface is replaced. App captures are not cropped. The visible BAND price badge, when present, is the app's estimate, not an invoice or a claimed total spend.

`video-scene-provenance.json` records every scene and each output change with the original source path, SHA-256, caption index and output time. The raw recording timestamps remain in the two original frame manifests. These private source manifests are recording provenance, not an additional autonomous production run.

## Narration and captions

The video uses the stock Google Cloud Text-to-Speech voice documented in `AUDIO-PROVENANCE.md`. It does not impersonate Shivam Gupta. All 41 captions use measured complete-sentence timing and are burned into a reserved bottom panel. No caption covers recorded controls. The matching SRT remains available for YouTube accessibility.

The narration is 177.226667 seconds. The 30 fps video has 5,317 frames and is 177.233333 seconds, ending approximately 6.7 ms after the audio. This is normal frame-grid quantization. No spoken word was truncated. The final narration ends before the final silent handle.

## Scope and disclosure

The app footage demonstrates the original accepted local stage, not the separately developed hosted companion. The final segment states this boundary. The four-stage checks and independent HTTP results apply to the graded run. Finite verification is not production certification. The narration explicitly discloses operator recovery of interrupted BAND seats, without further implementation instructions. The commercial price is a hypothesis, not revenue.

## Targeted narration revision

The repair sentence now says “The Engineer seat fixed the history validation.” Only this source audio clip was regenerated after an ASR articulation flag. Subsequent scene and caption boundaries were shifted by the measured 3.333 ms difference. All recorded source frames are unchanged. A targeted automatic transcription recovered every intended replacement word. It does not establish naturalness or replace listening. The prior export is retained privately rather than presented as the current final.

## Validation and remaining limitation

The MP4 uses 1920 by 1080 H.264, 30 fps, yuv420p, AAC audio and faststart layout. `video-ffprobe.json` and `video-qa.json` record output metadata, file hash and size. The encoding is below the 100 MB upload limit. A frame was extracted from every scene in the actual encoded MP4 for contact-sheet inspection, with full-resolution review of title, recorded UI, close-up room text and caption layout. A complete FFmpeg decode check found no errors.

Auditory QA remains limited: the available agent tools could not provide audio input. Objective loudness, clipping and timing checks were performed, but pronunciation, delivery and splice continuity have not been listened to by this agent. A listening pass should precede public publication. No public upload is claimed by this artifact.

## Files

- `proofline-tablekeeper-demo.mp4`: captioned final video.
- `proofline-thumbnail.jpg`: JPEG encoding of the approved submission cover, with the same visual content.
- `proofline-narration.srt`: portable captions.
- `video-contact-sheet.jpg`: extracted scene-frame QA.
- `video-scene-provenance.json`: source hashes and edit map.
- Reproduction: `../.build/build_video.py`, then `../.build/qa_video.py`. Uses Pillow plus local FFmpeg. The original capture manifests and audio must be present.
