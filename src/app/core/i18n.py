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
    add_files: str
    rescan: str
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
    action_reveal_input: str
    action_open_output: str
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
    err_no_output_folder: str
    file_filter_audio: str
    select_files_title: str


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
    subtitle: str
    btn_close: str
    tab_quickstart: str
    tab_settings: str
    tab_models: str
    tab_about: str
    quickstart_content: str
    settings_content: str
    models_content: str
    about_content: str


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
High-performance desktop workstation for AI audio source separation.

1. Adding Audio Files:
   • Add Files: Click "Add Files..." to browse and queue specific audio files (.wav, .mp3, .flac, .ogg, .m4a, .aiff, .wma).
   • Input Folder: Choose an Input Folder and click "Rescan Folder" to automatically load all supported tracks.
   • Drag-and-Drop: Drag audio files or folders directly from Windows Explorer into the Queue panel.
   • Subfolders Option: Enable "Create a subfolder per track" to organize separated stems into neat subdirectories.

2. Model Selection:
   • Click "Change Model..." to select from 10 high-precision neural separation models:
     - Vocals & Instrumental (BS-RoFormer & Mel-Band RoFormer)
     - Karaoke (Lead vocal isolation while preserving background backing vocals)
     - De-Reverb (Acoustic room reflection & dry signal restoration)
     - Multi-Stem (Splitting into 4 or 6 discrete instrument stems: Vocals, Drums, Bass, etc.)
   • Automatic Download: Models download and verify automatically into local storage on first use.

3. Hardware & Quality Settings:
   • Device: CUDA (NVIDIA GPU with real-time VRAM detection) or CPU fallback.
   • VRAM Limit: 0 for Auto, or set a custom GB ceiling when running other GPU apps.
   • Chunk Size: Choose from Auto, Small (~3GB), Medium (~4GB), Big (~6GB), or Huge (~8+ GB).
   • Overlap Slider: Adjust cross-fade overlap from 2x (fastest throughput) to 8x (studio mastering fidelity).
   • Export Format: WAV 32-bit Float (maximum dynamic range), WAV 24-bit, WAV 16-bit, FLAC (lossless), or MP3 (320kbps).

4. Queue & Processing Controls:
   • Start / Stop: Click "Start Transform" to process the queue. Stop safely at any time.
   • Live Progress: Track percent progress, elapsed timer, and status (Pending, Downloading, Transforming, Finished, Failed).
   • Context Menu: Right-click any track in the queue to Open File, Show in Folder, Open Output Folder, Move to Top, or Remove.
   • Queue Management: Use "Clear Finished" or "Clear All" to maintain your queue.
   • Non-Blocking Engine: The interface remains completely responsive while the background worker processes audio.
"""

_EN_ABOUT = """BS-RoFormer Infer Studio
High-Performance Audio Source Separation Desktop Application

Author & Maintainer:
• I1Kuz
  GitHub: https://github.com/I1Kuz
  Project Repository: https://github.com/I1Kuz/bs-roformer-infer-gui

Original Model Architecture & Training:
• Band-Split RoFormer (BS-RoFormer):
  Wei-Tsung Lu et al. (ByteDance)
• PyTorch Architecture Implementation:
  Phil Wang (@lucidrains) — https://github.com/lucidrains/BS-RoFormer
• Model Checkpoints & Music Source Separation Training:
  Roman Solovyev (ZFTurbo) & Alexander Stempkovskiy
  Repository: https://github.com/ZFTurbo/Music-Source-Separation-Training
• High-Performance Inference Engine:
  OpenMirLab — https://github.com/openmirlab/bs-roformer-infer

User Interface & Windows Styling:
• Sun Valley ttk Theme (sv-ttk):
  rdbende — https://github.com/rdbende/Sun-Valley-ttk-theme
• Windows Modern DWM & Dark Titlebar (pywinstyles):
  Akascape — https://github.com/Akascape/py-window-styles

Core Machine Learning & Audio Libraries:
• PyTorch & CUDA Toolkit:
  PyTorch Foundation — https://pytorch.org
• Torchaudio, SoundFile, Librosa, NumPy

License:
• GNU General Public License v3.0 (GPL-3.0)
• Free and open-source software under the terms of GPL-3.0.
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
        frame_title="Files & Folders",
        input_folder="Input Folder:",
        output_folder="Output Folder:",
        browse="Browse...",
        add_files="Add Files...",
        rescan="Rescan Folder",
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
        action_reveal_input="Show in Folder",
        action_open_output="Open Output Folder",
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
        err_no_output_folder="Please select an Output Folder before starting separation.",
        file_filter_audio="Audio Files",
        select_files_title="Select Audio Files",
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
        subtitle="Band-Split RoFormer Audio Source Separation Studio",
        btn_close="Close",
        tab_quickstart="Quick Start",
        tab_settings="Audio & Quality",
        tab_models="Models & Formats",
        tab_about="About",
        quickstart_content=_EN_QUICKSTART,
        settings_content=_EN_SETTINGS_GUIDE,
        models_content=_EN_MODELS_GUIDE,
        about_content=_EN_ABOUT,
    ),
)


# ---------------------------------------------------------------------------
# Ukrainian text & translations
# ---------------------------------------------------------------------------

