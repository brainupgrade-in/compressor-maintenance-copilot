"""Assemble the demo video: one still per scene with a slow zoom, its narration, and background music that
ducks under the voice. Inputs: scenes.json, build/{slides,app}/*.png, build/voice/<id>.mp3, the music file.

    python3 submission/video/assemble.py ~/Music/Inspired.mp3
Output: build/compressor-copilot-demo.mp4 (1920x1080, 30 fps, H.264 + AAC)
"""
import json
import subprocess
import sys
from pathlib import Path

VIDEO = Path(__file__).resolve().parent
BUILD = VIDEO / "build"
MUSIC = Path(sys.argv[1]).expanduser()
LEAD, TAIL, FPS = 0.5, 0.7, 30  # silence before and after each narration, seconds


def run(*cmd):
    subprocess.run(cmd, check=True, capture_output=True)


def duration(f: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                         capture_output=True, text=True, check=True).stdout
    return float(out)


clips, voices, total = [], [], 0.0
(BUILD / "clips").mkdir(exist_ok=True)
for s in json.loads((VIDEO / "scenes.json").read_text()):
    voice = BUILD / "voice" / f"{s['id']}.mp3"
    d = LEAD + duration(voice) + TAIL
    frames = round(d * FPS)
    clip = BUILD / "clips" / f"{s['id']}.mp4"
    # 2x upscale first so the zoom is smooth; zoom 1.00 -> 1.04 across the scene; fade in/out 0.3 s
    vf = (f"scale=3840:2160,zoompan=z='1+0.04*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
          f":d={frames}:s=1920x1080:fps={FPS},fade=t=in:st=0:d=0.3,fade=t=out:st={d - 0.3:.3f}:d=0.3,format=yuv420p")
    run("ffmpeg", "-y", "-loop", "1", "-i", str(BUILD / s["visual"]), "-t", f"{d:.3f}", "-vf", vf,
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-r", str(FPS), str(clip))
    clips.append(clip)
    voices.append((voice, total + LEAD))
    total += d
    print(f"scene {s['id']}: {d:.1f}s")

(BUILD / "clips.txt").write_text("".join(f"file '{c}'\n" for c in clips))
run("ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(BUILD / "clips.txt"), "-c", "copy", str(BUILD / "video.mp4"))

# narration track: each clip placed at its scene's start
inputs, parts = [], []
for i, (v, start) in enumerate(voices):
    inputs += ["-i", str(v)]
    ms = round(start * 1000)
    parts.append(f"[{i}:a]adelay={ms}|{ms},aresample=44100[v{i}]")
mix = "".join(f"[v{i}]" for i in range(len(voices)))
run("ffmpeg", "-y", *inputs, "-filter_complex",
    ";".join(parts) + f";{mix}amix=inputs={len(voices)}:normalize=0,apad=whole_dur={total:.3f}[out]",
    "-map", "[out]", "-t", f"{total:.3f}", str(BUILD / "narration.wav"))

# music: quieter base level, ducked further while the narrator speaks (sidechain), faded in and out
run("ffmpeg", "-y", "-i", str(BUILD / "narration.wav"), "-stream_loop", "-1", "-i", str(MUSIC), "-filter_complex",
    f"[1:a]atrim=0:{total:.3f},asetpts=PTS-STARTPTS,volume=0.2,afade=t=in:d=2,"
    f"afade=t=out:st={total - 4:.3f}:d=4[m];"
    "[0:a]asplit=2[sc][nar];"
    "[m][sc]sidechaincompress=threshold=0.015:ratio=10:attack=30:release=600[duck];"
    "[nar][duck]amix=inputs=2:normalize=0,alimiter=limit=0.95[a]",
    "-map", "[a]", "-t", f"{total:.3f}", "-c:a", "pcm_s16le", str(BUILD / "audio.wav"))

out = BUILD / "compressor-copilot-demo.mp4"
run("ffmpeg", "-y", "-i", str(BUILD / "video.mp4"), "-i", str(BUILD / "audio.wav"), "-map", "0:v", "-map", "1:a",
    "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",  # web loudness
    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out))
print(f"wrote {out} ({total:.1f}s, {out.stat().st_size / 1e6:.1f} MB)")
