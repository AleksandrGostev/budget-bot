#!/usr/bin/env python3
#
# A library that allows to create an inline calendar keyboard.
# grcanosa https://github.com/grcanosa
#
"""
Base methods for calendar keyboard creation and processing.
"""

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
import datetime
import calendar


def create_callback_data(action, year, month, day, payment_id):
    """ Create the callback data associated to each button"""
    return ";".join([action, str(year), str(month), str(day), payment_id])


def separate_callback_data(data):
    """ Separate the callback data"""
    return data.split(";")


def create_calendar(year=None, month=None, payment_id=None):
    now = datetime.datetime.now()
    if year is None: year = now.year
    if month is None: month = now.month
    data_ignore = create_callback_data("IGNORE", year, month, 0, payment_id)
    keyboard = InlineKeyboardMarkup(row_width=7)
    # First row - Month and Year
    row = [InlineKeyboardButton(calendar.month_name[month] + " " + str(year), callback_data=data_ignore)]
    keyboard.row(*row)
    # Second row - Week Days
    row = []
    for day in ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]:
        row.append(InlineKeyboardButton(day, callback_data=data_ignore))
    keyboard.row(*row)

    my_calendar = calendar.monthcalendar(year, month)
    for week in my_calendar:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(" ", callback_data=data_ignore))
            else:
                row.append(InlineKeyboardButton(str(day), callback_data=create_callback_data("DAY", year, month, day,
                                                                                             payment_id)))
        keyboard.row(*row)
    # Last row - Buttons
    row = [InlineKeyboardButton("<", callback_data=create_callback_data("PREV-MONTH", year, month, day, payment_id)),
           InlineKeyboardButton(" ", callback_data=data_ignore),
           InlineKeyboardButton(">", callback_data=create_callback_data("NEXT-MONTH", year, month, day, payment_id))]
    keyboard.row(*row)

    return keyboard
