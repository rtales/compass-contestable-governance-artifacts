from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ContestabilityScorecard:
    replayable: bool
    has_policy_hash: bool
    has_dataset_manifest: bool
    packet_complete: bool

    def score(self) -> int:
        return int(self.replayable) + int(self.has_policy_hash) + int(self.has_dataset_manifest) + int(self.packet_complete)

    def to_dict(self) -> dict:
        return {
            "replayable": self.replayable,
            "has_policy_hash": self.has_policy_hash,
            "has_dataset_manifest": self.has_dataset_manifest,
            "packet_complete": self.packet_complete,
            "score": self.score(),
            "max_score": 4,
        }
