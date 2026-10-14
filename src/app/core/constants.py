from typing import final


@final
class AppConstants:
    """Core application-wide constants."""

    GITHUB_REPO_URL: str = "https://github.com/I1Kuz/bs-roformer-infer-gui"
    APP_DATA_DIRNAME: str = "BSRoFormer Studio"
    CACHE_DIRNAME: str = "bs-roformer-infer"


GITHUB_REPO_URL: str = AppConstants.GITHUB_REPO_URL
APP_DATA_DIRNAME: str = AppConstants.APP_DATA_DIRNAME
CACHE_DIRNAME: str = AppConstants.CACHE_DIRNAME
