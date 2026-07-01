"""
Ollama-based chat digest and summarizer with structured output.
Replaces heuristic logic in digest.py and sumy-based summarize.py.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import ollama
from pydantic import BaseModel, Field

from ..config import constants
from ..config.constants import MESSENGER_BUILTIN_MESSAGES

MODEL = "llama3.2"

# ─────────────────────────────────────────────────────────────────────────────
# Structured-output schemas
# ─────────────────────────────────────────────────────────────────────────────


class ThreadDigest(BaseModel):
    keywords: List[str] = Field(
        description="Up to 6 main topic keywords in Polish, lowercase base forms (e.g. 'piłka', 'wyjazd')"
    )
    summary: str = Field(
        description=(
            "A flowing, human-readable story in Polish (3–5 sentences) recounting what happened "
            "in this conversation thread: what was discussed, the mood, any notable moments. "
            "No bullet points, no headers — just prose."
        )
    )
    importance_score: float = Field(
        description=(
            "Importance score 0.0–10.0. Higher for: many participants, heated debate, "
            "rich topic, memorable moments. Lower for: small-talk, few messages, no clear topic."
        )
    )


class ChatDigest(BaseModel):
    threads: List[ThreadDigest]


class MonthlySummary(BaseModel):
    summary: str = Field(
        description=(
            "A flowing narrative in Polish (15-20 sentences) covering: the main topics discussed, "
            "recurring themes, the general mood, who was most vocal, any memorable or funny moments, "
            "and at least one direct quote if something stood out. No bullet points — just prose."
        )
    )


class ActiveDaySummary(BaseModel):
    date: str = Field(description="Date in YYYY-MM-DD format")
    summary: str = Field(
        description=(
            "A flowing, human-readable story in Polish (5-10 sentences) describing the day "
            "as if recounting it to a friend: what people talked about, the mood, any highlights. "
            "No bullet points, no headers — just prose."
        )
    )


# ─────────────────────────────────────────────────────────────────────────────
# Internal metadata container
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class ThreadResult:
    thread: List[Dict]
    digest: ThreadDigest
    start: datetime
    end: datetime
    authors: List[str]


# ─────────────────────────────────────────────────────────────────────────────
# Preprocessing helpers (algorithmic — kept out of the LLM)
# ─────────────────────────────────────────────────────────────────────────────

_URL_RE = re.compile(r"https?://\S+")
_WS_RE = re.compile(r"\s+")


def _clean_text(text: str) -> str:
    text = _URL_RE.sub("", text or "")
    text = text.replace("​", " ")
    return _WS_RE.sub(" ", text).strip()


def _is_builtin(content: str) -> bool:
    if not content:
        return False
    low = content.lower()
    return any(k.lower() in low for k in MESSENGER_BUILTIN_MESSAGES)


def _iter_messages(data: Dict) -> List[Dict]:
    msgs = sorted(data.get("messages", []), key=lambda m: m.get("timestamp_ms", 0))
    out = []
    for m in msgs:
        txt = _clean_text(m.get("content", "") or "")
        if txt and not _is_builtin(txt):
            out.append(
                {
                    "ts": m.get("timestamp_ms", 0),
                    "author": m.get("sender_name", "Unknown"),
                    "text": txt,
                }
            )
    return out


def _segment_threads(messages: List[Dict], time_gap_min: int = 60) -> List[List[Dict]]:
    if not messages:
        return []
    threads: List[List[Dict]] = []
    cur = [messages[0]]
    for prev, nxt in zip(messages, messages[1:]):
        if (nxt["ts"] - prev["ts"]) / 60_000 >= time_gap_min:
            threads.append(cur)
            cur = [nxt]
        else:
            cur.append(nxt)
    threads.append(cur)
    return threads


def _format_thread_for_prompt(thread: List[Dict]) -> str:
    lines = []
    for m in thread:
        ts = datetime.fromtimestamp(m["ts"] / 1000).strftime("%H:%M")
        lines.append(f"[{ts}] {m['author']}: {m['text']}")
    return "\n".join(lines)


def _ns_to_s(ns: float) -> str:
    return f"{ns * 1e-9:.2f}s"


# ─────────────────────────────────────────────────────────────────────────────
# Ollama calls
# ─────────────────────────────────────────────────────────────────────────────


def _analyse_thread(thread: List[Dict], model: str = MODEL) -> ThreadDigest:
    participants = ", ".join(sorted({m["author"] for m in thread}))
    start = datetime.fromtimestamp(thread[0]["ts"] / 1000).strftime("%Y-%m-%d %H:%M")
    end = datetime.fromtimestamp(thread[-1]["ts"] / 1000).strftime("%H:%M")
    thread_text = _format_thread_for_prompt(thread)

    prompt = (
        f"You are analysing a Polish-language group chat thread ({start}–{end}).\n"
        f"Participants: {participants}\n"
        f"Message count: {len(thread)}\n\n"
        "1. keywords: up to 6 main topic keywords in Polish base forms, lowercase. Avoid stopwords.\n\n"
        "2. summary: write a flowing story in Polish (3–5 sentences) recounting this thread "
        "as if telling a friend — what was discussed, the mood, any memorable moments. "
        "If something was particularly funny or interesting, quote it directly inline "
        '(e.g. Kowalski napisał: "dokładnie tak to było"). '
        "Do NOT use bullet points, headers, or lists — write only natural prose.\n\n"
        "3. importance_score: float 0.0–10.0. Higher for many participants, lively debate, "
        "rich topic, memorable moments. Lower for small-talk or few messages.\n\n"
        "Return ONLY valid JSON matching the schema. No markdown, no extra text.\n\n"
        f"Messages:\n{thread_text}"
    )

    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        format=ThreadDigest.model_json_schema(),
        options={"temperature": 0},
    )
    print(f"  [thread digest] {_ns_to_s(response.total_duration)}")
    return ThreadDigest.model_validate_json(response.message.content)


def _summarize_month(messages: List[Dict], model: str = MODEL) -> MonthlySummary:
    participants = sorted({m["author"] for m in messages})
    month_label = datetime.fromtimestamp(messages[0]["ts"] / 1000).strftime("%Y-%m") if messages else "?"

    # Sample evenly across the month so the model sees the full spread,
    # then cap total chars to leave enough context for output generation.
    max_chars = 12_000
    step = max(1, len(messages) // 300)
    sampled = messages[::step]
    lines: List[str] = []
    total = 0
    for m in sampled:
        line = f"{m['author']}: {m['text']}"
        total += len(line) + 1
        if total > max_chars:
            break
        lines.append(line)
    sample = "\n".join(lines)

    prompt = (
        f"You are summarising an entire month ({month_label}) of a Polish group chat.\n"
        f"Participants: {', '.join(participants)}\n"
        f"Total messages in the month: {len(messages)}\n\n"
        "Write a flowing narrative in Polish (15–20 sentences) that gives a real picture of this month. "
        "You MUST cover: (1) the main topics and recurring themes, (2) the general mood and dynamic between participants, "
        "(3) who was most active or vocal, (4) any memorable, funny, or heated moments, "
        "(5) at least one direct quote from the messages if something stood out "
        '(e.g. Kowalski napisał: "dokładnie tak to było"). '
        "Do NOT use bullet points, headers, or lists — write only natural flowing prose.\n\n"
        "Return ONLY valid JSON with a single 'summary' field. No markdown, no extra text.\n\n"
        f"Sample of messages from the month:\n{sample}"
    )

    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        format=MonthlySummary.model_json_schema(),
        options={"temperature": 0},
    )
    print(f"  [month summary] {_ns_to_s(response.total_duration)}")
    return MonthlySummary.model_validate_json(response.message.content)


def _summarize_day(date: str, message_lines: List[str], model: str = MODEL) -> ActiveDaySummary:
    text = "".join(message_lines)[:10_000]

    prompt = (
        f"You are summarising a single day ({date}) of a Polish group chat.\n\n"
        "Write a short flowing story in Polish (5-10 sentences) that recounts this day "
        "as if you were telling a friend: what people talked about, the mood, any highlights or funny moments. "
        "Do NOT use bullet points, headers, or lists — write only natural prose.\n\n"
        "Return ONLY valid JSON with a 'date' field (exactly: " + date + ") "
        "and a 'summary' field containing that story. No markdown, no extra text.\n\n"
        f"Messages:\n{text}"
    )

    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        format=ActiveDaySummary.model_json_schema(),
        options={"temperature": 0},
    )
    print(f"  [day summary {date}] {_ns_to_s(response.total_duration)}")
    result = ActiveDaySummary.model_validate_json(response.message.content)
    return ActiveDaySummary(date=date, summary=result.summary)


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────


def build_group_chat_digest(
    data: Dict,
    model: str = MODEL,
    time_gap_min: int = 60,
    min_thread_messages: int = 8,
    max_threads: int = 8,
) -> Tuple[ChatDigest, str]:
    """Returns (ChatDigest, formatted_text_in_Polish)."""
    messages = _iter_messages(data)
    if not messages:
        return (ChatDigest(threads=[]), "Brak wiadomości tekstowych do streszczenia.")

    raw_threads = [t for t in _segment_threads(messages, time_gap_min) if len(t) >= min_thread_messages]
    if not raw_threads:
        return (
            ChatDigest(threads=[]),
            "Nie wykryto wystarczająco dużych wątków. Zmniejsz min_thread_messages lub time_gap_min.",
        )

    results: List[ThreadResult] = []
    for thread in raw_threads:
        digest = _analyse_thread(thread, model=model)
        results.append(
            ThreadResult(
                thread=thread,
                digest=digest,
                start=datetime.fromtimestamp(thread[0]["ts"] / 1000),
                end=datetime.fromtimestamp(thread[-1]["ts"] / 1000),
                authors=sorted({m["author"] for m in thread}),
            )
        )

    results.sort(key=lambda r: r.digest.importance_score, reverse=True)
    top = results[:max_threads]

    chat_digest = ChatDigest(threads=[r.digest for r in top])
    return chat_digest, _render_digest_text(top)


def summarize_month(data: Dict, model: str = MODEL) -> MonthlySummary:
    messages = _iter_messages(data)
    if not messages:
        return MonthlySummary(summary="Brak wiadomości.")
    return _summarize_month(messages, model=model)


def summarize_most_active_days(
    active_days_messages: Dict[str, List[str]],
    model: str = MODEL,
) -> List[ActiveDaySummary]:
    return [_summarize_day(date, lines, model=model) for date, lines in active_days_messages.items()]


def save_group_chat_digest(
    data: Dict,
    out_dir: Optional[Path] = None,
    model: str = MODEL,
    **kwargs,
) -> Path:
    out_dir = out_dir or Path(constants.results_dir())
    out_dir.mkdir(parents=True, exist_ok=True)
    _, text = build_group_chat_digest(data, model=model, **kwargs)
    out_path = out_dir / "digest_ollama.txt"
    out_path.write_text(text, encoding="utf-8")
    return out_path


# ─────────────────────────────────────────────────────────────────────────────
# Text renderer
# ─────────────────────────────────────────────────────────────────────────────


def _render_digest_text(results: List[ThreadResult]) -> str:
    lines: List[str] = []
    for i, r in enumerate(results, 1):
        d = r.digest
        start = r.start.strftime("%Y-%m-%d %H:%M")
        end = r.end.strftime("%H:%M")

        lines.append(f"Wątek {i} ({start}–{end})")
        lines.append(f"Temat (słowa kluczowe): {', '.join(d.keywords) or 'brak wyraźnych słów kluczowych'}")
        lines.append(f"Uczestnicy: {', '.join(r.authors)}")
        lines.append(f"Liczba wiadomości: {len(r.thread)} | Wynik ważności: {d.importance_score:.2f}")
        lines.append(d.summary)
        lines.append("")

    return "\n".join(lines)
