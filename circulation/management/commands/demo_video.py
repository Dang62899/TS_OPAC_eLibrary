import os
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT, FPS = 960, 540, 10
NAVY, GOLD, WHITE, GREY = (12, 35, 75), (212, 175, 55), (255, 255, 255), (200, 210, 225)
FONT_DIRS = ("C:/Windows/Fonts/", "")


def ffmpeg_path():
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return None


def _font(name, size):
    for folder in FONT_DIRS:
        try:
            return ImageFont.truetype(folder + name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap(draw, text, font, max_width):
    lines, current = [], ""
    for word in text.split():
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _frame(title, subtitle, bullets, t, total, fonts):
    image = Image.new("RGB", (WIDTH, HEIGHT), NAVY)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, WIDTH, 8), fill=GOLD)
    draw.rectangle((0, HEIGHT - 64, WIDTH, HEIGHT), fill=(8, 24, 54))
    draw.text((40, HEIGHT - 46), "TS eLibrary | Sample instructional video (demo data)", font=fonts["small"], fill=GREY)

    intro = 3.0
    slide = min(1.0, t / 1.0)
    offset = int((1 - slide) * 60)
    y = 50 + offset
    for line in _wrap(draw, title, fonts["title"], WIDTH - 80):
        draw.text((40, y), line, font=fonts["title"], fill=WHITE)
        y += 56
    draw.text((40, y + 4), subtitle, font=fonts["sub"], fill=GOLD)
    y += 70

    per_bullet = max(1.2, (total - intro - 2.0) / max(1, len(bullets)))
    for index, bullet in enumerate(bullets):
        start = intro + index * per_bullet
        if t < start:
            break
        fade = min(1.0, (t - start) / 0.6)
        color = tuple(int(NAVY[c] + (WHITE[c] - NAVY[c]) * fade) for c in range(3))
        draw.ellipse((44, y + 12, 58, y + 26), fill=GOLD)
        for line in _wrap(draw, bullet, fonts["body"], WIDTH - 130):
            draw.text((76, y), line, font=fonts["body"], fill=color)
            y += 34
        y += 14

    progress = int((WIDTH - 80) * (t / total))
    draw.rectangle((40, HEIGHT - 76, WIDTH - 40, HEIGHT - 70), fill=(40, 62, 105))
    draw.rectangle((40, HEIGHT - 76, 40 + progress, HEIGHT - 70), fill=GOLD)
    return image


def build_video(path, title, subtitle, bullets, seconds=24):
    """Render a short slide-style MP4 (H.264) at `path`. Returns False when no encoder is available."""
    exe = ffmpeg_path()
    if exe is None:
        return False
    fonts = {
        "title": _font("arialbd.ttf", 44),
        "sub": _font("arial.ttf", 26),
        "body": _font("arial.ttf", 28),
        "small": _font("arial.ttf", 18),
    }
    command = [
        exe, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{WIDTH}x{HEIGHT}",
        "-r", str(FPS), "-i", "-", "-f", "lavfi", "-i", f"sine=frequency=220:sample_rate=44100:duration={seconds}",
        "-filter:a", "volume=0.02", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast",
        "-c:a", "aac", "-shortest", "-movflags", "+faststart", path,
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    for number in range(seconds * FPS):
        frame = _frame(title, subtitle, bullets, number / FPS, seconds, fonts)
        process.stdin.write(frame.tobytes())
    process.stdin.close()
    return process.wait() == 0 and os.path.exists(path) and os.path.getsize(path) > 0


def build_video_bytes(title, subtitle, bullets, seconds=24):
    handle, path = tempfile.mkstemp(suffix=".mp4")
    os.close(handle)
    try:
        if not build_video(path, title, subtitle, bullets, seconds):
            return None
        with open(path, "rb") as source:
            return source.read()
    finally:
        os.remove(path)
