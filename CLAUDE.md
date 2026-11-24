# CLAUDE.md - muse-worker

RunPod serverless worker for MUSE (ATA-SYS-MUSE). `worker.py` overlays text on a scene clip or merges clips
with ffmpeg, uploads to Cloudinary, and POSTs the result to the caller's `update_job_url`.

## Build / test / run
- `docker build -t muse-worker .`
- Run needs `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` (names only; never commit values).
- No tests and no `test_input.json`. Syntax check: `python -m py_compile worker.py`.
- Known issue: `requirements.txt` has only `requests`, but the code imports `runpod` and `cloudinary`.
  Fixing this is a code change; ask DM before doing it.

## Deploy
- RunPod serverless endpoint built from the `Dockerfile`. Endpoint details: TODO (DM).
- AI never deploys or changes live systems directly. It requests; a founder_admin approves in ATA Connect.
  Reading endpoint health / job status via the ATA Connect RunPod tools is fine.

## Rules
- Never commit secrets or `.env`; only commit `.env.example` (none exists yet).
- Input fields (`type`, `video_url`, `video_urls`, `scene_id`, `job_id`, `update_job_url`, `text`) and callback
  payloads (`job_id`, `scene_id`, `status`, `output_url`) are a contract with `muse-runtime`
  (`pages/api/render.js`, `merge-scenes.js`, `update-scene.js`, `update-job.js`). Change both sides together.
- Keep changes small and reversible. Work on a branch and open a PR; don't push to main.

## Key files
- `worker.py` - handler: `process_video` (scene mode), `merge_videos` (merge mode), `safe_post` callback
- `Dockerfile` - python:3.10-slim + ffmpeg, runs `python worker.py`
- `requirements.txt` - pip deps (incomplete, see above)
- `assets/scene1-6.mp4` - tiny sample clips
