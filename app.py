import subprocess
import os
import signal
import sys

VIDEO_DEVICE = "/dev/video25"
AUDIO_DEVICE = "plughw:3,0"

OUTPUT_DIR = "records"
SEGMENT_TIME = 10

WIDTH = 1920
HEIGHT = 1080
FPS = 30

VIDEO_CRF = "23"
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

        # umumiy timing
        "-fflags", "+genpts",
        "-max_interleave_delta", "0",

        # VIDEO INPUT
        "-thread_queue_size", "8192",
        "-f", "v4l2",
        "-input_format", "mjpeg",
        "-framerate", str(FPS),
        "-video_size", f"{WIDTH}x{HEIGHT}",
        "-use_wallclock_as_timestamps", "1",
        "-i", VIDEO_DEVICE,

        # AUDIO INPUT
        "-thread_queue_size", "8192",
        "-f", "alsa",
        "-use_wallclock_as_timestamps", "1",
        "-i", AUDIO_DEVICE,

        # map
        "-map", "0:v:0",
        "-map", "1:a:0",

        # VIDEO ENCODE
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-tune", "zerolatency",
        "-crf", VIDEO_CRF,
        "-pix_fmt", "yuv420p",
        "-r", str(FPS),

        # har 10 sekund boshida keyframe majburiy
        "-g", str(FPS * SEGMENT_TIME),
        "-keyint_min", str(FPS * SEGMENT_TIME),
        "-sc_threshold", "0",
        "-force_key_frames", f"expr:gte(t,n_forced*{SEGMENT_TIME})",

        # AUDIO ENCODE
        "-c:a", "aac",
        "-b:a", AUDIO_BITRATE,
        "-ar", "48000",
        "-ac", "2",
        "-af", "aresample=async=1000:first_pts=0",

        # SEGMENT OUTPUT
        "-f", "segment",
        "-segment_time", str(SEGMENT_TIME),
        "-segment_time_delta", "0.05",
        "-reset_timestamps", "1",
        "-strftime", "1",
        "-movflags", "+faststart",

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