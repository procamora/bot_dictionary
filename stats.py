#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Set, Dict, Tuple, NoReturn

from word import Word


def sort_protocol_based_attempts(word: Word, repeat: Dict[int, int]):
    return repeat[word.id]


@dataclass
class Stats:
    id_user: int
    total_fail: int
    total_success: int
    questions: List[Word]

    def __post_init__(self: Stats) -> NoReturn:
        self.questions = sorted(self.questions, key=lambda w: w.get_str_english(), reverse=False)

    def get_top_questions_failed_attempts(self: Stats, top: int) -> Tuple[List[Word], List[int]]:
        """
        Metodo para obtener los n puertos que mas fallos has tenido. Esta funciona puede ser costosa en tiempo
        :param top:
        :return:
        """

        # obtengo un set con los protocolos, eliminando repetidos (necesario implementar func hash en stats y protocols)
        # filtrando unicamente los que se han fallado
        unic_word: Set[Word] = set(filter(lambda p: not p.successful, self.questions))
        # unic_protocols: Set[Protocol] = set([i for i in self.questions])

        # Obtener repeticiones totales de cada elemento del set, [[word.id], repeticiones]
        repeat: Dict[int, int] = dict()
        for prt in unic_word:
            cont: int = 0
            for y in self.questions:
                if prt.id == y.id and not y.successful:
                    cont += 1
            repeat[prt.id] = cont

        # Ordenar set en base a las repeticiones
        sort_words: List[Word] = sorted(unic_word,
                                        key=lambda p: sort_protocol_based_attempts(p, repeat),
                                        reverse=True)

        response_words: List[Word] = list()
        response_fails: List[int] = list()

        # size max: len(sort_protocols)
        if len(sort_words) < top:
            top = len(sort_words)

        # listas con los n elementos con mas intentos
        for i in range(0, top):
            response_words.append(sort_words[i])
            response_fails.append(repeat[sort_words[i].id])

        return response_words, response_fails

    def __hash__(self: Stats) -> int:
        return hash((self.id_user, self.questions))
