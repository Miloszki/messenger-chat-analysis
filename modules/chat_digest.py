# modules/chat_digest.py
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .constants import MESSENGER_BUILTIN_MESSAGES, MONTHNAME, STOPWORDS_POLISH


# ----------------------------
# Config (tunable knobs)
# ----------------------------
@dataclass
class DigestConfig:
    # Thread segmentation
    time_gap_min: int = 60  # gap (minutes) => new thread
    min_thread_messages: int = 8  # ignore smaller threads
    max_threads: int = 8  # how many threads to output

    # Topic keywords
    top_keywords: int = 6
    min_word_len: int = 3

    # NEW: topic-related sentences (ranked)
    topic_sentences_max: int = 6
    topic_sentence_min_chars: int = 20

    # Stance detection (very simple rules)
    stance_phrases_pro: Tuple[str, ...] = (
        "jestem za",
        "popieram",
        "zgadzam się",
        "zgadzam sie",
        "masz rację",
        "masz racje",
        "dokładnie",
        "dokladnie",
        "racja",
    )
    stance_phrases_con: Tuple[str, ...] = (
        "jestem przeciw",
        "nie popieram",
        "nie zgadzam się",
        "nie zgadzam sie",
        "to bez sensu",
        "bzdura",
    )

    # Conflict / insults (expand for your group)
    insult_words: Tuple[str, ...] = (
        "idiota",
        "idiotka",
        "debil",
        "debilka",
        "kretyn",
        "głupek",
        "glupeк",
        "głupia",
        "głupi",
        "spierdalaj",
        "pierdol",
        "jeb",
        "kurwa",
    )

    # Anecdotes (1st person + event-ish words)
    anecdote_markers: Tuple[str, ...] = (
        "ugryz",
        "pogryz",
        "skalecz",
        "złama",
        "zlama",
        "wypadek",
        "uderz",
        "krew",
        "rana",
        "szpital",
        "boli",
        "bolało",
        "bolalo",
        "miałem",
        "mialem",
        "miałam",
        "mialam",
        "mnie",
        "mi",
        "ja ",
        "moje",
        "moja",
    )

    # Output / evidence
    include_evidence_snippets: bool = True
    evidence_max_len: int = 160


# ----------------------------
# Helpers
# ----------------------------
_WORD_RE = re.compile(r"[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż]+")
_URL_RE = re.compile(r"(https?://\S+)")
_WS_RE = re.compile(r"\s+")


def _clean_text(text: str) -> str:
    text = text or ""
    text = _URL_RE.sub("", text)
    text = text.replace("\u200b", " ")
    text = _WS_RE.sub(" ", text).strip()
    return text


def _clip(s: str, max_len: int) -> str:
    s = (s or "").strip()
    if len(s) <= max_len:
        return s
    return s[: max_len - 1].rstrip() + "…"


def _is_builtin_message(content: str) -> bool:
    if not content:
        return False
    low = content.lower()
    return any(k.lower() in low for k in MESSENGER_BUILTIN_MESSAGES)


def _iter_content_messages(data: Dict) -> List[Dict]:
    """
    Returns sorted list: {ts, author, text} only for real messages (filters system/builtin).
    """
    msgs = sorted(data.get("messages", []), key=lambda m: m.get("timestamp_ms", 0))
    out = []
    for m in msgs:
        txt = m.get("content")
        if not txt:
            continue
        txt = _clean_text(txt)
        if not txt:
            continue
        if _is_builtin_message(txt):
            continue
        out.append(
            {
                "ts": m.get("timestamp_ms", 0),
                "author": m.get("sender_name", "Unknown"),
                "text": txt,
            }
        )
    return out


