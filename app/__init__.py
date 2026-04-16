"""
Нейробалбес - Telegram бот для генерации контента на основе Марковских цепей.
"""

try:
    from .core.config import version
    __version__ = version
except ImportError:
    __version__ = "0.1.0"