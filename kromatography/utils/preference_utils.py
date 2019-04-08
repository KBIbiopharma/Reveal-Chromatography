""" Modifications of old preference versions which aren't done automatically.
"""

# -----------------------------------------------------------------------------
# Legacy preference format support
# -----------------------------------------------------------------------------


def translate_v1_to_v4(prefs):
    prefs = translate_v1_to_v2(prefs)
    prefs = translate_v2_to_v3(prefs)
    prefs = translate_v3_to_v4(prefs)
    return prefs


def translate_v1_to_v2(prefs):
    # Attribute removed:
    prefs.solver_preferences.remove_trait("executor")

    # Attributes moved from app to ui
    for attr in ["app_width", "app_height"]:
        val = getattr(prefs.app_preferences, attr)
        prefs.app_preferences.remove_trait(attr)
        prefs.ui_preferences.add_trait(attr, val)

    prefs.version = 2
    return prefs


def translate_v2_to_v3(prefs):
    # Attribute removed:
    prefs.optimizer_preferences.remove_trait("max_in_memory_group_size")
    prefs.version = 3
    return prefs


def translate_v3_to_v4(prefs):
    # Attribute moved from app preferences to new file preferences:
    app_prefs = prefs.app_preferences
    # Test because if no recent_files were stored, that attribute won't be set:
    if hasattr(app_prefs, "recent_files"):
        prefs.file_preferences.recent_files = app_prefs.recent_files
        app_prefs.remove_trait("recent_files")

    # Test because if no max_recent_files was stored, that attribute won't be
    # set:
    if hasattr(app_prefs, "max_recent_files"):
        prefs.file_preferences.max_recent_files = app_prefs.max_recent_files
        app_prefs.remove_trait("max_recent_files")

    prefs.version = 4
    return prefs


def translate_v2_to_v4(prefs):
    prefs = translate_v2_to_v3(prefs)
    prefs = translate_v3_to_v4(prefs)
    return prefs


PREF_ALTERATION_FUNCS = {
    1: translate_v1_to_v4,
    2: translate_v2_to_v4,
    3: translate_v3_to_v4,
}
