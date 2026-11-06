"""Source-pinned JSON-to-spawn adapter for floor 00; not a playable runtime.

The source metadata is a committed provenance claim, not a replacement for
checking FFDec exports against the original SWF in the audit workflow.
"""
from core.initial_spawn_probe import plan_initial_floor_spawn
from core.original_floor_json import load_original_floor_json

EXPECTED_ACTIONSCRIPT_SHA256 = '2372dc16f71b6ede1110b61101b47ff11dd529803fc4077accd075381bffe97c'
EXPECTED_RENDERER_SHA256 = '0de19a0338cd966446acb4fd2acb82f82cf77992c8839356e17afc8f3085d034'


def plan_committed_floor_00_spawn(json_text: str) -> dict:
    """Fail closed on source drift, floor ID drift, and invalid tile data."""
    payload = load_original_floor_json(json_text)
    if not isinstance(payload, dict) or payload.get('schema_version') != 1:
        raise ValueError('invalid original floor schema version')
    source = payload.get('source')
    if not isinstance(source, dict) or (
        source.get('actionscript_sha256') != EXPECTED_ACTIONSCRIPT_SHA256 or
        source.get('renderer_actionscript_sha256') != EXPECTED_RENDERER_SHA256
    ):
        raise ValueError('original ActionScript source pin mismatch')
    floors = payload.get('floors')
    if not isinstance(floors, dict) or '00' not in floors:
        raise ValueError('missing zero-padded original floor 00')
    return plan_initial_floor_spawn(floors['00'])