def _build_name_variants(data: Dict) -> Dict[str, List[str]]:
    """
    Map: participant full name -> possible mention variants in text (first/last/full).
    Used to guess "Y -> Z" in conflicts/stances.
    """
    variants: Dict[str, List[str]] = {}
    for p in data.get("participants", []):
        name = (p.get("name") or "").strip()
        if not name:
            continue
        parts = [x for x in name.split() if x]
        v = {name}
        if parts:
            v.add(parts[0])
            v.add(parts[-1])
            if len(parts) >= 2:
                v.add(parts[0] + " " + parts[-1])
        variants[name] = list({x.strip() for x in v if len(x.strip()) >= 2})
    return variants


def _mention_target(
    text_lower: str,
    name_variants: Dict[str, List[str]],
    exclude_author: Optional[str] = None,
) -> Optional[str]:
    for person, vars_ in name_variants.items():
        if exclude_author and person == exclude_author:
            continue
        for v in sorted(vars_, key=len, reverse=True):
            v_low = v.lower()
            if len(v_low) <= 3:
                if re.search(rf"\b{re.escape(v_low)}\b", text_lower):
                    return person
            else:
                if v_low in text_lower:
                    return person
    return None


def _segment_threads(messages: List[Dict], time_gap_min: int) -> List[List[Dict]]:
    if not messages:
        return []
    threads: List[List[Dict]] = []
    cur = [messages[0]]
    for prev, nxt in zip(messages, messages[1:]):
        gap_min = (nxt["ts"] - prev["ts"]) / 60000.0
        if gap_min >= time_gap_min:
            threads.append(cur)
            cur = [nxt]
        else:
            cur.append(nxt)
    if cur:
        threads.append(cur)
    return threads


# ----------------------------
# Stemming (supports pystempel variants)
# ----------------------------
def _make_stemmer():
    try:
        from pystempel import StempelStemmer

        return ("stempel", StempelStemmer.polimorf())
    except Exception:
        try:
            from pystempel import Stemmer

            return ("callable", Stemmer.polimorf())
        except Exception:
            return ("none", None)


def _stem(stemmer_kind: str, stemmer_obj, word: str) -> str:
    if not word:
        return word
    if stemmer_kind == "stempel":
        try:
            out = stemmer_obj.stem(word)
            return out if out else word
        except Exception:
            return word
    if stemmer_kind == "callable":
        # sometimes callable, sometimes .stem()
        try:
            out = stemmer_obj(word)
            return out if out else word
        except Exception:
            try:
                out = stemmer_obj.stem(word)
                return out if out else word
            except Exception:
                return word
    return word


# ----------------------------
# Sentence splitting (PL)
# ----------------------------
_SENT_SPLIT_RE = re.compile(r"(?<=[\.\?\!…])\s+|\n+")


def split_sentences_pl(text: str) -> List[str]:
    """
    Best-effort: try NLTK Punkt (polish), fallback to regex.
    """
    text = (text or "").strip()
    if not text:
        return []
    try:
        from nltk.tokenize import sent_tokenize

        sents = sent_tokenize(text, language="polish")
        sents = [s.strip() for s in sents if s and s.strip()]
        return sents if sents else [text]
    except Exception:
        sents = [s.strip() for s in _SENT_SPLIT_RE.split(text) if s and s.strip()]
        return sents if sents else [text]


# ----------------------------
# Topic keywords + NEW: topic sentences
# ----------------------------
def _keywords_for_thread(
    thread: List[Dict], cfg: DigestConfig, stemmer_kind: str, stemmer_obj
) -> List[str]:
    freq: Dict[str, int] = {}
    for m in thread:
        for w in _WORD_RE.findall(m["text"]):
            w_low = w.lower()
            if len(w_low) < cfg.min_word_len:
                continue
            if w_low in STOPWORDS_POLISH:
                continue
            s = _stem(stemmer_kind, stemmer_obj, w_low)
            if s in STOPWORDS_POLISH:
                continue
            freq[s] = freq.get(s, 0) + 1
    return [
        w
        for w, _ in sorted(freq.items(), key=lambda x: x[1], reverse=True)[
            : cfg.top_keywords
        ]
    ]


