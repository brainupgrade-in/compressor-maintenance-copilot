"""Generate an image with Gemini. GEMINI_API_KEY comes from the env file named by GEMINI_ENV_FILE (never printed).

    python3 gemini_image.py models
    python3 gemini_image.py make <model> <out.png> "<prompt>"
"""
import base64
import json
import os
import sys
import urllib.error
import urllib.request

KEY = next(l.split("=", 1)[1].strip().strip('"') for l in open(os.path.expanduser(os.environ["GEMINI_ENV_FILE"]))
           if l.startswith("GEMINI_API_KEY="))
API = "https://generativelanguage.googleapis.com/v1beta"


def call(path, body=None):
    req = urllib.request.Request(f"{API}/{path}", data=json.dumps(body).encode() if body else None,
                                 headers={"x-goog-api-key": KEY, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Gemini {e.code}: {e.read().decode()[:400]}")


if sys.argv[1] == "models":
    for m in call("models?pageSize=200")["models"]:
        if "image" in m["name"]:
            print(m["name"], "|", m.get("displayName"))
elif sys.argv[1] == "make":
    model, out, prompt = sys.argv[2:5]
    r = call(f"{model}:generateContent", {"contents": [{"parts": [{"text": prompt}]}],
                                          "generationConfig": {"responseModalities": ["IMAGE"],
                                                               "imageConfig": {"aspectRatio": "16:9"}}})
    for part in r["candidates"][0]["content"]["parts"]:
        if "inlineData" in part:
            open(out, "wb").write(base64.b64decode(part["inlineData"]["data"]))
            print("wrote", out)
            break
    else:
        raise SystemExit("no image in response: " + json.dumps(r)[:300])
