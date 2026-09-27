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
class FoldersTranslations:
    frame_title: str
    input_folder: str
    output_folder: str
    browse: str
    open_folder: str
    subfolder_per_track: str


@final
@dataclass(frozen=True, slots=True)
class ModelTranslations:
    frame_title: str
    change_model: str
    no_model: str
    category_prefix: str
    stems_prefix: str
    status_installed: str
    status_online: str


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
    btn_scan_folder: str
    btn_clear_finished: str
    btn_clear_all: str
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
    empty_title: str
    empty_hint: str
    summary_fmt: str


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
    tab_quickstart: str
    tab_settings: str
    tab_models: str
    quickstart_content: str
    settings_content: str
    models_content: str


@final
@dataclass(frozen=True, slots=True)
class AppTranslations:
    app_title: str
    loading: LoadingTranslations
    folders: FoldersTranslations
    model: ModelTranslations
    settings: SettingsTranslations
    queue: QueueTranslations
    status: StatusTranslations
    model_dialog: ModelDialogTranslations
    help_dialog: HelpDialogTranslations


# ---------------------------------------------------------------------------
# English text & translations
# ---------------------------------------------------------------------------

_EN_QUICKSTART = """Welcome to BS-RoFormer Infer Studio!

1. Select or Add Audio Files:
   • Click "Add Files..." to queue individual audio files (.mp3, .wav, .flac, .ogg, .m4a), OR
   • Select an Input Folder to automatically queue all audio files inside it.

2. Choose Target Model:
   • Click "Change Model..." to select from fine-tuned neural models.
   • Models are available for vocals, instrumental, karaoke, de-reverb, and multi-stem separation.

3. Pick Output Destination:
   • Set the Output Folder.
   • Optionally enable "Create a subfolder per track" to keep separated stems tidy.

4. Start Separation:
   • Click "Start Transform" to process the queue with GPU acceleration.
   • Monitor progress bars for each track in real time.
"""

_EN_SETTINGS_GUIDE = """VRAM & Hardware:
• CUDA (NVIDIA): Recommended for best performance. Automatically selected when available.
• CPU Mode: Fallback if no supported GPU is detected.
• VRAM Limit: 0 means Auto. Set a custom limit (in GB) if sharing GPU with other apps.

Chunk Size Preset:
• Auto: Recommended. Automatically balances quality and VRAM safety.
• Small (~3GB VRAM): For GPUs with 4GB VRAM or less to prevent Out-Of-Memory errors.
• Medium (~4GB VRAM): Balanced speed and memory usage.
• Big (~6GB VRAM): Standard high-quality model resolution.
• Huge (~8+ GB VRAM): Maximum receptive field context for GPUs with 8GB+ VRAM.

Overlap (Overlap Factor):
• 2x (Fastest): Quickest processing with standard chunk boundaries.
• 4x (Balanced): Smooth blend between consecutive chunks; eliminates seams.
• 6x - 8x (High Quality): Maximum cross-fade fidelity for studio mastering.
"""

_EN_MODELS_GUIDE = """Separation Categories:
• Vocals & Instrumental: Separates lead/backing vocals from music accompaniment.
• Karaoke: Specifically isolates lead vocals while retaining background harmonies.
• De-Reverb: Cleans room acoustics and dry signals from echo-heavy recordings.
• Multi-Stem: Splitting into 4-6 individual tracks (Vocals, Drums, Bass, Guitar, Piano, Other).

Audio Export Formats:
• WAV 32-bit (Float): Lossless, 32-bit floating point. Highest dynamic range, zero clipping.
• WAV 24-bit: Professional uncompressed audio standard.
• WAV 16-bit: CD-quality standard uncompressed PCM.
• FLAC: Lossless compression, smaller file size with identical sound quality.
• MP3 320kbps: Compact compressed audio suitable for general listening.
"""

_EN_TRANSLATIONS = AppTranslations(
    app_title="BS-RoFormer Infer Studio",
    loading=LoadingTranslations(
        initializing="Initializing...",
        checking_env="Checking environment and dependencies...",
        starting_worker="Starting inference worker process...",
        detecting_hw="Detecting hardware capabilities...",
        fetching_registry="Fetching model registry...",
        worker_start_failed="Failed to start background worker process.",
    ),
    folders=FoldersTranslations(
        frame_title="Folders",
        input_folder="Input Folder:",
        output_folder="Output Folder:",
        browse="Browse...",
        open_folder="Open in Explorer",
        subfolder_per_track="Create a subfolder per track",
    ),
    model=ModelTranslations(
        frame_title="Active Model",
        change_model="Change Model...",
        no_model="No model selected",
        category_prefix="Category:",
        stems_prefix="Stems:",
        status_installed="Installed",
        status_online="Auto-download",
    ),
    settings=SettingsTranslations(
        frame_title="Inference Settings",
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
        frame_title="Processing Queue",
        col_file="File",
        col_model="Model",
        col_status="Status",
        col_progress="Progress",
        col_actions="Actions",
        btn_add_files="Add Files...",
        btn_add_folder="Add Folder...",
        btn_scan_folder="Scan Folder",
        btn_clear_finished="Clear Finished",
        btn_clear_all="Clear All",
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
        empty_title="Queue is empty",
        empty_hint="Add audio files or scan input folder to start separation",
        summary_fmt="Total: {total}  |  Completed: {done}  |  Processing: {proc}  |  Pending: {pending}",
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
        tab_quickstart="Quick Start",
        tab_settings="Audio & Quality",
        tab_models="Models & Formats",
        quickstart_content=_EN_QUICKSTART,
        settings_content=_EN_SETTINGS_GUIDE,
        models_content=_EN_MODELS_GUIDE,
    ),
)


