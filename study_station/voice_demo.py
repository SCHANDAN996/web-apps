"""Study Station: Hindi narration smoke test (does not publish or modify videos).

Install: pip install edge-tts
Run: python voice_demo.py --output demo_voice.mp3
Run with custom script: python voice_demo.py --text-file narration.txt --output voice.mp3

Requires network access to Microsoft's Edge TTS service and ffprobe (FFmpeg).
"""
import argparse
import asyncio
import json
import shutil
import subprocess
from pathlib import Path

DEMO_TEXT = (
    "रुकिए! क्या आपको पता है, भारत का संविधान कब लागू हुआ था? "
    "पाँच सेकंड में जवाब दीजिए। "
    "क्या आपका जवाब छब्बीस जनवरी, उन्नीस सौ पचास है? "
    "बिल्कुल सही! इसी दिन हमारा संविधान लागू हुआ और भारत गणराज्य बना। "
    "अब बताइए, संविधान सभा के अध्यक्ष कौन थे? "
    "अपना जवाब कमेंट में लिखिए।"
)


async def synthesize(text: str, output: Path, voice: str, rate: str):
    try:
        import edge_tts
    except ImportError as exc:
        raise SystemExit("Missing dependency. Install with: pip install edge-tts") from exc
    talker = edge_tts.Communicate(text, voice=voice, rate=rate)
    await talker.save(str(output))


def inspect_audio(path: Path):
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise SystemExit("ffprobe missing: install FFmpeg and retry")
    result = subprocess.run([
        ffprobe, "-v", "error", "-select_streams", "a:0", "-show_entries",
        "stream=codec_name:format=duration", "-of", "json", str(path)
    ], capture_output=True, text=True, check=True)
    info = json.loads(result.stdout)
    duration = float(info.get("format", {}).get("duration", 0))
    if not info.get("streams") or duration < 3:
        raise RuntimeError("Audio verification failed: no track or too-short duration")
    return duration, info["streams"][0].get("codec_name", "unknown")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--text-file", type=Path, help="UTF-8 narration text")
    parser.add_argument("--output", type=Path, default=Path("demo_voice.mp3"))
    parser.add_argument("--voice", default="hi-IN-SwaraNeural", help="Try hi-IN-MadhurNeural for male voice")
    parser.add_argument("--rate", default="+5%")
    args = parser.parse_args()
    text = args.text_file.read_text(encoding="utf-8").strip() if args.text_file else DEMO_TEXT
    if not text:
        parser.error("Narration text is empty")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    asyncio.run(synthesize(text, args.output, args.voice, args.rate))
    duration, codec = inspect_audio(args.output)
    print(f"PASS: {args.output} | duration={duration:.1f}s | codec={codec} | voice={args.voice}")
    if not (25 <= duration <= 45):
        print("NOTE: duration outside 25–45 seconds; adjust narration length or --rate.")


if __name__ == "__main__":
    main()
