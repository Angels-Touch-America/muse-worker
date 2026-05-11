import runpod
import subprocess
import requests
import cloudinary
import cloudinary.uploader
import os
import uuid

# -----------------------------------
# CLOUDINARY CONFIG
# -----------------------------------

cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET")
)

# -----------------------------------
# SAFE CALLBACK
# -----------------------------------

def safe_post(url, payload):

    try:

        print(f"📡 CALLBACK → {url}")

        response = requests.post(
            url,
            json=payload,
            timeout=15
        )

        print(f"✅ CALLBACK STATUS: {response.status_code}")

    except Exception as e:

        print(f"❌ CALLBACK ERROR: {str(e)}")


# -----------------------------------
# DOWNLOAD VIDEO
# -----------------------------------

def download_video(url, filename):

    print(f"⬇️ Downloading: {url}")

    response = requests.get(
        url,
        timeout=30,
        stream=True
    )

    response.raise_for_status()

    with open(filename, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    print(f"✅ Downloaded: {filename}")


# -----------------------------------
# PROCESS VIDEO
# -----------------------------------

def process_video(
    video_url,
    scene_id,
    job_id,
    update_url,
    text
):

    try:

        input_file = f"/tmp/input_{scene_id}.mp4"
        output_file = f"/tmp/output_{scene_id}.mp4"

        # DOWNLOAD
        download_video(video_url, input_file)

        print("🎬 Processing video with text overlay...")

        safe_text = (
            text
            .replace("'", "")
            .replace(":", "")
            .replace('"', "")
        )

        ffmpeg_command = [
            "ffmpeg",
            "-y",
            "-i", input_file,
            "-vf",
            f"drawtext=text='{safe_text}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=h-120",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            output_file
        ]

        print("🧠 FFMPEG COMMAND:")
        print(" ".join(ffmpeg_command))

        subprocess.run(
            ffmpeg_command,
            check=True
        )

        print("☁️ Uploading scene to Cloudinary...")

        result = cloudinary.uploader.upload_large(
            output_file,
            resource_type="video"
        )

        output_url = result["secure_url"]

        print(f"✅ SCENE UPLOADED: {output_url}")

        safe_post(update_url, {
            "job_id": job_id,
            "scene_id": scene_id,
            "status": "completed",
            "output_url": output_url
        })

        return {
            "status": "completed",
            "output_url": output_url
        }

    except Exception as e:

        print(f"❌ PROCESS VIDEO ERROR: {str(e)}")

        safe_post(update_url, {
            "job_id": job_id,
            "scene_id": scene_id,
            "status": "failed"
        })

        return {
            "error": str(e)
        }


# -----------------------------------
# MERGE VIDEOS
# -----------------------------------

def merge_videos(
    video_urls,
    job_id,
    update_url
):

    try:

        print("🎬 Starting merge pipeline...")

        files = []

        for i, url in enumerate(video_urls):

            filename = f"/tmp/input_{i}.mp4"

            download_video(url, filename)

            files.append(filename)

        list_file = "/tmp/list.txt"

        with open(list_file, "w") as f:
            for file in files:
                f.write(f"file '{file}'\n")

        output_file = f"/tmp/output_{uuid.uuid4()}.mp4"

        ffmpeg_merge_command = [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_file,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            output_file
        ]

        print("🧠 MERGE COMMAND:")
        print(" ".join(ffmpeg_merge_command))

        subprocess.run(
            ffmpeg_merge_command,
            check=True
        )

        print("☁️ Uploading FINAL video...")

        result = cloudinary.uploader.upload_large(
            output_file,
            resource_type="video"
        )

        output_url = result["secure_url"]

        print(f"✅ FINAL VIDEO: {output_url}")

        safe_post(update_url, {
            "job_id": job_id,
            "status": "completed",
            "output_url": output_url
        })

        return {
            "status": "merged",
            "output_url": output_url
        }

    except Exception as e:

        print(f"❌ MERGE ERROR: {str(e)}")

        safe_post(update_url, {
            "job_id": job_id,
            "status": "failed"
        })

        return {
            "error": str(e)
        }


# -----------------------------------
# MAIN HANDLER
# -----------------------------------

def handler(event):

    try:

        input_data = event.get("input", {})

        print("📦 JOB RECEIVED:")
        print(input_data)

        # -----------------------------------
        # MERGE MODE
        # -----------------------------------

        if input_data.get("type") == "merge":

            return merge_videos(
                input_data["video_urls"],
                input_data["job_id"],
                input_data["update_job_url"]
            )

        # -----------------------------------
        # SCENE MODE
        # -----------------------------------

        return process_video(
            input_data["video_url"],
            input_data["scene_id"],
            input_data["job_id"],
            input_data["update_job_url"],
            input_data.get("text", "")
        )

    except Exception as e:

        print(f"❌ HANDLER ERROR: {str(e)}")

        return {
            "error": str(e)
        }


# -----------------------------------
# RUNPOD SERVERLESS START
# -----------------------------------

runpod.serverless.start({
    "handler": handler
})