# ---------------------------------------------------------------------------
# Ukrainian text & translations
# ---------------------------------------------------------------------------

_UK_QUICKSTART = """Ласкаво просимо до BS-RoFormer Infer Studio!

1. Додайте аудіофайли:
   • Натисніть «Додати файли...» для вибору окремих треків (.mp3, .wav, .flac, .ogg, .m4a), АБО
   • Оберіть «Вхідну папку», щоб автоматично додати всі знайдені файли до черги.

2. Оберіть нейромережеву модель:
   • Натисніть «Змінити модель...», щоб обрати підготовлену модель.
   • Доступні моделі для виділення вокалу, інструменталу, караоке, де-реверберації та мультитреків.

3. Вкажіть папку для збереження:
   • Оберіть «Папку збереження».
   • За бажанням увімкніть «Створювати окрему папку для кожного треку».

4. Запустіть обробку:
   • Натисніть акцентну кнопку «Розпочати обробку».
   • Прогрес кожного треку відображатиметься в реальному часі.
"""

_UK_SETTINGS_GUIDE = """Відеопам'ять (VRAM) та обладнання:
• CUDA (NVIDIA): Рекомендується для максимальної швидкості (обирається автоматично).
• Режим CPU: Резервний режим, якщо сумісна відеокарта відсутня.
• Ліміт VRAM: 0 означає Авто. Вкажіть число (в ГБ) для обмеження виділення пам'яті.

Розмір чанка (Chunk Size):
• Auto: Рекомендовано. Автоматично підбирає розмір під відеопам'ять.
• Small (~3GB VRAM): Для відеокарт з 4GB VRAM або менше для запобігання помилкам пам'яті.
• Medium (~4GB VRAM): Збалансована швидкість та споживання пам'яті.
• Big (~6GB VRAM): Стандартний розмір чанка для високої якості.
• Huge (~8+ GB VRAM): Максимальне контекстне вікно для відеокарт від 8GB VRAM.

Перекриття (Overlap Factor):
• 2x (Швидко): Найшвидша обробка зі стандартним склеюванням чанків.
• 4x (Збалансовано): Плавне накладання сусідніх фрагментів, усуває стики.
• 6x - 8x (Висока якість): Максимальна точність крос-фейду для студійного зведення.
"""

_UK_MODELS_GUIDE = """Категорії розділення:
• Вокал та Інструментал: Відокремлює вокальну партію від інструментального супроводу.
• Караоке: Вирізає лід-вокал, зберігаючи бек-вокали та інструментал.
• Де-реверберація: Очищає сигнал від луни кімнати та зайвої реверберації.
• Мульти-трек: Розподіл на 4-6 окремих доріжок (вокал, бас, ударні, гітара, клавішні тощо).

Формати збереження:
• WAV 32-bit (Float): Без втрат, 32-бітний формат з плаваючою комою (максимальний динамічний діапазон).
• WAV 24-bit: Студійний нестиснений стандарт аудіо.
• WAV 16-bit: Стандартний нестиснений PCM-звук (якість Audio CD).
• FLAC: Стиснення без втрат якості (менший розмір файлу).
• MP3 320kbps: Компактне стиснене аудіо з бітрейтом 320 кбіт/с.
"""

_UK_TRANSLATIONS = AppTranslations(
    app_title="BS-RoFormer Infer Studio",
    loading=LoadingTranslations(
        initializing="Ініціалізація...",
        checking_env="Перевірка середовища та залежностей...",
        starting_worker="Запуск фонового процесу обробки...",
        detecting_hw="Визначення характеристик обладнання...",
        fetching_registry="Отримання списку моделей...",
        worker_start_failed="Не вдалося запустити фоновий процес обробки.",
    ),
    folders=FoldersTranslations(
        frame_title="Папки",
        input_folder="Вхідна папка:",
        output_folder="Папка збереження:",
        browse="Огляд...",
        open_folder="Відкрити в Провіднику",
        subfolder_per_track="Створювати окрему папку для кожного треку",
    ),
    model=ModelTranslations(
        frame_title="Активна модель",
        change_model="Змінити модель...",
        no_model="Модель не обрано",
        category_prefix="Категорія:",
        stems_prefix="Доріжки:",
        status_installed="Встановлено",
        status_online="Автозавантаження",
    ),
    settings=SettingsTranslations(
        frame_title="Параметри обробки",
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
        frame_title="Черга обробки",
        col_file="Файл",
        col_model="Модель",
        col_status="Статус",
        col_progress="Прогрес",
        col_actions="Дії",
        btn_add_files="Додати файли...",
        btn_add_folder="Додати папку...",
        btn_scan_folder="Сканувати папку",
        btn_clear_finished="Очистити завершені",
        btn_clear_all="Очистити все",
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
        empty_title="Черга порожня",
        empty_hint="Додайте аудіофайли або проскануйте вхідну папку для початку",
        summary_fmt="Усього: {total}  |  Завершено: {done}  |  В обробці: {proc}  |  В черзі: {pending}",
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
        tab_quickstart="Швидкий старт",
        tab_settings="Якість та звук",
        tab_models="Моделі та формати",
        quickstart_content=_UK_QUICKSTART,
        settings_content=_UK_SETTINGS_GUIDE,
        models_content=_UK_MODELS_GUIDE,
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
