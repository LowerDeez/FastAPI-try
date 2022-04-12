from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class OAuthIntegration:
    name: str
    overwrite: bool
    kwargs: Dict[str, Any]
