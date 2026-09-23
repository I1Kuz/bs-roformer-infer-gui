from dataclasses import dataclass
from enum import StrEnum
from typing import final


class AppLanguage(StrEnum):
    EN = "en"
    UK = "uk"


@final
@dataclass(frozen=True, slots=True)
class LoadingTranslations:
    initializing: str
    checking_env: str
    starting_worker: str
    detecting_hw: str
    fetching_registry: str
    worker_start_failed: str


@final
@dataclass(frozen=True, slots=True)
class SetupTranslations:
    install_failed: str
    error_prefix: str
    retry: str


@final
@dataclass(frozen=True, slots=True)
class FoldersTranslations:
    frame_title: str
    input_folder: str
    output_folder: str
    browse: str
    subfolder_per_track: str


@final
@dataclass(frozen=True, slots=True)
class ModelTranslations:
    frame_title: str
    change_model: str
    no_model: str


@final
@dataclass(frozen=True, slots=True)
class SettingsTranslations:
    frame_title: str
    device: str
    vram_limit: str
    chunk_size: str
    export_format: str
    overlap: str
    speed: str
    quality: str
    help: str
    language: str


@final
@dataclass(frozen=True, slots=True)
class QueueTranslations:
    frame_title: str
    col_file: str
    col_model: str
    col_status: str
    col_progress: str
    col_actions: str
    btn_add_files: str
    btn_add_folder: str
    btn_clear_finished: str
    action_open_file: str
    action_open_folder: str
    action_prioritize: str
    action_remove: str
    start_transform: str
    stop: str
    ready: str
    gpu_detecting: str
    gpu_prefix: str
    no_gpu: str


@final
@dataclass(frozen=True, slots=True)
class StatusTranslations:
    pending: str
    processing: str
    downloading_model: str
    downloading: str
    transforming: str
    starting: str
    finished: str
    cancelled: str
    failed: str


@final
@dataclass(frozen=True, slots=True)
class ModelDialogTranslations:
    title: str
    col_installed: str
    col_name: str
    col_category: str
    installed_yes: str
    installed_no: str
    btn_select: str
    btn_cancel: str


@final
@dataclass(frozen=True, slots=True)
class HelpDialogTranslations:
    title: str
    btn_close: str
    content: str


@final
@dataclass(frozen=True, slots=True)
class AppTranslations:
    app_title: str
    loading: LoadingTranslations
    setup: SetupTranslations
    folders: FoldersTranslations
    model: ModelTranslations
    settings: SettingsTranslations
    queue: QueueTranslations
    status: StatusTranslations
    model_dialog: ModelDialogTranslations
    help_dialog: HelpDialogTranslations


# ---------------------------------------------------------------------------
# English translations
# ---------------------------------------------------------------------------

_EN_HELP_TEXT = """BS-RoFormer Infer Studio — Guide

VRAM & Hardware
• CUDA (NVIDIA): Recommended for best performance.
• CPU: Fallback mode if no compatible GPU is available.
• VRAM Limit: 0 means Auto. Set a value (in GB) to limit memory allocation.

Chunk Size
• Auto: Recommended for most systems. Chooses optimal chunk size based on GPU VRAM.
• Small (~3GB VRAM): Use for GPUs with 4GB VRAM or less to prevent Out-Of-Memory errors.
• Medium (~4GB VRAM): Balanced quality and memory usage.
• Big (~6GB VRAM): Native chunk size for models with high quality.
• Huge (~8+ GB VRAM): Maximum context window for cards with 8GB+ VRAM.

Overlap
• Controls overlap between consecutive audio chunks (2 to 8).
• Lower values (2-3): Faster processing.
• Higher values (4-8): Eliminates seams and artifacts between chunks, higher quality.

Export Formats
• WAV 32-bit (Float): Lossless, highest dynamic range.
• WAV 24-bit / 16-bit: Standard uncompressed PCM formats.
• MP3 320kbps: Compact compressed audio.
• FLAC: Lossless compressed audio.
"""

