# MUSE Worker

RunPod serverless worker that processes MUSE video scenes with ffmpeg and uploads results to Cloudinary.
Part of MUSE (ATA-SYS-MUSE).

## What it does
`worker.py` starts `runpod.serverless.start({"handler": handler})`. Each job's `input` picks one of two modes:

- **Scene mode** (default). Input: `video_url`, `scene_id`, `job_id`, `update_job_url`, optional `text`.
  Downloads the clip, burns `text` in as a white caption near the bottom (ffmpeg `drawtext`), re-encodes
  to H.264, uploads to Cloudinary, then POSTs `{job_id, scene_id, status, output_url}` to `update_job_url`.
- **Merge mode** (`type: "merge"`). Input: `video_urls`, `job_id`, `update_job_url`.
  Downloads all clips, joins them with the ffmpeg concat demuxer, uploads the final video to Cloudinary,
  then POSTs `{job_id, status, output_url}` to `update_job_url`.

On error it POSTs `status: "failed"` to the callback and returns `{"error": ...}`.
Temp files go to `/tmp`. `assets/scene1-6.mp4` are small sample clips (about 8 KB each).

## Stack
Python 3.10 (`python:3.10-slim`), ffmpeg (apt), `runpod`, `cloudinary`, `requests`. Docker image.

## Run locally
```
docker build -t muse-worker .
docker run --rm -e CLOUDINARY_CLOUD_NAME -e CLOUDINARY_API_KEY -e CLOUDINARY_API_SECRET muse-worker
```
TODO (DM): no local test input is in the repo. The RunPod SDK can run a handler locally with a
`test_input.json` file or `--test_input`; none exists here.

**Known issue:** `requirements.txt` lists only `requests` (with a UTF-8 BOM), but `worker.py` also imports
`runpod` and `cloudinary`. The Dockerfile only runs `pip install -r requirements.txt`. Unless the live
image was built differently, the container will fail on import. TODO (DM): confirm how the live image is built.

## Configuration
Environment variables (names only):

| Name | Purpose |
| --- | --- |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary account for uploads |
| `CLOUDINARY_API_KEY` | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | Cloudinary API secret |

Set these on the RunPod endpoint/template, never in the repo.

## Deploy
Runs as a RunPod serverless endpoint built from this repo's `Dockerfile`.
TODO (DM): endpoint name/ID, and whether RunPod builds from GitHub or from a pushed registry image.
No ATA Connect deploy job exists for this worker. AI may read endpoint health and request jobs via the
ATA Connect RunPod tools; changes to the live endpoint need founder_admin approval.

## Connects to
- Called by the MUSE app ([muse-runtime](https://github.com/Angels-Touch-America/muse-runtime)) via the RunPod API.
  The caller supplies `update_job_url` (a callback route on the app, e.g. its `update-job` / `update-scene` API).
- Cloudinary (video storage).

## Owner / status
Owner: DM (Darrell McCrimmons). Status: "Recovered Muse Worker" 2026-05-10, last change 2026-05-17 (Dockerfile only).
