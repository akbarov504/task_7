import subprocess
import os
import signal
import sys

VIDEO_DEVICE = "/dev/video25"
AUDIO_DEVICE = "hw:3,0"

OUTPUT_DIR = "records"
SEGMENT_TIME = 10

WIDTH = 1920
HEIGHT = 1080
FPS = 30

VIDEO_BITRATE = "2500k"
AUDIO_BITRATE = "128k"

os.makedirs(OUTPUT_DIR, exist_ok=True)

process = None

def build_ffmpeg_command():
    timestamp_pattern = os.path.join(
        OUTPUT_DIR,
        "cam_%Y-%m-%d_%H-%M-%S.mp4"
    )

    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "warning",

        "-f", "v4l2",
        "-thread_queue_size", "4096",
        "-framerate", str(FPS),
        "-video_size", f"{WIDTH}x{HEIGHT}",
        "-i", VIDEO_DEVICE,

        "-f", "alsa",
        "-thread_queue_size", "4096",
        "-i", AUDIO_DEVICE,

        "-c:v", "mpeg4",
        "-preset", "veryfast",
        "-tune", "zerolatency",
        "-pix_fmt", "yuv420p",
        "-r", str(FPS),
        "-b:v", VIDEO_BITRATE,
        "-maxrate", VIDEO_BITRATE,
        "-bufsize", "5000k",
        "-g", str(FPS * 2),

        "-c:a", "aac",
        "-b:a", AUDIO_BITRATE,
        "-ar", "44100",
        "-ac", "1",

        "-movflags", "+faststart",

        "-f", "segment",
        "-segment_time", str(SEGMENT_TIME),
        "-reset_timestamps", "1",
        "-strftime", "1",

        timestamp_pattern
    ]

    return cmd

def stop_ffmpeg(signum=None, frame=None):
    global process
    print("\n[INFO] Yozuv to'xtatilmoqda...")

    if process and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()

    print("[INFO] FFmpeg to'xtadi.")
    sys.exit(0)

def main():
    global process

    cmd = build_ffmpeg_command()

    print("[INFO] Live recording boshlandi")
    print(f"[INFO] Kamera: {VIDEO_DEVICE}")
    print(f"[INFO] Mikrofon: {AUDIO_DEVICE}")
    print(f"[INFO] Papka: {OUTPUT_DIR}")
    print(f"[INFO] Segment: {SEGMENT_TIME} sekund")
    print(f"[INFO] Format: {WIDTH}x{HEIGHT} @ {FPS}fps")
    print("[INFO] To'xtatish uchun CTRL+C bosing\n")

    signal.signal(signal.SIGINT, stop_ffmpeg)
    signal.signal(signal.SIGTERM, stop_ffmpeg)

    process = subprocess.Popen(cmd)
    process.wait()

if __name__ == "__main__":
    main()
