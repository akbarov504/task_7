import subprocess
import os
import signal
import sys
import time

OUT_VIDEO_DEVICE = "/dev/video29"
OUT_AUDIO_DEVICE = "hw:4,0"

IN_VIDEO_DEVICE = "/dev/video25"
IN_AUDIO_DEVICE = "hw:3,0" 

OUTPUT_DIR = "records"
SEGMENT_TIME = 10

WIDTH = 1920
HEIGHT = 1080
FPS = 30

# AI team uchun UDP stream portlari
OUT_STREAM_URL = "udp://127.0.0.1:23000?pkt_size=1316"
IN_STREAM_URL = "udp://127.0.0.1:23001?pkt_size=1316"

# Streamni yengil qilish uchun
STREAM_WIDTH = 1280
STREAM_HEIGHT = 720
STREAM_FPS = 15

os.makedirs(OUTPUT_DIR, exist_ok=True)
processes = []

def build_ffmpeg_command(video_device, audio_device, channels, sample_rate, prefix, stream_url):
    timestamp_pattern = os.path.join(
        OUTPUT_DIR,
        f"{prefix}_%Y-%m-%d_%H-%M-%S.mp4"
    )

    cmd = [
        "ffmpeg",
        "-nostdin",
        "-hide_banner",
        "-loglevel", "warning",
        "-fflags", "+genpts",

        "-thread_queue_size", "2048",
        "-f", "v4l2",
        "-input_format", "mjpeg",
        "-framerate", str(FPS),
        "-video_size", f"{WIDTH}x{HEIGHT}",
        "-i", video_device,

        "-thread_queue_size", "2048",
        "-f", "alsa",
        "-channels", channels,
        "-sample_rate", sample_rate,
        "-i", audio_device,

        "-map", "0:v:0",
        "-map", "1:a:0",
        "-max_muxing_queue_size", "1024",

        "-c:v", "copy",

        "-c:a", "aac",
        "-b:a", "128k",
        "-af", "aresample=async=1",

        "-f", "segment",
        "-segment_time", str(SEGMENT_TIME),
        "-segment_format", "mp4",
        "-reset_timestamps", "1",
        "-strftime", "1",

        timestamp_pattern,

        "-map", "0:v:0",
        "-an",
        "-vf", f"scale={STREAM_WIDTH}:{STREAM_HEIGHT},fps={STREAM_FPS}",
        "-pix_fmt", "yuv420p",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-tune", "zerolatency",
        "-g", str(STREAM_FPS * 2),
        "-bf", "0",
        "-f", "mpegts",
        stream_url,
    ]
    return cmd

def stop_ffmpeg(signum=None, frame=None):
    global processes
    print("\n[INFO] Ikkala yozuv ham to'xtatilmoqda...")

    for p in processes:
        if p and p.poll() is None:
            p.terminate()
            
    time.sleep(2)
    
    for p in processes:
        if p and p.poll() is None:
            p.kill()

    print("[INFO] Hamma FFmpeg jarayonlari to'xtatildi.")
    sys.exit(0)

def check_path_exists(path_value, label):
    if not os.path.exists(path_value):
        print(f"[ERROR] {label} topilmadi: {path_value}")
        return False
    return True

def main():
    global processes

    if not check_path_exists(OUT_VIDEO_DEVICE, "OUT video device"):
        sys.exit(1)

    if not check_path_exists(IN_VIDEO_DEVICE, "IN video device"):
        sys.exit(1)

    cmd_out = build_ffmpeg_command(OUT_VIDEO_DEVICE, OUT_AUDIO_DEVICE, "2", "48000", "OUT", OUT_STREAM_URL)
    cmd_in = build_ffmpeg_command(IN_VIDEO_DEVICE, IN_AUDIO_DEVICE, "2", "48000", "IN", IN_STREAM_URL)

    print("[INFO] Live recording + UDP stream boshlandi")
    print(f"[INFO] OUT kamera: {OUT_VIDEO_DEVICE} | Mic: {OUT_AUDIO_DEVICE}")
    print(f"[INFO] IN  kamera: {IN_VIDEO_DEVICE} | Mic: {IN_AUDIO_DEVICE}")
    print(f"[INFO] Papka: {OUTPUT_DIR}")
    print(f"[INFO] Segment vaqti: {SEGMENT_TIME} sekund")
    print(f"[INFO] OUT stream: {OUT_STREAM_URL}")
    print(f"[INFO] IN  stream: {IN_STREAM_URL}")
    print(f"[INFO] Stream size: {STREAM_WIDTH}x{STREAM_HEIGHT} @ {STREAM_FPS} fps")
    print("[INFO] To'xtatish uchun CTRL+C bosing\n")

    signal.signal(signal.SIGINT, stop_ffmpeg)
    signal.signal(signal.SIGTERM, stop_ffmpeg)

    process_out = subprocess.Popen(cmd_out)
    process_in = subprocess.Popen(cmd_in)
    
    processes.append(process_out)
    processes.append(process_in)

    process_out.wait()
    process_in.wait()

if __name__ == "__main__":
    main()