def _topic_sentence_candidates(
    thread: List[Dict],
    keywords: List[str],
    cfg: DigestConfig,
    stemmer_kind: str,
    stemmer_obj,
) -> List[Dict]:
    """
    Builds sentence candidates with scores based on keyword overlap.
    Each candidate: {author, sentence, matched_keywords, score}
    """
    candidates: List[Dict] = []
    kw_set = set(keywords)

    for msg in thread:
        author = msg["author"]
        for sent in split_sentences_pl(msg["text"]):
            sent = sent.strip()
            if len(sent) < cfg.topic_sentence_min_chars:
                continue

            stems = set()
            for w in _WORD_RE.findall(sent):
                w_low = w.lower()
                if len(w_low) < cfg.min_word_len:
                    continue
                if w_low in STOPWORDS_POLISH:
                    continue
                stems.add(_stem(stemmer_kind, stemmer_obj, w_low))

            matched = sorted([kw for kw in kw_set if kw in stems])
            if not matched:
                continue

            # scoring: keyword coverage dominates, slight preference for informative length
            score = (3.0 * len(matched)) + min(len(sent) / 120.0, 1.0)
            candidates.append(
                {
                    "author": author,
                    "sentence": sent,
                    "matched_keywords": matched,
                    "score": score,
                }
            )

    # rank high to low
    candidates.sort(
        key=lambda x: (x["score"], len(x["matched_keywords"]), len(x["sentence"])),
        reverse=True,
    )
    return candidates


def _select_topic_sentences_and_filter_keywords(
    thread: List[Dict],
    keywords: List[str],
    cfg: DigestConfig,
    stemmer_kind: str,
    stemmer_obj,
) -> Tuple[List[str], List[Dict]]:
    """
    NEW requirement:
    - If a keyword appears in thread keywords, we ensure at least one selected sentence contains it.
    - If a keyword doesn't appear in ANY sentence candidate, we drop it (so requirement remains true).
    Returns: (filtered_keywords, selected_topic_sentences)
    """
    candidates = _topic_sentence_candidates(
        thread, keywords, cfg, stemmer_kind, stemmer_obj
    )

    # Build coverage map: keyword -> best candidate containing it
    best_for_kw: Dict[str, Dict] = {}
    for cand in candidates:
        for kw in cand["matched_keywords"]:
            if kw not in best_for_kw:
                best_for_kw[kw] = cand

    filtered_keywords = [kw for kw in keywords if kw in best_for_kw]

    # Select sentences ensuring coverage (one per kw if possible)
    selected: List[Dict] = []
    seen_sentences = set()

    for kw in filtered_keywords:
        cand = best_for_kw[kw]
        key = (cand["author"], cand["sentence"])
        if key not in seen_sentences:
            selected.append(cand)
            seen_sentences.add(key)

    # Fill remaining slots with top-ranked candidates (dedup)
    for cand in candidates:
        if len(selected) >= cfg.topic_sentences_max:
            break
        key = (cand["author"], cand["sentence"])
        if key in seen_sentences:
            continue
        selected.append(cand)
        seen_sentences.add(key)

    return filtered_keywords, selected


# ----------------------------
# Stances / conflicts / anecdotes
# ----------------------------
def _detect_stances(
    thread: List[Dict], cfg: DigestConfig, name_variants: Dict[str, List[str]]
) -> List[Dict]:
    stances = []
    for m in thread:
        t = m["text"].lower()
        author = m["author"]
        target = _mention_target(t, name_variants, exclude_author=author)

        pro = any(p in t for p in cfg.stance_phrases_pro)
        con = any(p in t for p in cfg.stance_phrases_con)
        if pro == con:
            continue

        stances.append(
            {
                "author": author,
                "polarity": "za" if pro else "przeciw",
                "target": target,
                "evidence": m["text"],
            }
        )
    return stances


