import subprocess
import os
import signal
import sys
from datetime import datetime

VIDEO_DEVICE = "/dev/video25"
AUDIO_DEVICE = "plughw:3,0"

OUTPUT_DIR = "records"
SEGMENT_TIME = 10

WIDTH = 1920
HEIGHT = 1080
FPS = 30

VIDEO_CRF = "23"
AUDIO_BITRATE = "128k"

running = True
current_process = None

os.makedirs(OUTPUT_DIR, exist_ok=True)


def build_output_filename():
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return os.path.join(OUTPUT_DIR, f"cam_{now}.mp4")


def build_ffmpeg_command(output_file):
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "warning",
        "-y",

        # VIDEO INPUT
        "-thread_queue_size", "4096",
        "-f", "v4l2",
        "-input_format", "mjpeg",
        "-framerate", str(FPS),
        "-video_size", f"{WIDTH}x{HEIGHT}",
        "-i", VIDEO_DEVICE,

        # AUDIO INPUT
        "-thread_queue_size", "4096",
        "-f", "alsa",
        "-i", AUDIO_DEVICE,

        # MAP
        "-map", "0:v:0",
        "-map", "1:a:0",

        # RECORD ONLY 10 SECONDS
        "-t", str(SEGMENT_TIME),

        # VIDEO ENCODE
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-tune", "zerolatency",
        "-crf", VIDEO_CRF,
        "-pix_fmt", "yuv420p",
        "-r", str(FPS),
        "-g", str(FPS * 2),

        # AUDIO ENCODE
        "-c:a", "aac",
        "-b:a", AUDIO_BITRATE,
        "-ar", "48000",
        "-ac", "2",

        # OUTPUT
        "-movflags", "+faststart",
        output_file
    ]
    return cmd


def stop_all(signum=None, frame=None):
    global running, current_process
    print("\n[INFO] Yozuv to'xtatilmoqda...")
    running = False

    if current_process and current_process.poll() is None:
        current_process.terminate()
        try:
            current_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            current_process.kill()

    print("[INFO] Dastur to'xtadi.")
    sys.exit(0)


def main():
    global current_process

    print("[INFO] Live recording boshlandi")
    print(f"[INFO] Kamera: {VIDEO_DEVICE}")
    print(f"[INFO] Mikrofon: {AUDIO_DEVICE}")
    print(f"[INFO] Papka: {OUTPUT_DIR}")
    print(f"[INFO] Har fayl: {SEGMENT_TIME} sekund")
    print(f"[INFO] Format: {WIDTH}x{HEIGHT} @ {FPS}fps")
    print("[INFO] To'xtatish uchun CTRL+C bosing\n")

    signal.signal(signal.SIGINT, stop_all)
    signal.signal(signal.SIGTERM, stop_all)

    while running:
        output_file = build_output_filename()
        cmd = build_ffmpeg_command(output_file)

        print(f"[INFO] Yozilyapti: {output_file}")
        current_process = subprocess.Popen(cmd)
        current_process.wait()

        if current_process.returncode != 0 and running:
            print("[WARNING] FFmpeg xato bilan tugadi, 1 sekunddan keyin qayta uriniladi...")
            import time
            time.sleep(1)


if __name__ == "__main__":
    main()