import subprocess
import os
import signal
import sys

# =========================
# SOZLAMALAR
# =========================
VIDEO_DEVICE = "/dev/video25"

# arecord -l bilan tekshirib to'g'ri device qo'yiladi
# masalan: "hw:1,0" yoki "hw:2,0"
AUDIO_DEVICE = "hw:3,0"

OUTPUT_DIR = "records"
SEGMENT_TIME = 10

WIDTH = 1920
HEIGHT = 1080
FPS = 30

# CPU yengilroq ishlashi uchun preset ultrafast
# sifatni CRF boshqaradi: 18 juda sifatli, 20-23 normal
CRF = "20"
PRESET = "ultrafast"

process = None


def build_ffmpeg_command():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    output_pattern = os.path.join(
        OUTPUT_DIR,
        "cam_%Y-%m-%d_%H-%M-%S.mp4"
    )

    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "info",
        "-y",

        # INPUT buffering
        "-thread_queue_size", "4096",

        # Kamera input
        "-f", "v4l2",

        # Ko'p webcamlarda 1080p30 uchun shu juda muhim
        "-input_format", "mjpeg",

        "-framerate", str(FPS),
        "-video_size", f"{WIDTH}x{HEIGHT}",
        "-use_wallclock_as_timestamps", "1",
        "-i", VIDEO_DEVICE,

        # Audio input
        "-thread_queue_size", "4096",
        "-f", "alsa",
        "-ac", "1",
        "-ar", "44100",
        "-i", AUDIO_DEVICE,

        # Video encode
        "-c:v", "libx264",
        "-preset", PRESET,
        "-crf", CRF,
        "-pix_fmt", "yuv420p",
        "-r", str(FPS),
        "-g", str(FPS * 2),

        # Audio encode
        "-c:a", "aac",
        "-b:a", "128k",
        "-af", "aresample=async=1:first_pts=0",

        # MP4 mosligi
        "-movflags", "+faststart",

        # Segment qilib yozish
        "-f", "segment",
        "-segment_time", str(SEGMENT_TIME),
        "-reset_timestamps", "1",
        "-strftime", "1",

        output_pattern
    ]

    return cmd


def stop_ffmpeg(signum=None, frame=None):
    global process
    print("\n[INFO] Recording to'xtatilmoqda...")

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
    print(f"[INFO] Video device: {VIDEO_DEVICE}")
    print(f"[INFO] Audio device: {AUDIO_DEVICE}")
    print(f"[INFO] Resolution: {WIDTH}x{HEIGHT}")
    print(f"[INFO] FPS: {FPS}")
    print(f"[INFO] Segment time: {SEGMENT_TIME} sekund")
    print(f"[INFO] Output dir: {OUTPUT_DIR}")
    print("[INFO] To'xtatish uchun CTRL+C bosing\n")

    signal.signal(signal.SIGINT, stop_ffmpeg)
    signal.signal(signal.SIGTERM, stop_ffmpeg)

    process = subprocess.Popen(cmd)
    process.wait()


if __name__ == "__main__":
    main()