def _detect_conflicts(
    thread: List[Dict], cfg: DigestConfig, name_variants: Dict[str, List[str]]
) -> List[Dict]:
    conflicts = []
    for m in thread:
        t_low = m["text"].lower()
        if not any(bad in t_low for bad in cfg.insult_words):
            continue
        author = m["author"]
        target = _mention_target(t_low, name_variants, exclude_author=author)
        conflicts.append(
            {"from": author, "to": target, "type": "insult", "evidence": m["text"]}
        )
    return conflicts


def _detect_anecdotes(thread: List[Dict], cfg: DigestConfig) -> List[Dict]:
    anecdotes = []
    for m in thread:
        t_low = m["text"].lower()
        if not any(mark in t_low for mark in cfg.anecdote_markers):
            continue
        if len(m["text"]) < 25:
            continue
        anecdotes.append({"author": m["author"], "evidence": m["text"]})
    return anecdotes


def _thread_score(
    thread: List[Dict],
    stances: List[Dict],
    conflicts: List[Dict],
    anecdotes: List[Dict],
    topic_sents: List[Dict],
) -> float:
    authors = {m["author"] for m in thread}
    return (
        1.0
        + 0.08 * len(thread)
        + 0.6 * len(authors)
        + 2.2 * len(conflicts)
        + 1.2 * len(stances)
        + 1.1 * len(anecdotes)
        + 0.8 * min(len(topic_sents), 6)
    )


