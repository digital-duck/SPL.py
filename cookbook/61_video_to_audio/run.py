#!/usr/bin/env python3
"""
run.py — physical runner for Recipe 61: Video to Audio.

Extracts the audio track from a video file using ffmpeg (via the shared
cookbook/tools/video_tools.py::extract_audio() helper). No LLM is required
— this is a deterministic codec operation.

Usage
-----
  # MP4 → MP3 (default)
  python cookbook/61_video_to_audio/run.py \\
      --video cookbook/61_video_to_audio/sample/clip.mp4

  # MP4 → WAV (lossless, high sample rate)
  python cookbook/61_video_to_audio/run.py \\
      --video cookbook/61_video_to_audio/sample/clip.mp4 \\
      --target-format wav --sample-rate 48000

  # MP4 → FLAC (lossless compressed, archival)
  python cookbook/61_video_to_audio/run.py \\
      --video cookbook/61_video_to_audio/sample/clip.mp4 \\
      --target-format flac

  # High-quality MP3
  python cookbook/61_video_to_audio/run.py \\
      --video cookbook/61_video_to_audio/sample/clip.mp4 \\
      --target-format mp3 --bitrate 320k

  # Custom output directory
  python cookbook/61_video_to_audio/run.py \\
      --video cookbook/61_video_to_audio/sample/clip.mp4 \\
      --output-dir /tmp/audio
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import click

# ── Path setup (run from repo root or recipe directory) ───────────────────────
_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))

from cookbook.tools.video_tools import extract_audio as _extract_audio_impl  # noqa: E402

_SUPPORTED_FORMATS = {"mp3", "wav", "ogg", "flac", "aac", "m4a", "opus"}


def _check_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        print("[video_to_audio] ERROR: ffmpeg not found.")
        print("  Ubuntu/Debian: sudo apt install ffmpeg")
        print("  macOS:         brew install ffmpeg")
        sys.exit(1)


def extract_audio(
    video_path: str,
    target_format: str,
    bitrate: str,
    sample_rate: int,
    output_dir: str,
) -> Path:
    _check_ffmpeg()

    fmt = target_format.strip().lower().lstrip(".")
    if fmt not in _SUPPORTED_FORMATS:
        print(f"[video_to_audio] ERROR: Unsupported format '{fmt}'.")
        print(f"  Supported: {sorted(_SUPPORTED_FORMATS)}")
        sys.exit(1)

    src = Path(video_path.strip())
    if not src.exists():
        print(f"[video_to_audio] ERROR: Source file not found: {src}")
        sys.exit(1)

    print(f"[video_to_audio] extracting audio from {src.name}  "
          f"(target_format={fmt}, bitrate={bitrate}, sample_rate={sample_rate})")

    try:
        dst = _extract_audio_impl(
            video_path=str(src),
            target_format=fmt,
            bitrate=bitrate,
            sample_rate=str(sample_rate),
            output_dir=output_dir,
        )
    except (ValueError, RuntimeError) as exc:
        print(f"[video_to_audio] ERROR: {exc}")
        sys.exit(1)

    dst = Path(dst)
    print(f"[video_to_audio] saved → {dst}")
    return dst


@click.command()
@click.option("--video",         required=True, help="Source video file path")
@click.option("--target-format", default="mp3", show_default=True,
              type=click.Choice(sorted(_SUPPORTED_FORMATS)))
@click.option("--bitrate",       default="192k", show_default=True,
              help="Bitrate for lossy formats, e.g. 128k, 192k, 320k")
@click.option("--sample-rate",   default=44100, show_default=True, type=int,
              help="Output sample rate in Hz")
@click.option("--output-dir",    default="cookbook/61_video_to_audio/outputs", show_default=True)
def main(video, target_format, bitrate, sample_rate, output_dir) -> None:
    """Recipe 61 — Video to Audio Extraction (SPL 3.0)."""
    dst = extract_audio(
        video_path=video,
        target_format=target_format,
        bitrate=bitrate,
        sample_rate=sample_rate,
        output_dir=output_dir,
    )

    click.echo()
    click.echo("── Result ───────────────────────────────────────────────────────────")
    click.echo(f"Extracted audio: {dst}")
    click.echo("─────────────────────────────────────────────────────────────────────")


if __name__ == "__main__":
    main()
