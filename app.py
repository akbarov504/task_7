import subprocess
import os
import signal
import sys
import time

# --- OUT (Tashqi) qurilmalar ---
OUT_VIDEO_DEVICE = "/dev/video25"
OUT_AUDIO_DEVICE = "hw:3,0" 

# --- IN (Ichki) qurilmalar ---
IN_VIDEO_DEVICE = "/dev/video29"
IN_AUDIO_DEVICE = "hw:4,0" 

OUTPUT_DIR = "records"
SEGMENT_TIME = 10

WIDTH = 1920
HEIGHT = 1080
FPS = 30

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Ikkala processni saqlash uchun ro'yxat
processes = []

def build_ffmpeg_command(video_device, audio_device, prefix):
    # Fayl nomi preffiks bilan (Masalan: OUT_2023... yoki IN_2023...) MP4 formatida
    timestamp_pattern = os.path.join(
        OUTPUT_DIR,
        f"{prefix}_%Y-%m-%d_%H-%M-%S.mp4"
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
        "-i", video_device,

        # AUDIO INPUT
        "-thread_queue_size", "2048",
        "-f", "alsa",
        "-channels", "2",
        "-sample_rate", "48000",
        "-i", audio_device,

        "-map", "0:v:0",
        "-map", "1:a:0",
        "-max_muxing_queue_size", "1024",

        # VIDEO OUTPUT (Copy rejim - Protsessor 0% qiynaladi)
        "-c:v", "copy",

        # AUDIO OUTPUT
        "-c:a", "aac",
        "-b:a", "128k",
        "-af", "aresample=async=1",

        # SEGMENT OUTPUT (MP4 formatiga o'zgartirildi)
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
            
    # Jarayonlar yopilishini biroz kutamiz
    time.sleep(2)
    
    for p in processes:
        if p and p.poll() is None:
            p.kill()

    print("[INFO] Hamma FFmpeg jarayonlari to'xtatildi.")
    sys.exit(0)

def main():
    global processes

    # 1. OUT buyrug'ini tuzamiz
    cmd_out = build_ffmpeg_command(OUT_VIDEO_DEVICE, OUT_AUDIO_DEVICE, "OUT")
    # 2. IN buyrug'ini tuzamiz
    cmd_in = build_ffmpeg_command(IN_VIDEO_DEVICE, IN_AUDIO_DEVICE, "IN")

    print("[INFO] Live recording boshlandi (COPY MODE | MP4)")
    print(f"[INFO] 1-Kamera (OUT): {OUT_VIDEO_DEVICE} | Mic: {OUT_AUDIO_DEVICE}")
    print(f"[INFO] 2-Kamera (IN) : {IN_VIDEO_DEVICE} | Mic: {IN_AUDIO_DEVICE}")
    print(f"[INFO] Papka: {OUTPUT_DIR}")
    print(f"[INFO] Segment: {SEGMENT_TIME} sekund")
    print("[INFO] To'xtatish uchun CTRL+C bosing\n")

    # Dasturni xavfsiz to'xtatish uchun signallar
    signal.signal(signal.SIGINT, stop_ffmpeg)
    signal.signal(signal.SIGTERM, stop_ffmpeg)

    # Ikkala kamerani bir vaqtda ishga tushiramiz
    process_out = subprocess.Popen(cmd_out)
    process_in = subprocess.Popen(cmd_in)
    
    processes.append(process_out)
    processes.append(process_in)

    # Dastur yopilib ketmasligi uchun kutib turamiz
    process_out.wait()
    process_in.wait()

if __name__ == "__main__":
    main()