# ----------------------------
# Public API
# ----------------------------
def build_group_chat_digest(data: Dict, cfg: Optional[DigestConfig] = None) -> str:
    cfg = cfg or DigestConfig()

    messages = _iter_content_messages(data)
    if not messages:
        return "Brak wiadomości tekstowych do streszczenia (po odfiltrowaniu systemowych wpisów)."

    name_variants = _build_name_variants(data)
    stemmer_kind, stemmer_obj = _make_stemmer()

    threads = _segment_threads(messages, cfg.time_gap_min)

    enriched = []
    for th in threads:
        if len(th) < cfg.min_thread_messages:
            continue

        keywords = _keywords_for_thread(th, cfg, stemmer_kind, stemmer_obj)

        # NEW: ensure keyword -> at least one topic sentence includes it
        keywords, topic_sentences = _select_topic_sentences_and_filter_keywords(
            th, keywords, cfg, stemmer_kind, stemmer_obj
        )

        stances = _detect_stances(th, cfg, name_variants)
        conflicts = _detect_conflicts(th, cfg, name_variants)
        anecdotes = _detect_anecdotes(th, cfg)

        score = _thread_score(th, stances, conflicts, anecdotes, topic_sentences)

        start_dt = datetime.fromtimestamp(th[0]["ts"] / 1000.0)
        end_dt = datetime.fromtimestamp(th[-1]["ts"] / 1000.0)

        enriched.append(
            {
                "thread": th,
                "score": score,
                "keywords": keywords,
                "topic_sentences": topic_sentences,
                "stances": stances,
                "conflicts": conflicts,
                "anecdotes": anecdotes,
                "start": start_dt,
                "end": end_dt,
            }
        )

    if not enriched:
        return (
            "Nie wykryto wystarczająco dużych wątków do narracyjnego streszczenia.\n"
            "Sugestia: zmniejsz min_thread_messages albo time_gap_min."
        )

    enriched.sort(key=lambda x: x["score"], reverse=True)
    top = enriched[: cfg.max_threads]

    lines: List[str] = []
    lines.append(f"DIGEST ROZMOWY — {MONTHNAME}")
    lines.append("=" * 60)
    lines.append(f"Wykryte wątki (top {len(top)}): {len(enriched)} łącznie\n")

    for i, item in enumerate(top, start=1):
        th = item["thread"]
        authors = sorted({m["author"] for m in th})
        start = item["start"].strftime("%Y-%m-%d %H:%M")
        end = item["end"].strftime("%H:%M")

        topic = (
            ", ".join(item["keywords"])
            if item["keywords"]
            else "brak wyraźnych słów kluczowych"
        )
        lines.append(f"Wątek {i} ({start}–{end})")
        lines.append(f"Temat (słowa kluczowe): {topic}")
        lines.append(f"Uczestnicy: {', '.join(authors)}")
        lines.append(
            f"Liczba wiadomości: {len(th)} | Wynik ważności: {item['score']:.2f}"
        )

        # NEW category: sentences related to topic (ranked)
        if item["topic_sentences"]:
            lines.append("Odnoszące się do tematu wątku (ranking):")
            for s in item["topic_sentences"][: cfg.topic_sentences_max]:
                if cfg.include_evidence_snippets:
                    lines.append(
                        f"- {s['author']}: „{_clip(s['sentence'], cfg.evidence_max_len)}”"
                    )
                else:
                    lines.append(f"- {s['author']}")

        # stance
        if item["stances"]:
            lines.append("Stanowiska / opowiedzenie się po stronie:")
            for s in item["stances"][:6]:
                tgt = f" wobec {s['target']}" if s.get("target") else ""
                if cfg.include_evidence_snippets:
                    lines.append(
                        f"- {s['author']} był/a **{s['polarity']}**{tgt}: „{_clip(s['evidence'], cfg.evidence_max_len)}”"
                    )
                else:
                    lines.append(f"- {s['author']} był/a **{s['polarity']}**{tgt}")

        # conflicts
        if item["conflicts"]:
            lines.append("Konflikty / przytyki:")
            for c in item["conflicts"][:6]:
                tgt = c["to"] if c.get("to") else "kogoś (niejednoznaczne)"
                if cfg.include_evidence_snippets:
                    lines.append(
                        f"- {c['from']} obraził/a {tgt}: „{_clip(c['evidence'], cfg.evidence_max_len)}”"
                    )
                else:
                    lines.append(f"- {c['from']} obraził/a {tgt}")

        # anecdotes
        if item["anecdotes"]:
            lines.append("Anegdoty / historie osobiste:")
            for a in item["anecdotes"][:6]:
                if cfg.include_evidence_snippets:
                    lines.append(
                        f"- {a['author']} opowiadał/a: „{_clip(a['evidence'], cfg.evidence_max_len)}”"
                    )
                else:
                    lines.append(f"- {a['author']} opowiadał/a anegdotę")

        # fallback
        if (
            not item["stances"]
            and not item["conflicts"]
            and not item["anecdotes"]
            and not item["topic_sentences"]
        ):
            samples = th[-2:] if len(th) >= 2 else th
            lines.append("Przykładowe wypowiedzi:")
            for m in samples:
                lines.append(
                    f"- {m['author']}: „{_clip(m['text'], cfg.evidence_max_len)}”"
                )

        lines.append("-" * 60)

    lines.append("\nDOSTRAJANIE")
    lines.append(
        f"- Segmentacja: time_gap_min={cfg.time_gap_min}, min_thread_messages={cfg.min_thread_messages}"
    )
    lines.append(
        "- Konflikty: rozszerz cfg.insult_words (i dodaj wyjątki, jeśli to 'żarty')."
    )
    lines.append(
        "- Temat: zwiększ top_keywords / topic_sentences_max albo zmień min_word_len."
    )
    lines.append(
        "- Jeśli keywordów ubywa: to znaczy, że nie wystąpiły w żadnym zdaniu-kandydacie (zgodnie z wymaganiem)."
    )

    return "\n".join(lines)


def save_group_chat_digest(
    data: Dict, out_dir: Optional[Path] = None, cfg: Optional[DigestConfig] = None
) -> Path:
    out_dir = out_dir or Path(f"./results{MONTHNAME}")
    out_dir.mkdir(parents=True, exist_ok=True)

    digest = build_group_chat_digest(data, cfg=cfg)
    out_path = out_dir / f"{MONTHNAME}_GROUP_CHAT_DIGEST.txt"
    out_path.write_text(digest, encoding="utf-8")
    return out_path