_UK_HELP_TEXT = """BS-RoFormer Infer Studio — Довідка

Відеопам'ять (VRAM) та обладнання
• CUDA (NVIDIA): Рекомендується для максимальної швидкості.
• CPU: Резервний режим, якщо сумісний GPU відсутній.
• Ліміт VRAM: 0 означає Авто. Вкажіть число (в ГБ) для обмеження виділення пам'яті.

Розмір чанка (Chunk Size)
• Auto: Рекомендовано для більшості систем. Обирає розмір на основі пам'яті GPU.
• Small (~3GB VRAM): Для відеокарт з 4GB VRAM або менше для запобігання помилкам Out-Of-Memory.
• Medium (~4GB VRAM): Збалансоване співвідношення якості та споживання пам'яті.
• Big (~6GB VRAM): Стандартний розмір чанка для високої якості.
• Huge (~8+ GB VRAM): Максимальне контекстне вікно для відеокарт від 8GB VRAM.

Перекриття (Overlap)
• Керує ступенем накладання сусідніх чанків аудіо (від 2 до 8).
• Менші значення (2-3): Швидша обробка.
• Більші значення (4-8): Усуває артефакти та стики між чанками, найкраща якість.

Формати експорту
• WAV 32-bit (Float): Без втрат, максимальний динамічний діапазон.
• WAV 24-bit / 16-bit: Стандартні формати PCM без стиснення.
• MP3 320kbps: Компактне стиснене аудіо з бітрейтом 320 кбіт/с.
• FLAC: Стиснення без втрат якості.
"""

_EN_TRANSLATIONS = AppTranslations(
    app_title="(BS-RoFormer-Infer) Studio",
    loading=LoadingTranslations(
        initializing="Initializing...",
        checking_env="Checking environment and dependencies...",
        starting_worker="Starting inference worker process...",
        detecting_hw="Detecting hardware capabilities...",
        fetching_registry="Fetching model registry...",
        worker_start_failed="Failed to start background worker process.",
    ),
    setup=SetupTranslations(
        install_failed="Installation Failed",
        error_prefix="Error: ",
        retry="Retry",
    ),
    folders=FoldersTranslations(
        frame_title="Folders",
        input_folder="Input Folder:",
        output_folder="Output Folder:",
        browse="Browse...",
        subfolder_per_track="Create a subfolder per track",
    ),
    model=ModelTranslations(
        frame_title="Model",
        change_model="Change Model...",
        no_model="No model selected",
    ),
    settings=SettingsTranslations(
        frame_title="Advanced Settings",
        device="Device:",
        vram_limit="VRAM Limit (GB, 0=auto):",
        chunk_size="Chunk Size:",
        export_format="Export Format:",
        overlap="Overlap:",
        speed="Speed",
        quality="Quality",
        help="Help",
        language="Language:",
    ),
    queue=QueueTranslations(
        frame_title="Queue",
        col_file="File",
        col_model="Model",
        col_status="Status",
        col_progress="Progress",
        col_actions="Actions",
        btn_add_files="Add Files...",
        btn_add_folder="Add Folder...",
        btn_clear_finished="Clear Finished",
        action_open_file="Open File",
        action_open_folder="Open Folder",
        action_prioritize="Move to Top",
        action_remove="Remove",
        start_transform="Start Transform",
        stop="Stop",
        ready="Ready",
        gpu_detecting="GPU: Detecting...",
        gpu_prefix="GPU: ",
        no_gpu="No compatible GPU (CPU mode)",
    ),
    status=StatusTranslations(
        pending="Pending",
        processing="Processing",
        downloading_model="Downloading / Loading Model...",
        downloading="Downloading",
        transforming="Transforming",
        starting="Starting...",
        finished="Finished",
        cancelled="Cancelled",
        failed="Failed",
    ),
    model_dialog=ModelDialogTranslations(
        title="Select Model",
        col_installed="Installed",
        col_name="Name",
        col_category="Category",
        installed_yes="Yes",
        installed_no="No (auto-download)",
        btn_select="Select",
        btn_cancel="Cancel",
    ),
    help_dialog=HelpDialogTranslations(
        title="Help & Documentation",
        btn_close="Close",
        content=_EN_HELP_TEXT,
    ),
)

