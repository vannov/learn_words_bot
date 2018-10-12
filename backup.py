CALLBACK_TYPE_SCHEDULE_START = "ss"
CALLBACK_TYPE_SCHEDULE_CONTINUE = "sc"
CALLBACK_TYPE_SCHEDULE_COMPLETE = "se"

SCHEDULE_FREQUENCY_DAILY="d"
SCHEDULE_FREQUENCY_WEEKLY="w"
SCHEDULE_FREQUENCY_OFF="o"


def schedule_start(bot, update):
    """ Starts scheduling notifications """
    text = 'Set notifications schedule.\nCurrent schedule: ...'

    daily = {
        'type': CALLBACK_TYPE_SCHEDULE_CONTINUE,
        'frequency': SCHEDULE_FREQUENCY_DAILY
    }
    weekly = {
        'type': CALLBACK_TYPE_SCHEDULE_CONTINUE,
        'frequency': SCHEDULE_FREQUENCY_WEEKLY
    }
    off = {
        'type': CALLBACK_TYPE_SCHEDULE_CONTINUE,
        'frequency': SCHEDULE_FREQUENCY_OFF
    }
    button_list = [
        InlineKeyboardButton(text="Daily",
                             callback_data=json.dumps(daily)),
        InlineKeyboardButton(text="Weekly",
                             callback_data=json.dumps(weekly)),
        InlineKeyboardButton(text="Turn off",
                             callback_data=json.dumps(off))
    ]
    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=3))
    bot.sendMessage(chat_id=get_chat_id(update), text=text, reply_markup=reply_markup)

def schedule_continue(bot, update, frequency):
    """ Continue scheduling notifications after user selected frequency """
    if frequency == SCHEDULE_FREQUENCY_DAILY:
        text = 'Select time you want to be notified daily.'
        text_value_pairs = [
            ('12 AM', 0),
            ('1 AM', 1),
            ('2 AM', 2),
            ('3 AM', 3),
            ('4 AM', 4),
            ('5 AM', 5),
            ('6 AM', 6),
            ('7 AM', 7),
            ('8 AM', 8),
            ('9 AM', 9),
            ('10 AM', 10),
            ('11 AM', 11),
            ('12 PM', 12),
            ('1 PM', 13),
            ('2 PM', 14),
            ('3 PM', 15),
            ('4 PM', 16),
            ('5 PM', 17),
            ('6 PM', 18),
            ('7 PM', 19),
            ('8 PM', 20),
            ('9 PM', 21),
            ('10 PM', 22),
            ('11 PM', 23)
        ]
    elif frequency == SCHEDULE_FREQUENCY_WEEKLY:
        text = 'Enter day you want to be notified weekly.'
        text_value_pairs = [
            ('Monday', 0),
            ('Tuesday', 1),
            ('Wednesday', 2),
            ('Thursday', 3),
            ('Friday', 4),
            ('Saturday', 5),
            ('Sunday', 6),
        ]
    elif frequency == SCHEDULE_FREQUENCY_OFF:
        text = 'Turning off notifications.'
        #TODO: turn off
        bot.sendMessage(chat_id=get_chat_id(update), text=text)
        return
    else:
        error(bot, update, "Unexpected frequency selected: " + str(frequency))
        return

    button_list = create_callback_schedule_button_list(text_value_pairs=text_value_pairs, frequency=frequency)
    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=4))
    bot.sendMessage(chat_id=get_chat_id(update), text=text, reply_markup=reply_markup)

def schedule_complete(bot, update, callback_dict):
    """ Completes scheduling notifications after user selected hour/day """
    frequency = callback_dict['frequency']
    value = callback_dict['value']
    # TODO: write to storage