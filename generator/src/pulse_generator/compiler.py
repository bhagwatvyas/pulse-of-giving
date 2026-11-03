from datetime import date
import hashlib

from .domain import CommunityPulseSnapshot, MusicSpec, SupplyState


MOOD_BY_STATE = {
    SupplyState.STEADY: {"tempo": (66, 70), "harmony": "open major ninth voicings", "density": "spacious"},
    SupplyState.NEEDS_SUPPORT: {"tempo": (70, 74), "harmony": "warm suspended chords", "density": "gently flowing"},
    SupplyState.HIGH_NEED: {"tempo": (74, 78), "harmony": "resolved modal harmony", "density": "present but unhurried"},
}

NEGATIVE_PROMPT = (
    "vocals, lyrics, spoken words, alarm sounds, sirens, aggressive drums, "
    "harsh percussion, abrupt ending, dramatic drop, anxious or frightening mood"
)


def pacific_seed(snapshot_id: str, day: date) -> int:
    material = f"{snapshot_id}:{day.isoformat()}:v1".encode()
    return int.from_bytes(hashlib.sha256(material).digest()[:8], "big") & ((1 << 63) - 1)


def compile_music_spec(
    snapshot: CommunityPulseSnapshot,
    day: date,
    model_id: str = "self-hosted-model-pending-validation",
) -> MusicSpec:
    seed = pacific_seed(snapshot.snapshot_id, day)
    mood = MOOD_BY_STATE[snapshot.supply_state]
    low, high = mood["tempo"]
    tempo = low + seed % (high - low + 1)
    prompt = (
        f"35 second instrumental ambient composition, {tempo} BPM, {mood['harmony']}, "
        f"{mood['density']} texture, soft felt piano, warm analog pads, gentle acoustic detail, "
        "reassuring, restorative, subtle ending fade. No named artists or recognizable melodies."
    )
    return MusicSpec(
        snapshot_id=snapshot.snapshot_id,
        snapshot_status=snapshot.status,
        pacific_date=day,
        seed=seed,
        model_id=model_id,
        duration_seconds=35,
        tempo_bpm=tempo,
        prompt=prompt,
        negative_prompt=NEGATIVE_PROMPT,
        safety_constraints=[
            "instrumental only",
            "tempo must remain within 64-80 BPM",
            "calm mood is invariant across supply states",
            "music date must never be presented as data publication date",
        ],
    )
