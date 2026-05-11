import runpod
import subprocess
import requests
import cloudinary
import cloudinary.uploader
import os
import uuid

cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET")
)


# 🔥 PROCESS VIDEO WITH TEXT
def process_video(video_url, scene_id, job_id, update_url, text):
    try:
        print(f"⬇️ Downloading: {video_url}")

        input_file = f"/tmp/input_{scene_id}.mp4"
        output_file = f"/tmp/output_{scene_id}.mp4"

        r = requests.get(video_url)
        with open(input_file, "wb") as f:
            f.write(r.content)

        print("🎬 Processing video with text...")

        safe_text = text.replace("'", "").replace(":", "")

        subprocess.run([
            "ffmpeg",
            "-i", input_file,
            "-vf",
            f"drawtext=text='{safe_text}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=h-120",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            output_file
        ], check=True)

        print("☁️ Uploading to Cloudinary...")

        result = cloudinary.uploader.upload_large(
            output_file,
            resource_type="video"
        )

        output_url = result["secure_url"]

        print(f"✅ Uploaded: {output_url}")

        requests.post(update_url, json={
            "job_id": job_id,
            "scene_id": scene_id,
            "status": "completed",
            "output_url": output_url
        })

        return {"status": "done"}

    except Exception as e:
        print(f"❌ Error: {str(e)}")

        requests.post(update_url, json={
            "job_id": job_id,
            "scene_id": scene_id,
            "status": "failed"
        })

        return {"error": str(e)}


# 🔥 MERGE VIDEOS
def merge_videos(video_urls, job_id, update_url):
    try:
        print("🎬 Starting merge...")

        files = []

        for i, url in enumerate(video_urls):
            filename = f"/tmp/input_{i}.mp4"
            r = requests.get(url)
            with open(filename, "wb") as f:
                f.write(r.content)
            files.append(filename)

        list_file = "/tmp/list.txt"
        with open(list_file, "w") as f:
            for file in files:
                f.write(f"file '{file}'\n")

        output_file = f"/tmp/output_{uuid.uuid4()}.mp4"

        subprocess.run([
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", list_file,
            "-c", "copy",
            output_file
        ], check=True)

        result = cloudinary.uploader.upload_large(
            output_file,
            resource_type="video"
        )

        output_url = result["secure_url"]

        print(f"✅ FINAL VIDEO: {output_url}")

        requests.post(update_url, json={
            "job_id": job_id,
            "status": "completed",
            "output_url": output_url
        })

        return {"status": "merged"}

    except Exception as e:
        print(f"❌ MERGE ERROR: {str(e)}")

        requests.post(update_url, json={
            "job_id": job_id,
            "status": "failed"
        })

        return {"error": str(e)}


# 🔥 MAIN HANDLER
def handler(event):
    try:
        input_data = event.get("input", {})

        print("📦 JOB RECEIVED:", input_data)

        if input_data.get("type") == "merge":
            return merge_videos(
                input_data["video_urls"],
                input_data["job_id"],
                input_data["update_job_url"]
            )

        return process_video(
            input_data["video_url"],
            input_data["scene_id"],
            input_data["job_id"],
            input_data["update_job_url"],
            input_data.get("text", "")
        )

    except Exception as e:
        print(f"❌ HANDLER ERROR: {str(e)}")
        return {"error": str(e)}


runpod.serverless.start({"handler": handler})