import math
from collections import Counter
from datetime import datetime


def split_turns(messages, gap_minutes):
    """Group messages into turns: one sender's consecutive messages, each under `gap_minutes` after the previous."""
    gap_ms = gap_minutes * 60 * 1000
    turns = []
    for msg in sorted((m for m in messages if not m.is_builtin), key=lambda m: m.timestamp_ms):
        last = turns[-1][-1] if turns else None
        if last and last.sender == msg.sender and msg.timestamp_ms - last.timestamp_ms < gap_ms:
            turns[-1].append(msg)
        else:
            turns.append([msg])
    return turns


def _received(msg):
    """Reactions on a message, not counting the sender reacting to themselves."""
    if msg.reactors:
        return sum(1 for actor in msg.reactors if actor != msg.sender)
    return msg.num_reactions


def get_reaction_scores(messages, gap_minutes, prior_turns):
    """Per-sender reactions per turn, smoothed toward the group mean; sorted best first.

    Counting per turn instead of per message means splitting one thought into several
    messages doesn't dilute the score; smoothing keeps members with few turns from
    topping the ranking on luck.
    """
    stats = {}
    for turn in split_turns(messages, gap_minutes):
        s = stats.setdefault(turn[0].sender, {"message_count": 0, "turn_count": 0, "reactions_received": 0})
        s["turn_count"] += 1
        s["message_count"] += len(turn)
        s["reactions_received"] += sum(_received(m) for m in turn)

    total_turns = sum(s["turn_count"] for s in stats.values())
    if not total_turns:
        return [], 0.0
    group_mean = sum(s["reactions_received"] for s in stats.values()) / total_turns

    rows = []
    for name, s in stats.items():
        score = (s["reactions_received"] + prior_turns * group_mean) / (s["turn_count"] + prior_turns)
        rows.append(
            {
                "name": name,
                **s,
                "reactions_per_message": s["reactions_received"] / s["message_count"],
                "reactions_per_turn": s["reactions_received"] / s["turn_count"],
                "reaction_score": score,
                "relative_score": score / group_mean if group_mean else None,
            }
        )

    rows.sort(key=lambda r: r["reaction_score"], reverse=True)
    max_score = rows[0]["reaction_score"]
    for row in rows:
        row["marker"] = row["reaction_score"] / max_score if max_score else 0.0
    return rows, group_mean


def get_ratios(messages, member_count, min_share):
    """Text messages reacted to by at least `min_share` of members (sender's own reaction excluded)."""
    min_reactors = max(1, math.ceil(min_share * member_count))
    ratios = []
    for msg in messages:
        if msg.is_builtin or not msg.content or msg.photos or msg.videos:
            continue
        reactors = {actor for actor in msg.reactors if actor != msg.sender}
        if len(reactors) < min_reactors:
            continue
        reactions = Counter(
            emoji for actor, emoji in zip(msg.reactors, msg.reactions) if actor != msg.sender
        )
        ratios.append(
            {
                "sender": msg.sender,
                "text": msg.content,
                "sent_at": datetime.fromtimestamp(msg.timestamp_ms / 1000).isoformat(timespec="seconds"),
                "date": msg.date,
                "reactor_count": len(reactors),
                "reactor_share": len(reactors) / member_count if member_count else None,
                "reactions": dict(reactions.most_common()),
            }
        )
    ratios.sort(key=lambda r: (r["reactor_count"], r["sent_at"]), reverse=True)
    return ratios, min_reactors
