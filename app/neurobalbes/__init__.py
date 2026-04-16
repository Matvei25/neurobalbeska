# -*- coding: utf-8 -*-
"""
Нейробалбес - модуль для генерации контента на основе обученных данных
"""

from .balbes import Balbes
from .text_generator import TextGenerator
from .meme_generator import MemeGenerator
from .voice_generator import VoiceGenerator
from .demotivator_generator import DemotivatorGenerator

__all__ = [
    'Balbes',
    'TextGenerator',
    'MemeGenerator',
    'VoiceGenerator',
    'DemotivatorGenerator',
]
