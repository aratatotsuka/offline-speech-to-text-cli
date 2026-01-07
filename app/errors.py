from __future__ import annotations


class AppError(Exception):
    exit_code: int = 1


class ConfigError(AppError):
    exit_code = 2


class NoInputFilesError(AppError):
    exit_code = 3


class ModelNotFoundError(AppError):
    exit_code = 4


class WhisperFailedError(AppError):
    exit_code = 5


class DocxConversionError(AppError):
    exit_code = 6


class DiarizationNotSupportedError(AppError):
    exit_code = 10

