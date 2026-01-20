#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTS Audio Pre-generation Script

Generates audio files for all words in CSV files.
Priority: Free Dictionary API > ElevenLabs API (fallback)

Usage:
    python3 generate_audio.py

Features:
- Skips already generated audio files (checks file existence and size)
- Uses Free Dictionary API first (free, accurate)
- Falls back to ElevenLabs API if needed
- Progress tracking and statistics
- Resumable (can stop and restart)
"""

import os
import csv
import time
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Set, Tuple
import requests
from tqdm import tqdm


# ==================== Configuration ====================

WORDS_DIR = Path("docs/words")
AUDIO_OUTPUT_DIR = Path("docs/audio")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"  # George - English
ELEVENLABS_MODEL = "eleven_multilingual_v2"

# Rate limiting
DICTIONARY_DELAY = 0.1  # 100ms between calls
ELEVENLABS_DELAY = 0.5  # 500ms between calls (rate limit protection)

# Minimum valid audio file size (bytes)
MIN_AUDIO_SIZE = 1024  # 1KB - smaller files are likely corrupted


# ==================== Helper Functions ====================


def get_audio_filename(word: str) -> str:
    """
    Generate consistent filename for a word.
    Uses hash to handle special characters safely.
    """
    # Normalize: lowercase, strip whitespace
    normalized = word.lower().strip()

    # Use hash for filename to avoid special character issues
    hash_part = hashlib.md5(normalized.encode()).hexdigest()[:8]

    # Keep readable part (alphanumeric only)
    safe_word = "".join(c for c in normalized if c.isalnum())[:20]

    return f"{safe_word}_{hash_part}.mp3"


def is_audio_file_valid(filepath: Path) -> bool:
    """
    Check if audio file exists and is valid (non-empty, reasonable size).

    Returns:
        True if file exists and appears valid, False otherwise
    """
    if not filepath.exists():
        return False

    # Check file size
    size = filepath.stat().st_size
    if size < MIN_AUDIO_SIZE:
        print(f"⚠️  Invalid file (too small: {size} bytes): {filepath.name}")
        return False

    return True


def collect_unique_words(words_dir: Path) -> Set[str]:
    """
    Collect all unique words from CSV files.

    Returns:
        Set of unique words (normalized to lowercase)
    """
    unique_words = set()

    csv_files = list(words_dir.glob("*.csv"))
    print(f"📂 Found {len(csv_files)} CSV files")

    for csv_file in csv_files:
        try:
            # Try UTF-8 first, fallback to other encodings
            for encoding in ["utf-8", "cp949", "euc-kr", "latin-1"]:
                try:
                    with open(csv_file, "r", encoding=encoding) as f:
                        reader = csv.reader(f)
                        for row in reader:
                            if len(row) >= 2 and row[0].strip():
                                word = row[0].strip().lower()
                                unique_words.add(word)
                    break  # Success, exit encoding loop
                except UnicodeDecodeError:
                    continue  # Try next encoding
        except Exception as e:
            print(f"⚠️  Error reading {csv_file.name}: {e}")

    return unique_words


def filter_existing_audio(
    words: Set[str], audio_dir: Path
) -> Tuple[Set[str], Set[str]]:
    """
    Filter out words that already have valid audio files.

    Returns:
        Tuple of (words_needing_audio, words_with_audio)
    """
    words_needing_audio = set()
    words_with_audio = set()

    for word in words:
        filename = get_audio_filename(word)
        filepath = audio_dir / filename

        if is_audio_file_valid(filepath):
            words_with_audio.add(word)
        else:
            words_needing_audio.add(word)

    return words_needing_audio, words_with_audio


# ==================== TTS API Functions ====================


def fetch_from_dictionary_api(word: str) -> bytes | None:
    """
    Fetch audio from Free Dictionary API (free, accurate for English words).

    Returns:
        Audio bytes if successful, None otherwise
    """
    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            return None

        data = response.json()
        phonetics = data[0].get("phonetics", [])

        # Find first phonetic with audio
        for phonetic in phonetics:
            audio_url = phonetic.get("audio")
            if audio_url:
                audio_response = requests.get(audio_url, timeout=10)
                if audio_response.status_code == 200:
                    audio_data = audio_response.content
                    if len(audio_data) >= MIN_AUDIO_SIZE:
                        return audio_data

        return None

    except Exception as e:
        print(f"  ⚠️  Dictionary API error for '{word}': {e}")
        return None


def fetch_from_elevenlabs(word: str, api_key: str) -> bytes | None:
    """
    Fetch audio from ElevenLabs API (costs money, but works for any text).

    Returns:
        Audio bytes if successful, None otherwise
    """
    if not api_key:
        return None

    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"

        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key,
        }

        data = {
            "text": word,
            "model_id": ELEVENLABS_MODEL,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
            },
        }

        response = requests.post(url, headers=headers, json=data, timeout=15)

        if response.status_code == 200:
            audio_data = response.content
            if len(audio_data) >= MIN_AUDIO_SIZE:
                return audio_data
        else:
            print(
                f"  ⚠️  ElevenLabs API error for '{word}': HTTP {response.status_code}"
            )

        return None

    except Exception as e:
        print(f"  ⚠️  ElevenLabs API error for '{word}': {e}")
        return None


def generate_audio_for_word(
    word: str, output_path: Path, use_elevenlabs: bool = True
) -> bool:
    """
    Generate audio for a single word.

    Strategy:
    1. Check if file already exists and is valid -> skip
    2. Try Dictionary API first (free)
    3. Fallback to ElevenLabs if enabled

    Returns:
        True if audio was generated/exists, False otherwise
    """
    # Double-check: Skip if file already exists and is valid
    if is_audio_file_valid(output_path):
        return True

    # Try Dictionary API first
    audio_data = fetch_from_dictionary_api(word)
    source = "Dictionary"

    if audio_data:
        time.sleep(DICTIONARY_DELAY)
    elif use_elevenlabs:
        # Fallback to ElevenLabs
        audio_data = fetch_from_elevenlabs(word, ELEVENLABS_API_KEY)
        source = "ElevenLabs"
        if audio_data:
            time.sleep(ELEVENLABS_DELAY)

    if not audio_data:
        return False

    # Save audio file
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to temporary file first, then rename (atomic operation)
        temp_path = output_path.with_suffix(".tmp")
        temp_path.write_bytes(audio_data)

        # Verify written file
        if temp_path.stat().st_size < MIN_AUDIO_SIZE:
            temp_path.unlink()
            print(f"  ⚠️  Generated file too small for '{word}'")
            return False

        # Atomic rename
        temp_path.rename(output_path)

        print(f"  ✅ Generated: {word} ({source}, {len(audio_data)} bytes)")
        return True

    except Exception as e:
        print(f"  ⚠️  Failed to save '{word}': {e}")
        if temp_path.exists():
            temp_path.unlink()
        return False


# ==================== Main Function ====================


def main():
    """Main execution function."""

    print("=" * 70)
    print("🎵 TTS Audio Pre-generation Script")
    print("=" * 70)

    # Validate directories
    if not WORDS_DIR.exists():
        print(f"❌ Words directory not found: {WORDS_DIR}")
        return

    AUDIO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Collect unique words
    print("\n📋 Collecting words from CSV files...")
    all_words = collect_unique_words(WORDS_DIR)
    print(f"   Found {len(all_words)} unique words")

    # Filter already generated
    print("\n🔍 Checking for existing audio files...")
    words_to_generate, existing_words = filter_existing_audio(
        all_words, AUDIO_OUTPUT_DIR
    )

    print(f"   ✅ Already generated: {len(existing_words)} words")
    print(f"   ⏳ Need to generate: {len(words_to_generate)} words")

    if len(words_to_generate) == 0:
        print("\n🎉 All audio files already exist! Nothing to do.")
        return

    # Check ElevenLabs API key
    use_elevenlabs = bool(ELEVENLABS_API_KEY)
    if use_elevenlabs:
        print(f"   🔑 ElevenLabs API key: configured")
    else:
        print(
            f"   ⚠️  ElevenLabs API key: NOT configured (will use Dictionary API only)"
        )

    # Confirm before proceeding
    print(f"\n🚀 Ready to generate {len(words_to_generate)} audio files")
    print(f"   Output directory: {AUDIO_OUTPUT_DIR.absolute()}")

    response = input("\nProceed? [y/N]: ").strip().lower()
    if response not in ["y", "yes"]:
        print("❌ Cancelled by user")
        return

    # Generate audio files
    print(f"\n⚙️  Generating audio files...")
    print("=" * 70)

    stats = {
        "success": 0,
        "failed": 0,
        "skipped": 0,
    }

    words_list = sorted(words_to_generate)

    for i, word in enumerate(tqdm(words_list, desc="Progress", unit="word")):
        # Final check before generation
        output_path = AUDIO_OUTPUT_DIR / get_audio_filename(word)

        if is_audio_file_valid(output_path):
            stats["skipped"] += 1
            continue

        success = generate_audio_for_word(word, output_path, use_elevenlabs)

        if success:
            stats["success"] += 1
        else:
            stats["failed"] += 1

    # Summary
    print("\n" + "=" * 70)
    print("📊 Generation Summary")
    print("=" * 70)
    print(f"   ✅ Successfully generated: {stats['success']}")
    print(f"   ⏭️  Skipped (already exist): {stats['skipped']}")
    print(f"   ❌ Failed: {stats['failed']}")
    print(
        f"   📁 Total files in {AUDIO_OUTPUT_DIR.name}/: {len(list(AUDIO_OUTPUT_DIR.glob('*.mp3')))}"
    )

    if stats["failed"] > 0:
        print(f"\n⚠️  Some words failed. You can re-run this script to retry.")

    print("\n✨ Done!")


if __name__ == "__main__":
    main()
