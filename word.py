#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from typing import Text, List, NoReturn, Callable

import unidecode

# remove especial char (acents ó->o, ñ->n) and espaces
convert_str: Callable[[Text], Text] = lambda w: unidecode.unidecode(str(w).strip())


@dataclass()
class Word:
    id: int
    spanish: List[Text]
    english: List[Text]
    successful: bool = False  # use for stats

    def __post_init__(self: Word) -> NoReturn:
        self.spanish = list(map(convert_str, self.spanish))
        self.english = list(map(convert_str, self.english))

    def get_str_spanish(self: Word) -> Text:
        return ', '.join(self.spanish)

    def get_str_english(self: Word) -> Text:
        return ', '.join(self.english)

    def __hash__(self: Word) -> int:
        return hash((self.get_str_english(), self.get_str_spanish()))

    def __str__(self) -> Text:
        return f'{self.__class__.__name__}(id={self.id}, english=[{self.get_str_english()}], ' \
               f'spanish=[{self.get_str_spanish()}], {self.successful})'
