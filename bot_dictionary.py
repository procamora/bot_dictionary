#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# https://geekytheory.com/telegram-programando-un-bot-en-python/
# https://bitbucket.org/master_groosha/telegram-proxy-bot/src/07a6b57372603acae7bdb78f771be132d063b899/proxy_bot.py?at=master&fileviewer=file-view-default
# https://github.com/eternnoir/pyTelegramBotAPI/blob/master/telebot/types.py

"""commands
Name:
Dictionary Spanish - English

username:
procamora_dictionary_bot

Description:
This is a bot to study English-Spanish vocabulary. It allows you to insert words and perform vocabulary tests.

About:
This bot has been developed by @procamora

Botpic:
<imagen del bot>

Commands:
set_en - Add a word in English
set_es - Add a word in Spanish
get - Get a word
test - Start test mode
stats - See statistics
help - Show help
start - Start the bot
"""

import configparser
import logging
import random
import re
import sys
from pathlib import Path
from typing import NoReturn, Tuple, List, Text, Callable

import unidecode
from procamora_utils.logger import get_logging
from requests import exceptions
from telebot import TeleBot, types, apihelper

from implement_sqlite import select_all_words, check_database, insert_stat, select_user_stats, get_word, insert_word
from stats import Stats
from word import Word

logger: logging = get_logging(False, 'bot_dictionary')


def get_basic_file_config():
    return '''[BASICS]
ADMIN = 111111
BOT_TOKEN = 1069111113:AAHOk9K5TAAAAAAAAAAIY1OgA_LNpAAAAA
DEBUG = 0
LIMIT_STATS = 500
'''


FILE_CONFIG: Path = Path(Path(__file__).resolve().parent, "settings.cfg")
if not FILE_CONFIG.exists():
    logger.critical(f'File {FILE_CONFIG} not exists and is necesary')
    FILE_CONFIG.write_text(get_basic_file_config())
    logger.critical(f'Creating file {FILE_CONFIG}. It is necessary to configure the file.')
    sys.exit(1)

config: configparser.ConfigParser = configparser.ConfigParser()
config.read(FILE_CONFIG)

config_basic: configparser.SectionProxy = config["BASICS"]

if bool(int(config_basic.get('DEBUG'))):
    bot: TeleBot = TeleBot(config["DEBUG"].get('BOT_TOKEN'))
else:
    bot: TeleBot = TeleBot(config_basic.get('BOT_TOKEN'))

owner_bot: int = int(config_basic.get('ADMIN'))

check: bytes = b'\xE2\x9C\x94'
cross: bytes = b'\xE2\x9D\x8C'

my_commands: Tuple[Text, ...] = (
    '/set_en',  # 0
    '/set_es',  # 1
    '/get',  # 2
    '/test',  # 3
    '/stats',  # 4

    '/start',  # -3
    '/help',  # -2
    '/exit',  # -1 (SIEMPRE TIENE QUE SER EL ULTIMO, ACCEDO CON -1)
)

# remove especial char (acents ó->o, ñ->n)
remove_especial_chars: Callable[[Text], Text] = lambda w: unidecode.unidecode(w)


def get_markup_cmd() -> types.ReplyKeyboardMarkup:
    markup: types.ReplyKeyboardMarkup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.row(my_commands[0], my_commands[1])
    markup.row(my_commands[2], my_commands[3], my_commands[4])
    markup.row(my_commands[-2], my_commands[-1])
    # markup.row(my_commands[4])
    return markup


def is_response_command(message: types.Message) -> bool:
    response: bool = False
    if message.text[0] == '/':
        response = True

    if message.text == my_commands[-1]:  # exit
        bot.reply_to(message, "Question round stop", reply_markup=get_markup_cmd())
    elif message.text == my_commands[-2]:  # help
        command_help(message)
    elif message.text == my_commands[-3]:  # start
        command_start(message)
    elif message.text == my_commands[0]:  # set_en
        set_en(message)
    elif message.text == my_commands[1]:  # set_es
        set_es(message)
    elif message.text == my_commands[2]:  # get
        get_world(message)
    elif message.text == my_commands[3]:  # test
        send_word_en(message)
    elif message.text == my_commands[4]:  # stats
        send_stats(message)
    return response


def get_random_word() -> Word:
    """
    Obtengo todos los protocolos disponibles y aleatoriamente selecciono uno para retornarlo
    :return Protocol:
    """
    response_query: List[Word] = select_all_words()
    element: int = random.randrange(0, len(response_query) - 1)
    logger.debug(response_query[element])
    return response_query[element]


def report_and_repeat(message: types.Message, word: Word, func: Callable, info: Text):
    """
    Metodo auxiliar con el que volver a preguntar tras una respuesta no valida
    :param message:
    :param word:
    :param func:
    :param info:
    :return:
    """
    bot.reply_to(message, info, reply_markup=get_markup_cmd())
    bot.register_next_step_handler(message, func, word=word)


