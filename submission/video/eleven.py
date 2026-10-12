"""ElevenLabs helpers for the demo video. ELEVENLABS_API_KEY is read from the env file named by
ELEVENLABS_ENV_FILE (default: the repo's .env); it is never printed.

    python3 eleven.py find Raje          # voice id lookup (account voices, then the shared library)
    python3 eleven.py tts <voice_id> <in.txt> <out.mp3>
"""
import json
import os
import sys
import urllib.parse
import urllib.request

ENV_FILE = os.environ.get("ELEVENLABS_ENV_FILE") or os.path.join(os.path.dirname(__file__), "../../.env")
KEY = next(l.split("=", 1)[1].strip().strip('"') for l in open(os.path.expanduser(ENV_FILE))
           if l.startswith("ELEVENLABS_API_KEY="))
API = "https://api.elevenlabs.io"


def call(path, body=None):
    req = urllib.request.Request(API + path, data=json.dumps(body).encode() if body else None,
                                 headers={"xi-api-key": KEY, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


if sys.argv[1] == "find":
    name = sys.argv[2].lower()
    mine = json.loads(call("/v1/voices"))["voices"]
    for v in mine:
        if name in v["name"].lower():
            print("account:", v["voice_id"], v["name"], v.get("labels"))
    shared = json.loads(call("/v1/shared-voices?" + urllib.parse.urlencode({"search": sys.argv[2], "page_size": 10})))
    for v in shared.get("voices", []):
        print("shared:", v["voice_id"], v["name"], v.get("accent"), v.get("gender"), v.get("descriptive"), v.get("public_owner_id"))
elif sys.argv[1] == "tts":
    voice, src, out = sys.argv[2:5]
    audio = call(f"/v1/text-to-speech/{voice}?output_format=mp3_44100_128",
                 {"text": open(src).read().strip(), "model_id": "eleven_multilingual_v2",
                  "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}})
    open(out, "wb").write(audio)
    print("wrote", out, len(audio), "bytes")
