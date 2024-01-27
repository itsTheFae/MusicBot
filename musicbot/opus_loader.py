from discord import opus


def load_opus_lib() -> None:
    if opus.is_loaded():
        return

    try:
        opus._load_default()  # pylint: disable=protected-access
        return
    except OSError:
        pass

    raise RuntimeError("Could not load an opus lib.")
