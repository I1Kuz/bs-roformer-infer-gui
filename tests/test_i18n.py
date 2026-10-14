import dataclasses
import re
from typing import Any

from app.core.i18n import (
    _EN_TRANSLATIONS,
    _UK_TRANSLATIONS,
    LANGUAGE_DISPLAY_NAMES,
    AppLanguage,
    get_current_language,
    get_translations,
    set_current_language,
)


def _extract_placeholders(text: str) -> set[str]:
    return set(re.findall(r"\{([a-zA-Z0-9_]+)\}", text))


def _compare_dataclass_fields(en_obj: Any, uk_obj: Any, path: str = "") -> None:
    assert dataclasses.is_dataclass(en_obj), f"{path} is not a dataclass"
    assert dataclasses.is_dataclass(uk_obj), f"{path} is not a dataclass"

    en_fields = {f.name for f in dataclasses.fields(en_obj)}
    uk_fields = {f.name for f in dataclasses.fields(uk_obj)}
    assert en_fields == uk_fields, f"Field mismatch at {path}: {en_fields ^ uk_fields}"

    for f_name in en_fields:
        en_val = getattr(en_obj, f_name)
        uk_val = getattr(uk_obj, f_name)
        subpath = f"{path}.{f_name}" if path else f_name

        if dataclasses.is_dataclass(en_val):
            _compare_dataclass_fields(en_val, uk_val, subpath)
        elif isinstance(en_val, str):
            assert isinstance(uk_val, str), f"Type mismatch at {subpath}: expected str, got {type(uk_val)}"
            assert en_val.strip(), f"Empty string in EN translation at {subpath}"
            assert uk_val.strip(), f"Empty string in UK translation at {subpath}"

            en_placeholders = _extract_placeholders(en_val)
            uk_placeholders = _extract_placeholders(uk_val)
            assert en_placeholders == uk_placeholders, (
                f"Placeholder mismatch at {subpath}: EN has {en_placeholders}, UK has {uk_placeholders}"
            )


def test_translation_structures_and_placeholders() -> None:
    _compare_dataclass_fields(_EN_TRANSLATIONS, _UK_TRANSLATIONS)


def test_language_display_names() -> None:
    for lang in AppLanguage:
        assert lang.value in LANGUAGE_DISPLAY_NAMES
        assert bool(LANGUAGE_DISPLAY_NAMES[lang.value])


def test_language_switching() -> None:
    initial_lang = get_current_language()
    try:
        set_current_language(AppLanguage.UK)
        assert get_current_language() == AppLanguage.UK
        trans_uk = get_translations()
        assert trans_uk is _UK_TRANSLATIONS

        set_current_language(AppLanguage.EN)
        assert get_current_language() == AppLanguage.EN
        trans_en = get_translations()
        assert trans_en is _EN_TRANSLATIONS

        # Invalid language code falls back to English
        fallback = get_translations("non_existent_lang")
        assert fallback is _EN_TRANSLATIONS
    finally:
        set_current_language(initial_lang)
