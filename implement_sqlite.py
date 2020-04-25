#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import logging
import sqlite3
from pathlib import Path  # nueva forma de trabajar con rutas
from typing import List, Text, NoReturn, Dict, Any

from procamora_utils.interface_sqlite import conection_sqlite, execute_script_sqlite
from procamora_utils.logger import get_logging

from stats import Stats
from word import Word

logger: logging = get_logging(False, 'sqlite')

# Ruta absoluta de la BD
DB: Path = Path(Path(__file__).resolve().parent, "dictionary.db")
DB_STRUCTURE: Path = Path(Path(__file__).resolve().parent, "dictionary.sql")


def select_all_words() -> List[Word]:
    query: Text = "SELECT * FROM Words"
    response_query: List[Dict[Text, Any]] = conection_sqlite(DB, query, is_dict=True)
    response: List[Word] = list()
    for i in response_query:
        word: Word = Word(i['id'], i['spanish'].split(','), i['english'].split(','))
        response.append(word)
    return response


def get_word(word: Text) -> List[Word]:
    word_all: Text = f'%{word}%'
    query: Text = "SELECT Words.* " \
                  "FROM Words " \
                  "WHERE spanish LIKE ? OR english LIKE ?"
    logger.info(query)
    response_query: List[Dict[Text, Any]] = conection_sqlite(DB, query, query_params=(word_all, word_all), is_dict=True)
    response: List[Word] = list()
    for i in response_query:
        word: Word = Word(i['id'], i['spanish'].split(','), i['english'].split(','))
        response.append(word)
    return response


def select_user_stats(id_user: int, limit) -> Stats:
    query = "SELECT Stats.id_user, Stats.successful, Words.* " \
            "FROM Stats " \
            "INNER JOIN Words ON Stats.id_word = Words.id " \
            "WHERE Stats.id_user=?" \
            "ORDER BY Stats.id DESC " \
            "LIMIT ?;"

    total_fail: int = 0
    total_success: int = 0
    words: List[Word] = list()
    response_query: List[Dict[Text, Any]] = conection_sqlite(DB, query, query_params=(id_user, limit), is_dict=True)
    for i in response_query:
        success: bool = False
        if i['successful'] == 'True':
            success = True
            total_success += 1
        else:
            total_fail += 1
        word: Word = Word(i['id'], i['spanish'].split(','), i['english'].split(','), successful=success)
        words.append(word)

    stats: Stats = Stats(id_user, total_fail, total_success, words)
    return stats


def insert_stat(id_user: int, word: Word, successful: bool) -> NoReturn:
    query: Text = f"INSERT INTO Stats(id_user, id_word, successful) VALUES (?, ?, ?)"
    logger.info(query)
    conection_sqlite(DB, query, query_params=(id_user, word.id, str(successful)), is_dict=False)


def insert_word(word: Word) -> Text:
    query: Text = f"INSERT INTO Words(spanish, english) VALUES (?, ?)"
    logger.info(f'{query}, ({word.get_str_spanish()},{word.get_str_english()})')
    try:
        conection_sqlite(DB, query, query_params=(word.get_str_spanish(), word.get_str_english()), is_dict=False)
        return str()
    except sqlite3.IntegrityError as e:
        logger.error(e)
        return str(e)


def check_database() -> NoReturn:
    """
    Comprueba si existe la base de datos, sino existe la crea
    :return:
    """
    try:
        query: Text = "SELECT * FROM Words"
        conection_sqlite(DB, query)
    except OSError:
        logger.info(f'the database {DB} doesn\'t exist, creating it with the default configuration')
        execute_script_sqlite(DB, DB_STRUCTURE.read_text())