# Handle always first "/start" message when new chat with your bot is created
@bot.message_handler(commands=["start"])
def command_start(message: types.Message) -> NoReturn:
    bot.send_message(message.chat.id,
                     f"Welcome to the bot Dictionary Spanish - English\nThis is a bot to study English-Spanish "
                     f"vocabulary. It allows you to insert words and perform vocabulary tests."
                     f"\nYour id is: {message.chat.id}",
                     reply_markup=get_markup_cmd())
    command_system(message)
    return  # solo esta puesto para que no falle la inspeccion de codigo


@bot.message_handler(commands=["help"])
def command_help(message: types.Message) -> NoReturn:
    markup: types.InlineKeyboardMarkup = types.InlineKeyboardMarkup()
    itembtna: types.InlineKeyboardButton = types.InlineKeyboardButton(
        'Github', url="https://github.com/procamora/bot_dictionary")
    markup.row(itembtna)
    bot.send_message(message.chat.id, 'You can find the source code for this bot in:', reply_markup=markup)
    command_system(message)
    return  # solo esta puesto para que no falle la inspeccion de codigo


@bot.message_handler(commands=["system"])
def command_system(message: types.Message) -> NoReturn:
    commands: Text = '\n'.join(i for i in my_commands)
    bot.send_message(message.chat.id, f"List of available commands\nChoose an option:\n{commands}",
                     reply_markup=get_markup_cmd())
    return  # solo esta puesto para que no falle la inspeccion de codigo


@bot.message_handler(commands=['exit'])
def send_exit(message: types.Message) -> NoReturn:
    bot.send_message(message.chat.id, "go to menu", reply_markup=get_markup_cmd())
    return


@bot.message_handler(commands=['set_en'])
def set_en(message: types.Message) -> NoReturn:
    msg: List[Text] = remove_especial_chars(str(message.text).strip()).split(' ')
    if len(msg) != 3:
        bot.reply_to(message, 'Command incomplete. The command requires a search word as an argument.\n'
                              'Ex: /set_en wish deseo or /set_en wish deseo,querer\n'
                              'Important: if multiple synonyms are added there can be no spacing between the commas,',
                     reply_markup=get_markup_cmd())
        return

    regex: Text = r'^(([a-z]+),?)+$'
    fail: bool = False
    if not re.search(regex, msg[2], re.IGNORECASE):
        bot.reply_to(message, f'{msg[2]} does not satisfy the regex: {regex}\n', reply_markup=get_markup_cmd())
        fail = True
    if not re.search(regex, msg[1], re.IGNORECASE):
        bot.reply_to(message, f'{msg[1]} does not satisfy the regex: {regex}\n', reply_markup=get_markup_cmd())
        fail = True
    if fail:  # show all errors before exit
        return

    word: Word = Word(0, msg[2].split(','), msg[1].split(','))  # id=0 nor use in insert
    insert: Text = insert_word(word)
    if re.search('UNIQUE constraint failed', insert, re.IGNORECASE):
        bot.reply_to(message, f'The word {word.get_str_english()} is already stored', reply_markup=get_markup_cmd())
    else:
        bot.reply_to(message, f'insert: {word}', reply_markup=get_markup_cmd())
    return


@bot.message_handler(commands=['set_es'])
def set_es(message: types.Message) -> NoReturn:
    msg: List[Text] = remove_especial_chars(str(message.text).strip()).split(' ')
    if len(msg) != 3:
        bot.reply_to(message, 'Command incomplete. The command requires a search word as an argument.\n'
                              'Ex: /set_es deseo wish or /set_es deseo,querer wish\n'
                              'Important: if multiple synonyms are added there can be no spacing between the commas,',
                     reply_markup=get_markup_cmd())
        return

    regex: Text = r'^(([a-z]+),?)+$'
    fail: bool = False
    if not re.search(regex, msg[1], re.IGNORECASE):
        bot.reply_to(message, f'{msg[1]} does not satisfy the regex: {regex}\n', reply_markup=get_markup_cmd())
        fail = True
    if not re.search(regex, msg[2], re.IGNORECASE):
        bot.reply_to(message, f'{msg[2]} does not satisfy the regex: {regex}\n', reply_markup=get_markup_cmd())
        fail = True
    if fail:  # show all errors before exit
        return

    word: Word = Word(0, msg[1].split(','), msg[2].split(','))  # id=0 nor use in insert
    insert: Text = insert_word(word)
    if re.search('UNIQUE constraint failed', insert, re.IGNORECASE):
        bot.reply_to(message, f'The word {word.get_str_spanish()} is already stored', reply_markup=get_markup_cmd())
    else:
        bot.reply_to(message, f'insert: {word}', reply_markup=get_markup_cmd())
    return


@bot.message_handler(commands=['get'])
def get_world(message: types.Message) -> NoReturn:
    msg: List[Text] = str(message.text).strip().split(' ')
    if len(msg) != 2:
        bot.reply_to(message, 'Command incomplete. The command requires a search word as an argument.\nEx: /get wish',
                     reply_markup=get_markup_cmd())
        return

    words: List[Word] = get_word(msg[1])
    response: Text = str()
    for w in words:
        response += f'*english*={w.get_str_english()}\n*spanish*={w.get_str_spanish()}\n\n'

    if len(response) == 0:
        bot.reply_to(message, 'Word not stored in the database', reply_markup=get_markup_cmd(), parse_mode='MarkdownV2')
    else:
        bot.reply_to(message, escape_string(response), reply_markup=get_markup_cmd(), parse_mode='MarkdownV2')
    return


