"""Fail-soft wraps so LTX encode never sees a non-÷32 spatial size."""

from __future__ import annotations

import sys
from typing import Any, Callable

from .align import center_crop_bcthw, snap_hw

WRAPPED_ATTR = "_ez_ltx_spatial_wrapped"

# LTXVImgToVideo.execute(cls, positive, negative, image, vae, width, height, ...)
_IMG2VIDEO_WIDTH_INDEX = 4
# EmptyLTXVLatentVideo.execute(cls, width, height, ...)
_EMPTY_WIDTH_INDEX = 0


def log(message: str) -> None:
    """Write a pack line to stderr.

    Args:
        message: Text after the ``[ez_ltx_spatial]`` prefix.

    Returns:
        None
    """
    print(f"[ez_ltx_spatial] {message}", file=sys.stderr)


def _is_wrapped(fn: Any) -> bool:
    raw = getattr(fn, "__func__", fn)
    return bool(getattr(raw, WRAPPED_ATTR, False))


def _mark_wrapped(fn: Callable[..., Any]) -> Callable[..., Any]:
    setattr(fn, WRAPPED_ATTR, True)
    return fn


def snap_width_height_in_call(
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    width_index: int,
) -> tuple[tuple[Any, ...], dict[str, Any]]:
    """Replace width/height in a node ``execute`` call with ÷32 snaps.

    Args:
        args: Positional args after ``cls``.
        kwargs: Keyword args.
        width_index: Index of ``width`` in ``args`` (height is next).

    Returns:
        Possibly-copied ``(args, kwargs)``. Missing width/height is a no-op.
    """
    args_list = list(args)
    kwargs_out = dict(kwargs)
    if "width" in kwargs_out:
        width = kwargs_out["width"]
    elif len(args_list) > width_index:
        width = args_list[width_index]
    else:
        return args, kwargs
    if "height" in kwargs_out:
        height = kwargs_out["height"]
    elif len(args_list) > width_index + 1:
        height = args_list[width_index + 1]
    else:
        return args, kwargs
    new_w, new_h = snap_hw(width, height)
    old_w, old_h = int(width), int(height)
    if (new_w, new_h) != (old_w, old_h):
        log(f"{old_w}x{old_h} -> {new_w}x{new_h} (LTX VAE requires spatial ÷32)")
    if "width" in kwargs_out:
        kwargs_out["width"] = new_w
    else:
        args_list[width_index] = new_w
    if "height" in kwargs_out:
        kwargs_out["height"] = new_h
    else:
        args_list[width_index + 1] = new_h
    return tuple(args_list), kwargs_out


def _wrap_classmethod_wh(cls: type, name: str, width_index: int) -> bool:
    orig = getattr(cls, name, None)
    if orig is None or _is_wrapped(orig):
        return False
    orig_fn = getattr(orig, "__func__", orig)

    def execute(inner_cls: type, *args: Any, **kwargs: Any) -> Any:
        args, kwargs = snap_width_height_in_call(args, kwargs, width_index)
        return orig_fn(inner_cls, *args, **kwargs)

    _mark_wrapped(execute)
    setattr(cls, name, classmethod(execute))
    if name == "execute" and getattr(cls, "generate", None) is not None:
        setattr(cls, "generate", classmethod(execute))
    return True


def _wrap_video_vae_encode(cls: type) -> bool:
    orig = getattr(cls, "encode", None)
    if orig is None or _is_wrapped(orig):
        return False
    orig_fn = getattr(orig, "__func__", orig)

    def encode(self: Any, x: Any, device: Any = None) -> Any:
        try:
            cropped = center_crop_bcthw(x)
        except Exception as exc:
            log(f"encode crop skipped: {exc}")
            return orig_fn(self, x, device)
        if cropped is not x:
            try:
                old_h, old_w = int(x.shape[-2]), int(x.shape[-1])
                new_h, new_w = int(cropped.shape[-2]), int(cropped.shape[-1])
                log(
                    f"encode {old_w}x{old_h} -> {new_w}x{new_h} "
                    "(LTX VAE requires spatial ÷32)"
                )
            except Exception:
                log("encode cropped to a ÷32 spatial window")
        return orig_fn(self, cropped, device)

    _mark_wrapped(encode)
    cls.encode = encode
    return True


def apply_patches() -> dict[str, bool]:
    """Wrap LTX nodes and VideoVAE.encode when Comfy modules are importable.

    Returns:
        Map of target name to whether this call installed a new wrap.
    """
    results = {
        "LTXVImgToVideo": False,
        "EmptyLTXVLatentVideo": False,
        "VideoVAE": False,
    }
    try:
        from comfy_extras.nodes_lt import EmptyLTXVLatentVideo, LTXVImgToVideo
    except Exception as exc:
        log(f"LTX nodes not wrapped ({exc})")
    else:
        results["LTXVImgToVideo"] = _wrap_classmethod_wh(
            LTXVImgToVideo, "execute", _IMG2VIDEO_WIDTH_INDEX
        )
        results["EmptyLTXVLatentVideo"] = _wrap_classmethod_wh(
            EmptyLTXVLatentVideo, "execute", _EMPTY_WIDTH_INDEX
        )
    try:
        from comfy.ldm.lightricks.vae.causal_video_autoencoder import VideoVAE
    except Exception as exc:
        log(f"VideoVAE.encode not wrapped ({exc})")
    else:
        results["VideoVAE"] = _wrap_video_vae_encode(VideoVAE)
    return results
