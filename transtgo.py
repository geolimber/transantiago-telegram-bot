#!/usr/bin/env python
# -*- coding: utf-8 -*-
from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
import os
import json
import requests

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Keyboard variables
location_keyboard = KeyboardButton(text="Buscar paraderos cercanos", request_location=True)
location_keyboard = ReplyKeyboardMarkup([[location_keyboard]], resize_keyboard=True)


# Define handlers
def start(bot, update):
    """Send a message when the command /start is issued."""
    update.message.reply_text(
        'Hola! Soy tus ojos en sistema de TranSantiago. Te ayudo ver donde esta el bus que estas esperando. Simplemente comparte tu ubicación para buscar paraderos mas cercanos, o si ya estas en el paradero, mándame el código indicado en la esquina inferior derecha del letrero.',
        reply_markup=location_keyboard)


def help(bot, update):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Simplemente comparte tu ubicación para buscar paraderos mas cercanos, o si ya estas en '
                              'el paradero, mándame el código indicado en la esquina inferior derecha del letrero.',
                              reply_markup=location_keyboard)


def echo(bot, update):
    """Get bus stop next arrivals"""
    update.message.reply_text('Solicitando información, espera...', reply_markup=ReplyKeyboardRemove())
    url = 'https://api.scltrans.it/v2/stops/{}/next_arrivals'.format(update.message.text.replace(' ', ''))
    try:
        with requests.get(url=url) as file:
            j = file.json()
            if file.status_code !=200:
                raise Exception('Servidor Transantiago no responde')
    except Exception as e:
        update.message.reply_text('Parece que hubo un error al '
                                  'obtener los datos. Intenta de nuevo mas tarde.\n{}'.format(e),
                                  reply_markup=location_keyboard)
        return None
    if j['results']:
        next_arrivals = [[x['route_id'], x['bus_distance']] for x in j['results']]
        message = '*\u2116 Micro* - _Distancia (m)_\n'
        for i in next_arrivals:
            if i[1] is not None:
                message += '\u2116 *{}* a _{}_ metros\n'.format(i[0], i[1])
            else:
                message += '\u2116 *{}* fuera de horario\n'.format(i[0])
        update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=location_keyboard)
    else:
        update.message.reply_text('Esto no se parece a un código de paradero correcto😐',
                                  reply_markup=location_keyboard)


def ubicacion(bot, update):
    # search for bus stops near received location
    received_location = update.message.location
    update.message.reply_text('Recibido.\nBuscando paraderos, espera...')
    url = 'https://api.scltrans.it/v1/stops?center_lat={}&center_lon={}&radius=300'.format(received_location.latitude,
                                                                                           received_location.longitude)
    try:
        with requests.get(url=url) as file:
            j = file.json()
            if j['results']:
                reply_keyboard = [[i['stop_id']] for i in j['results']]
                update.message.reply_text('Elija tu paradero',
                                          reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True,
                                                                           resize_keyboard=True))
            else:
                update.message.reply_text('¿Oye, donde andai?\nNo enctuentro paraderos en tu alrededor🤔',
                                          reply_markup=location_keyboard)

    except Exception as e:
        update.message.reply_text('Parece que hubo un error al '
                                  'obtener los datos. Intenta de nuevo más tarde.')


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    """Start the bot."""
    token = os.environ.get('TS_TOKEN')
    PORT = int(os.environ.get('PORT', '8443'))
    # Creating EventHandler and passing bot's token to this handler.
    updater = Updater(token)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, echo))

    # if message is a location, then show nearest bus stops
    dp.add_handler(MessageHandler(Filters.location, ubicacion))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_webhook(listen="0.0.0.0",
                          port=PORT,
                          url_path=token)
    updater.bot.set_webhook("https://transtgo-bot.herokuapp.com/" + token)
    updater.idle()


if __name__ == '__main__':
    main()
# TODO: Cambiar lista de paraderos para lista inline buttons con callback data
# TODO: Agregar botón repetir solicitud