@bot.message_handler(commands=['stats'])
def send_stats(message: types.Message) -> NoReturn:
    """
    Muestra las estadisticas del usuario
    :param message:
    :return:
    """
    stat: Stats = select_user_stats(message.chat.id, int(config_basic.get('LIMIT_STATS')))
    logger.debug(stat)
    response: Text = f"user: {message.from_user.username}\n" \
                     f"total questions: {len(stat.questions)}\n" \
                     f"total successful: {stat.total_success}\n" \
                     f"total failed: {stat.total_fail}\n" \
                     "Top failed:\n"

    list_words: List[Word]
    list_attemps: List[int]
    list_words, list_attemps = stat.get_top_questions_failed_attempts(40)
    for word, attemp in zip(list_words, list_attemps):
        response += f'   - {attemp} (attemps) -> *english*={word.get_str_english()}, *spanish*={word.get_str_spanish()}\n'

    bot.reply_to(message, escape_string(response), reply_markup=get_markup_cmd(), parse_mode='MarkdownV2')
    return


@bot.message_handler(commands=['test'])
def send_word_en(message: types.Message, reply: bool = True) -> NoReturn:
    """
    Modo test en el que estoy realizando preguntas y asignado una funcion para que trate la respuesta
    :param message:
    :param reply:
    :return:
    """
    word: Word = get_random_word()

    question: str = f'New question:\nWhat is the English meaning of the word *{word.get_str_english()}*?'
    if reply:
        bot.reply_to(message, escape_string(question), reply_markup=get_markup_cmd(), parse_mode='MarkdownV2')
    else:
        bot.send_message(message.chat.id, escape_string(question), reply_markup=get_markup_cmd(),
                         parse_mode='MarkdownV2')

    bot.register_next_step_handler(message, check_word_es, word=word)
    return


def check_word_es(message: types.Message, word: Word) -> NoReturn:
    """
    Metodo para comprobar la respuesta en el modo test. Si recibo un comando ejecuto su funcion, y sino compruebo
    que sea una palabra valida y despues si es aceptable para la respuesta esperada.
    Finalmente se llama a la funcion que que la invoco para hacer un blucle infinito de preguntas.
    :param message:
    :param word:
    :return:
    """
    if is_response_command(message):
        return

    if not re.search(r'^[a-z]+$', message.text, re.IGNORECASE):
        report_and_repeat(message, word, check_word_es, 'Enter a valid word')
        return

    # msg: Text = unidecode.unidecode()  # remove especial char (acents ó->o, ñ->n)
    msg: Text = remove_especial_chars(message.text)
    if re.search(rf'{msg}', word.get_str_spanish(), re.IGNORECASE):
        bot.send_message(message.chat.id, check.decode("utf-8"), reply_markup=get_markup_cmd())
        insert_stat(message.chat.id, word, True)
    else:
        bot.send_message(message.chat.id, cross.decode("utf-8"), reply_markup=get_markup_cmd())
        insert_stat(message.chat.id, word, False)

    response: Text = f'*english*={word.get_str_english()}\n*spanish*={word.get_str_spanish()}'
    bot.reply_to(message, escape_string(response), reply_markup=get_markup_cmd(), parse_mode='MarkdownV2')
    logger.info(f'{word.get_str_english()} == {msg}')
    logger.info(word)
    send_word_en(message, reply=False)


@bot.message_handler(regexp=".*")
def text_not_valid(message: types.Message) -> NoReturn:
    texto: Text = 'unknown command, enter a valid command :)'
    bot.reply_to(message, texto, reply_markup=get_markup_cmd())
    command_system(message)
    return


def escape_string(text: Text) -> Text:
    # In all other places characters '_‘, ’*‘, ’[‘, ’]‘, ’(‘, ’)‘, ’~‘, ’`‘, ’>‘, ’#‘, ’+‘, ’-‘, ’=‘, ’|‘, ’{‘, ’}‘,
    # ’.‘, ’!‘ must be escaped with the preceding character ’\'.
    return text.replace('=', r'\=').replace('_', r'\_').replace('(', r'\(').replace(')', r'\)').replace('-', r'\-'). \
        replace('.', r'\.').replace('>', r'\>')


def main() -> NoReturn:
    check_database()  # create db if not exists
    try:
        import urllib
        bot.send_message(owner_bot, 'Starting bot', reply_markup=get_markup_cmd(), disable_notification=True)
        logger.info('Starting bot')
    except (apihelper.ApiException, exceptions.ReadTimeout) as e:
        logger.critical(f'Error in init bot: {e}')
        sys.exit(1)

    # Con esto, le decimos al bot que siga funcionando incluso si encuentra algun fallo.
    bot.infinity_polling(none_stop=True)


if __name__ == "__main__":
    main()