_UK_QUICKSTART = """Ласкаво просимо до BS-RoFormer Infer Studio!
Високопродуктивна робоча станція для нейромережевого розділення аудіодоріжок.

1. Додавання аудіофайлів:
   • Додати файли: Натисніть «Додати файли...», щоб обрати окремі треки (.wav, .mp3, .flac, .ogg, .m4a, .aiff, .wma).
   • Вхідна папка: Вкажіть вхідну папку та натисніть «Оновити папку» для автоматичного додавання знайдених аудіофайлів.
   • Перетягування (Drag-and-Drop): Перетягуйте файли або цілі папки безпосередньо з Провідника Windows у список черги.
   • Підпапки: Увімкніть «Створювати окрему папку для кожного треку», щоб зберігати розділені доріжки у персональних підкаталогах.

2. Вибір нейромережевої моделі:
   • Натисніть «Змінити модель...», щоб обрати одну з 10 моделей:
     - Вокал та Інструментал (BS-RoFormer та Mel-Band RoFormer)
     - Караоке (ізоляція лід-вокалу зі збереженням бек-вокалу)
     - Де-реверберація (очищення запису від луни та акустики приміщення)
     - Мульти-трек (розподіл на 4 або 6 окремих доріжок: вокал, бас, ударні тощо)
   • Автозавантаження: Обрані моделі автоматично завантажуються та верифікуються при першому використанні.

3. Параметри заліза та якості:
   • Пристрій: CUDA (NVIDIA GPU з моніторингом VRAM) або резервний режим CPU.
   • Ліміт VRAM: 0 для автоматичного визначення, або вкажіть ліміт (у ГБ) для контролю споживання пам'яті.
   • Розмір чанка: Auto (адаптивний), Small (~3GB), Medium (~4GB), Big (~6GB) або Huge (~8+ GB).
   • Слайдер перекриття: Регулюйте від 2x (максимальна швидкість) до 8x (ідеальне студійне склеювання без артефактів).
   • Формат експорту: WAV 32-bit Float (максимальний динамічний діапазон), WAV 24-bit, WAV 16-bit, FLAC (без втрат) або MP3 (320 кбіт/с).

4. Черга та пакетна обробка:
   • Запуск та зупинка: Кнопка «Розпочати обробку» запускає чергу. Зупинити процес можна в будь-який момент без збоїв.
   • Моніторинг у реальному часі: Відстеження прогресу (%), таймера та статусу (В черзі, Завантаження, Обробка, Завершено, Помилка).
   • Контекстне меню: Клікніть правою кнопкою миші по треку для швидких дій (Відкрити файл, Показати у папці, Відкрити папку збереження, На початок черги або Видалити).
   • Керування чергою: Кнопки «Очистити завершені» та «Очистити все».
   • Асинхронний воркер: Інтерфейс ніколи не зависає та залишається чуйним, оскільки обробка виконується в окремому ізольованому процесі.
"""

_UK_ABOUT = """BS-RoFormer Infer Studio
Десктопна студія для нейромережевого розділення аудіодоріжок

Автор та розробник:
• I1Kuz
  GitHub: https://github.com/I1Kuz
  Репозиторій проекту: https://github.com/I1Kuz/bs-roformer-infer-gui

Оригінальна архітектура моделей та навчання:
• Архітектура Band-Split RoFormer (BS-RoFormer):
  Wei-Tsung Lu та співавтори (ByteDance)
• Реалізація архітектури на PyTorch:
  Phil Wang (@lucidrains) — https://github.com/lucidrains/BS-RoFormer
• Контрольні точки моделей та навчання Music Source Separation Training:
  Roman Solovyev (ZFTurbo) та Alexander Stempkovskiy
  Репозиторій: https://github.com/ZFTurbo/Music-Source-Separation-Training
• Високопродуктивний рушій інференсу:
  OpenMirLab — https://github.com/openmirlab/bs-roformer-infer

Користувацький інтерфейс та інтеграція з Windows:
• Тема оформлення Sun Valley ttk (sv-ttk):
  rdbende — https://github.com/rdbende/Sun-Valley-ttk-theme
• Стилізація заголовка та DWM Windows (pywinstyles):
  Akascape — https://github.com/Akascape/py-window-styles

Машинне навчання та аудіо-бібліотеки:
• PyTorch & CUDA Toolkit:
  PyTorch Foundation — https://pytorch.org
• Torchaudio, SoundFile, Librosa, NumPy

Ліцензія:
• GNU General Public License v3.0 (GPL-3.0)
• Вільне програмне забезпечення з відкритим вихідним кодом згідно з умовами ліцензії GPL-3.0.
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
        frame_title="Файли та папки",
        input_folder="Вхідна папка:",
        output_folder="Папка збереження:",
        browse="Огляд...",
        add_files="Додати файли...",
        rescan="Оновити папку",
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
        action_reveal_input="Показати у папці",
        action_open_output="Відкрити папку збереження",
        action_prioritize="На початок черги",
        action_remove="Видалити",
        start_transform="Розпочати обробку",
        stop="Зупинити",
        ready="Готово",
        gpu_detecting="GPU: Визначення...",
        gpu_prefix="GPU: ",
        no_gpu="Сумісний GPU відсутній (режим CPU)",
        empty_title="Черга порожня",
        empty_hint="Додайте аудіофайли або оберіть вхідну папку для початку",
        summary_fmt="Усього: {total}  |  Завершено: {done}  |  В обробці: {proc}  |  В черзі: {pending}",
        err_no_output_folder="Будь ласка, оберіть папку збереження перед початком обробки.",
        file_filter_audio="Аудіофайли",
        select_files_title="Виберіть аудіофайли",
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
        subtitle="Студія розділення аудіодоріжок Band-Split RoFormer",
        btn_close="Закрити",
        tab_quickstart="Швидкий старт",
        tab_settings="Якість та звук",
        tab_models="Моделі та формати",
        tab_about="Про програму",
        quickstart_content=_UK_QUICKSTART,
        settings_content=_UK_SETTINGS_GUIDE,
        models_content=_UK_MODELS_GUIDE,
        about_content=_UK_ABOUT,
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