_UK_TRANSLATIONS = AppTranslations(
    app_title="(BS-RoFormer-Infer) Studio",
    loading=LoadingTranslations(
        initializing="Ініціалізація...",
        checking_env="Перевірка середовища та залежностей...",
        starting_worker="Запуск фонового процесу обробки...",
        detecting_hw="Визначення характеристик обладнання...",
        fetching_registry="Отримання списку моделей...",
        worker_start_failed="Не вдалося запустити фоновий процес обробки.",
    ),
    setup=SetupTranslations(
        install_failed="Помилка встановлення",
        error_prefix="Помилка: ",
        retry="Повторити",
    ),
    folders=FoldersTranslations(
        frame_title="Папки",
        input_folder="Вхідна папка:",
        output_folder="Папка збереження:",
        browse="Огляд...",
        subfolder_per_track="Створювати окрему папку для кожного треку",
    ),
    model=ModelTranslations(
        frame_title="Модель",
        change_model="Змінити модель...",
        no_model="Модель не обрано",
    ),
    settings=SettingsTranslations(
        frame_title="Розширені налаштування",
        device="Пристрій:",
        vram_limit="Ліміт VRAM (ГБ, 0=авто):",
        chunk_size="Розмір чанка:",
        export_format="Формат експорту:",
        overlap="Перекриття:",
        speed="Швидкість",
        quality="Якість",
        help="Довідка",
        language="Мова:",
    ),
    queue=QueueTranslations(
        frame_title="Черга",
        col_file="Файл",
        col_model="Модель",
        col_status="Статус",
        col_progress="Прогрес",
        col_actions="Дії",
        btn_add_files="Додати файли...",
        btn_add_folder="Додати папку...",
        btn_clear_finished="Очистити завершені",
        action_open_file="Відкрити файл",
        action_open_folder="Відкрити папку",
        action_prioritize="На початок черги",
        action_remove="Видалити",
        start_transform="Розпочати обробку",
        stop="Зупинити",
        ready="Готово",
        gpu_detecting="GPU: Визначення...",
        gpu_prefix="GPU: ",
        no_gpu="Сумісний GPU відсутній (режим CPU)",
    ),
    status=StatusTranslations(
        pending="В черзі",
        processing="Обробка",
        downloading_model="Завантаження моделі...",
        downloading="Завантаження",
        transforming="Обробка звуку",
        starting="Запуск...",
        finished="Завершено",
        cancelled="Скасовано",
        failed="Помилка",
    ),
    model_dialog=ModelDialogTranslations(
        title="Вибір моделі",
        col_installed="Встановлено",
        col_name="Назва",
        col_category="Категорія",
        installed_yes="Так",
        installed_no="Ні (автозавантаження)",
        btn_select="Обрати",
        btn_cancel="Скасувати",
    ),
    help_dialog=HelpDialogTranslations(
        title="Довідка та документація",
        btn_close="Закрити",
        content=_UK_HELP_TEXT,
    ),
)

_TRANSLATIONS: dict[str, AppTranslations] = {
    AppLanguage.EN: _EN_TRANSLATIONS,
    AppLanguage.UK: _UK_TRANSLATIONS,
}

LANGUAGE_DISPLAY_NAMES: dict[str, str] = {
    AppLanguage.EN: "English",
    AppLanguage.UK: "Українська",
}

_current_lang: str = AppLanguage.EN


def get_translations(lang: str | None = None) -> AppTranslations:
    """Returns the translation bundle for the given or current language."""
    target = lang or _current_lang
    return _TRANSLATIONS.get(target, _EN_TRANSLATIONS)


def set_current_language(lang: str) -> None:
    """Sets the active application language."""
    global _current_lang
    if lang in _TRANSLATIONS:
        _current_lang = lang


def get_current_language() -> str:
    """Returns the active application language code."""
    return _current_lang
