from __future__ import annotations

import platform
import sys
from dataclasses import dataclass
from importlib.metadata import distributions
from typing import Dict


@dataclass(frozen=True)
class EnvInfo:
    python: str
    platform: str
    packages: Dict[str, str]

    def to_dict(self) -> dict:
        return {"python": self.python, "platform": self.platform, "packages": self.packages}


def collect_env_info() -> EnvInfo:
    pkgs = {}
    for d in distributions():
        name = d.metadata["Name"]
        ver = d.version
        pkgs[name] = ver
    return EnvInfo(
        python=sys.version.replace("\n", " "),
        platform=platform.platform(),
        packages=dict(sorted(pkgs.items(), key=lambda x: x[0].lower())),
    )
