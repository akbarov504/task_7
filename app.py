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

os.makedirs(OUTPUT_DIR, exist_ok=True)

process = None

def build_ffmpeg_command():
    timestamp_pattern = os.path.join(
        OUTPUT_DIR,
        "cam_%Y-%m-%d_%H-%M-%S.mkv"
    )

    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "warning",

        "-fflags", "+genpts",

        # VIDEO INPUT
        "-thread_queue_size", "2048",
        "-f", "v4l2",
        "-input_format", "mjpeg",
        "-framerate", str(FPS),
        "-video_size", f"{WIDTH}x{HEIGHT}",
        "-i", VIDEO_DEVICE,

        # AUDIO INPUT
        "-thread_queue_size", "2048",
        "-f", "alsa",
        "-channels", "2",
        "-sample_rate", "48000",
        "-i", AUDIO_DEVICE,

        "-map", "0:v:0",
        "-map", "1:a:0",
        "-max_muxing_queue_size", "1024",

        # VIDEO OUTPUT (Copy rejim - Protsessor 0% qiynaladi)
        "-c:v", "copy",

        # AUDIO OUTPUT
        "-c:a", "aac",
        "-b:a", "128k",
        "-af", "aresample=async=1",

        # SEGMENT OUTPUT
        "-f", "segment",
        "-segment_time", str(SEGMENT_TIME),
        "-segment_format", "matroska",
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

    print("[INFO] Live recording boshlandi (COPY MODE)")
    print(f"[INFO] Kamera: {VIDEO_DEVICE}")
    print(f"[INFO] Mikrofon: {AUDIO_DEVICE}")
    print(f"[INFO] Papka: {OUTPUT_DIR}")
    print(f"[INFO] Segment: {SEGMENT_TIME} sekund")
    print("[INFO] To'xtatish uchun CTRL+C bosing\n")

    signal.signal(signal.SIGINT, stop_ffmpeg)
    signal.signal(signal.SIGTERM, stop_ffmpeg)

    process = subprocess.Popen(cmd)
    process.wait()

if __name__ == "__main__":
    main()