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
        # Muammo qayerdaligini ko'rish uchun "warning" o'rniga "info" qilib turamiz
        "-loglevel", "info",

        # timing
        "-fflags", "+genpts",

        # VIDEO INPUT
        "-thread_queue_size", "4096", # Kichraytirilgan, lekin yetarli bufer
        "-use_wallclock_as_timestamps", "1", # Qaytarib qo'shildi (Sinxronizatsiya uchun muhim)
        "-f", "v4l2",
        "-input_format", "mjpeg",
        "-framerate", str(FPS),
        "-video_size", f"{WIDTH}x{HEIGHT}",
        "-i", VIDEO_DEVICE,

        # AUDIO INPUT
        "-thread_queue_size", "4096",
        "-use_wallclock_as_timestamps", "1", # Qaytarib qo'shildi
        "-f", "alsa",
        "-i", AUDIO_DEVICE,

        # map
        "-map", "0:v:0",
        "-map", "1:a:0",

        # VIDEO
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-tune", "zerolatency",
        "-crf", VIDEO_CRF,
        "-pix_fmt", "yuv420p",
        "-r", str(FPS),

        # Segment aniq kesilishi uchun
        "-g", str(FPS * SEGMENT_TIME),
        "-keyint_min", str(FPS * SEGMENT_TIME),
        "-sc_threshold", "0",
        "-force_key_frames", f"expr:gte(t,n_forced*{SEGMENT_TIME})",

        # AUDIO
        # AAC formatini ishlatamiz, chunki PCM ba'zan MKV ni kesishda uzilishlar qiladi
        "-c:a", "aac",
        "-b:a", "128k",
        "-ar", "48000",
        "-ac", "2",
        # Asl nusxadagi aresample ni qaytaramiz, chunki wallclock ishlatilganda bu yaxshi ishlaydi
        "-af", "aresample=async=1000",

        # SEGMENT
        "-f", "segment",
        "-segment_time", str(SEGMENT_TIME),
        "-segment_time_delta", "0.05",
        "-reset_timestamps", "1",
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

    print("[INFO] Live recording boshlandi")
    print(f"[INFO] Kamera: {VIDEO_DEVICE}")
    print(f"[INFO] Mikrofon: {AUDIO_DEVICE}")
    print(f"[INFO] Papka: {OUTPUT_DIR}")
    print(f"[INFO] Segment: {SEGMENT_TIME} sekund")
    print(f"[INFO] To'xtatish uchun CTRL+C bosing\n")

    signal.signal(signal.SIGINT, stop_ffmpeg)
    signal.signal(signal.SIGTERM, stop_ffmpeg)

    process = subprocess.Popen(cmd)
    process.wait()

if __name__ == "__main__":
    main()