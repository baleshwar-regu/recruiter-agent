import pytest
import asyncio
import os
import shutil
from tests.interview_agent_test_runner import run_interview_test

TRANSCRIPTS_DIR = "transcripts"

def init_transcript_dir():
    if os.path.exists(TRANSCRIPTS_DIR):
        shutil.rmtree(TRANSCRIPTS_DIR)
    os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)

def save_transcript(persona: str, transcript: list[tuple[str, str]]):
    with open(f"{TRANSCRIPTS_DIR}/{persona}_transcript.txt", "w", encoding="utf-8") as f:
        for step, response in transcript:
            f.write(f"[{step}]\n{response}\n\n")

def run_common_assertions(persona: str, transcript: list[tuple[str, str]]):
    flat_text = " ".join(r for _, r in transcript).lower()

    assert "bigo1" in flat_text, f"[{persona}] Agent did not mention BIGO1"
    assert "bain" in flat_text, f"[{persona}] Agent did not mention Bain"
    assert "years of experience" in flat_text, f"[{persona}] Agent skipped experience question"
    assert "current project" in flat_text or "describe your project" in flat_text, f"[{persona}] Agent skipped project discussion"
    assert "sql" in flat_text, f"[{persona}] Agent did not ask SQL question"
    assert "do you have any questions" in flat_text, f"[{persona}] Agent skipped wrap-up question"

@pytest.mark.asyncio
async def test_strong_candidate():
    init_transcript_dir()
    transcript = await run_interview_test("strong")
    save_transcript("strong", transcript)
    run_common_assertions("strong", transcript)

@pytest.mark.asyncio
async def test_mediocre_candidate():
    transcript = await run_interview_test("mediocre")
    save_transcript("mediocre", transcript)
    run_common_assertions("mediocre", transcript)

@pytest.mark.asyncio
async def test_weak_candidate():
    transcript = await run_interview_test("weak")
    save_transcript("weak", transcript)
    run_common_assertions("weak", transcript)
