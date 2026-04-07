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

os.makedirs(OUTPUT_DIR, exist_ok=True)
processes = []

def build_ffmpeg_command(video_device, audio_device, channels, sample_rate, prefix):
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
        "-strftime", "1",

        timestamp_pattern
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

def main():
    global processes

    cmd_out = build_ffmpeg_command(OUT_VIDEO_DEVICE, OUT_AUDIO_DEVICE, "2", "48000", "OUT")
    cmd_in = build_ffmpeg_command(IN_VIDEO_DEVICE, IN_AUDIO_DEVICE, "2", "48000", "IN")

    print("[INFO] Live recording boshlandi (COPY MODE | MP4)")
    print(f"[INFO] 1-Kamera (OUT): {OUT_VIDEO_DEVICE} | Mic: {OUT_AUDIO_DEVICE}")
    print(f"[INFO] 2-Kamera (IN) : {IN_VIDEO_DEVICE} | Mic: {IN_AUDIO_DEVICE}")
    print(f"[INFO] Papka: {OUTPUT_DIR}")
    print(f"[INFO] Segment: {SEGMENT_TIME} sekund")
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
