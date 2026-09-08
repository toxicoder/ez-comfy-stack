"""Rights attestation helpers for the dub lane."""

from __future__ import annotations


class RightsError(ValueError):
    """Queue refused because the operator did not attest rights."""


def as_bool(value: object) -> bool:
    """Coerce widget values to bool.

    Arguments:
        value: Comfy BOOLEAN widget or stringy truthy.
    Returns:
        True only for true/1/yes/on.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False


def require_rights(have_rights: object) -> None:
    """Refuse cloning unless the operator attested rights.

    Arguments:
        have_rights: App widget value.
    Raises:
        RightsError: when the attestation is missing or false.
    """
    if as_bool(have_rights):
        return
    raise RightsError(
        "I have rights is off. This lane clones recorded speakers. Queue "
        "only when you own the recording or have speaker consent and a "
        "license to translate it."
    )
