from __future__ import annotations


def wrap_callable(owner, name, label=None, debug=None):
    """Wrap a callable with start/done/error debug logging."""
    try:
        original = getattr(owner, name)
    except Exception:
        return False
    if not callable(original):
        return False
    if getattr(original, "__fx_wrapped__", False):
        return False

    def wrapped(*args, **kwargs):
        tag = label or name
        if callable(debug):
            debug(f"{tag}:start")
        try:
            result = original(*args, **kwargs)
            if callable(debug):
                debug(f"{tag}:done")
            return result
        except Exception as exc:
            if callable(debug):
                debug(f"{tag}:error:{exc}")
            raise

    wrapped.__fx_wrapped__ = True
    try:
        setattr(owner, name, wrapped)
    except Exception:
        return False
    return True


def install_method_patch(owner, name, marker, wrapper_factory, debug=None):
    """Install an idempotent method patch and mark the wrapper."""
    try:
        original = getattr(owner, name)
    except Exception as exc:
        if callable(debug):
            debug(f"patch:{name}:missing:{exc}")
        return False
    if getattr(original, marker, False):
        return False
    patched = wrapper_factory(original)
    if not callable(patched):
        return False
    setattr(patched, marker, True)
    try:
        setattr(owner, name, patched)
    except Exception as exc:
        if callable(debug):
            debug(f"patch:{name}:install_error:{exc}")
        return False
    return True
