# standard Library Imports
import json  # JSON serialization and deserialization
import logging  # logging utility
import datetime  # date and time manipulation
from decimal import Decimal  # decimal arithmetic
import random  # random number generation

# import the required Telegram modules
from telegram.ext import (
    CommandHandler,
    ApplicationBuilder,
    filters,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    PicklePersistence,
)

# import the Telegram API token from config.py
from config import TELEGRAM_API_TOKEN

from utils import (
    send_typing_action,
    generate_markup,
    get_timezone_details,
    get_timezone_from_location,
    get_day_suffix,
    get_current_utc_time,
    get_current_time_in_timezone,
    convert_time,
    questions,
)

# enable logging
logging.basicConfig(level=logging.INFO)

# declare constants for ConversationHandler
CITY, NEW_CITY, CONVERSION, DIFFERENCE, TIME = range(5)


# handler function for /start command
async def start_conversation(update, context):
    with open("en_strings.json", "r") as f:
        strings = json.load(f)

        welcome_message = strings["welcome_message"]
        await update.message.reply_text(welcome_message, parse_mode="HTML")
        await update.message.reply_text("Please enter a city name:")

    return CITY


# send a typing indicator in the chat
@send_typing_action
# handler function for user input city name
async def handle_city(update, context):
    # get user's city name input
    user_text = update.message.text
    # check if the user input is in all capital letters
    if user_text.isupper():
        # capitalize only the first letter and convert the rest to lowercase
        city_name = user_text.capitalize()
    else:
        # capitalize the first letter of each word
        city_name = user_text.title() if user_text.islower() else user_text
    # get the timezone name of the city from user input
    timezone_name = get_timezone_from_location(user_text)
    # if the detected timezone name is none, prompt the user to enter another city name
    if timezone_name is None:
        await update.message.reply_text(
            "Sorry, I couldn't recognize that city. Please enter another city name:"
        )
        return
    # store user's timezone name and city name as context user_data
    context.user_data["timezone_name"] = timezone_name
    context.user_data["city_name"] = city_name
    # get the current time in the timezone of the user input city
    city_time = get_current_time_in_timezone(timezone_name)
    # get the timezone abbreviation and formatted offset
    timezone_abbr, timezone_offset_formatted = get_timezone_details(timezone_name)
    context.user_data["timezone_abbr"] = timezone_abbr
    context.user_data["timezone_offset_formatted"] = timezone_offset_formatted
    # convert the city time string into a datetime object and format it
    city_time_obj = datetime.datetime.strptime(city_time, "%H:%M:%S %d.%m.%Y").replace(
        microsecond=0
    )
    day_suffix = get_day_suffix(city_time_obj.day)
    formatted_city_time = city_time_obj.strftime(f"%I:%M %p on %B %d{day_suffix}, %Y")
    # send the current time, timezone abbreviation and offset to the user and propose next actions
    await update.message.reply_text(
        f"It's currently {formatted_city_time} in {city_name}. Timezone: {timezone_abbr} ({timezone_offset_formatted})"
        "\n\nWhat do you want to do next?",
        reply_markup=generate_markup(4),
    )


# send a typing indicator in the chat
@send_typing_action
# handler function for when 'New City' button is pressed
async def handle_new_city(update, context):
    # get user's city name input
    user_text = update.message.text
    # check if the user input is in all capital letters
    if user_text.isupper():
        # capitalize only the first letter and convert the rest to lowercase
        city_name = user_text.capitalize()
    else:
        # capitalize the first letter of each word
        city_name = user_text.title() if user_text.islower() else user_text
    timezone_name = get_timezone_from_location(user_text)
    if timezone_name is None:
        await update.message.reply_text(
            "Sorry, I couldn't recognize that city. Please enter another city name:"
        )
        return
    context.user_data["timezone_name"] = timezone_name
    context.user_data["city_name"] = city_name
    city_time = get_current_time_in_timezone(timezone_name)
    timezone_abbr, timezone_offset_formatted = get_timezone_details(timezone_name)
    context.user_data["timezone_abbr"] = timezone_abbr
    context.user_data["timezone_offset_formatted"] = timezone_offset_formatted
    city_time_obj = datetime.datetime.strptime(city_time, "%H:%M:%S %d.%m.%Y").replace(
        microsecond=0
    )
    day_suffix = get_day_suffix(city_time_obj.day)
    formatted_city_time = city_time_obj.strftime(f"%I:%M %p on %B %d{day_suffix}, %Y")
    reply1 = f"The time in {city_name} right now is {formatted_city_time}. Timezone: {timezone_abbr} ({timezone_offset_formatted})"
    reply2 = f"It's currently {formatted_city_time} in {city_name}. Timezone: {timezone_abbr} ({timezone_offset_formatted})"
    reply = random.choice([reply1, reply2])
    await update.message.reply_text(reply)
    random_question = random.choice(questions)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=random_question,
        reply_markup=generate_markup(4),
    )


async def handle_callback_query(update, context):
    # retrieve the callback query object from the Update object
    query = update.callback_query
    await query.answer()
    if query.data == "new_city":
        await query.message.reply_text("Please enter a new city:")
        return NEW_CITY
    elif query.data == "conversion":
        messages = [
            "What city would you like to convert the time to?",
            "Please enter the city you want to convert the time to:",
        ]
        await query.message.reply_text(random.choice(messages))
        return CONVERSION
    elif query.data == "difference":
        await query.message.reply_text(
            "Please enter another city to compare the time difference:"
        )
        return DIFFERENCE
    elif query.data == "help":
        with open("en_strings.json", "r") as f:
            strings = json.load(f)
        description = strings["description"]
        await query.message.reply_text(
            description,
            parse_mode="HTML",
            reply_markup=generate_markup(3),
        )


# send a typing indicator in the chat
@send_typing_action
async def handle_conversion(update, context):
    user_input = update.message.text
    # store user's city name
    context.user_data["destination_city_name"] = user_input
    # ask user which time they want to convert from
    await update.message.reply_text(
        "Please enter the time in 12-hour format (HH:MM AM/PM) and the city you are converting from, like '02:30 AM London'"
    )
    return TIME


# send a typing indicator in the chat
@send_typing_action
async def handle_time(update, context):
    user_input = update.message.text
    destination_city_name = context.user_data.get("destination_city_name")

    # convert the time
    source_time_parts = user_input.split(" ", 2)
    source_time = source_time_parts[0].strip()
    am_pm = source_time_parts[1].strip()
    initial_city = source_time_parts[2].strip()

    # combine the source time and AM/PM indicator
    source_time = source_time + " " + am_pm

    initial_timezone = get_timezone_from_location(initial_city)
    if initial_timezone is None:
        await update.message.reply_text(
            "Invalid source city.", reply_markup=generate_markup(4)
        )
        return

    destination_timezone = get_timezone_from_location(destination_city_name)
    if destination_timezone is None:
        await update.message.reply_text(
            "Invalid destination city.", reply_markup=generate_markup(4)
        )
        return

    destination_time = convert_time(source_time, initial_timezone, destination_timezone)

    # send the converted time as the response
    await update.message.reply_text(
        f"The time in {destination_city_name} is {destination_time}."
    )
    random_question = random.choice(questions)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=random_question,
        reply_markup=generate_markup(4),
    )


async def get_time_difference(update, context):
    # get user's city name input
    user_text = update.message.text
    # check if the user input is in all capital letters
    if user_text.isupper():
        # capitalize only the first letter and convert the rest to lowercase
        city_name = user_text.capitalize()
    else:
        # capitalize the first letter of each word
        city_name = user_text.title() if user_text.islower() else user_text
    try:
        timezone_name = get_timezone_from_location(user_text)
        city_time = get_current_time_in_timezone(timezone_name)
        context.user_data["difference_city_name"] = city_name
        context.user_data["difference_timezone_name"] = timezone_name
        context.user_data["difference_time"] = city_time
        await calculate_time_difference(update, context)
    except ValueError:
        await update.message.reply_text(
            f"Sorry, I couldn't recognize {user_text} as a city. Please enter another city name:"
        )
        return


# send a typing indicator in the chat
@send_typing_action
async def calculate_time_difference(update, context):
    city_name_1 = context.user_data["city_name"]
    city_name_2 = context.user_data["difference_city_name"]
    timezone_name_1 = context.user_data["timezone_name"]
    timezone_name_2 = context.user_data["difference_timezone_name"]

    # get time in UTC for both cities
    utc_time_1 = get_current_utc_time(timezone_name_1)
    utc_time_2 = get_current_utc_time(timezone_name_2)

    # convert timezone-aware datetime objects to naive datetime objects
    naive_time_1 = utc_time_1.replace(tzinfo=None)
    naive_time_2 = utc_time_2.replace(tzinfo=None)

    # calculate timezone difference
    time_difference = naive_time_2 - naive_time_1
    # convert timezone difference to hours
    time_difference_hours = abs(time_difference.total_seconds() / 3600)

    # return time difference to the user
    if time_difference_hours < 0.01:
        message = (
            f"There is no time difference between {city_name_1} and {city_name_2}."
        )
    elif time_difference.total_seconds() > 0:
        difference_text = (
            f"{Decimal(abs(time_difference_hours)):.2f}".replace(".", ":")
            + " hours behind"
        )
        message = f"The time in {city_name_2} is {difference_text} {city_name_1} time."
    else:
        difference_text = (
            f"{Decimal(abs(time_difference_hours)):.2f}".replace(".", ":")
            + " hours ahead"
        )
        message = (
            f"The time in {city_name_2} is {difference_text} of {city_name_1} time."
        )
    await update.message.reply_text(message)
    random_question = random.choice(questions)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=random_question,
        reply_markup=generate_markup(4),
    )


def main():
    # set Telegram bot
    persistence = PicklePersistence(filepath="conversationbot")
    application = (
        ApplicationBuilder().token(TELEGRAM_API_TOKEN).persistence(persistence).build()
    )

    # create a conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_conversation)],
        states={
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_city)],
            NEW_CITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_city)
            ],
            CONVERSION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_conversion)
            ],
            TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_time)],
            DIFFERENCE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_time_difference)
            ],
        },
        fallbacks=[
            CallbackQueryHandler(
                handle_callback_query, pattern="^(conversion|difference|new_city|help)$"
            )
        ],
        allow_reentry=True,
        name="my_conversation",
        persistent=True,
    )
    # add ConversationHandler to application that will be used for handling updates
    application.add_handler(conv_handler)

    # start the Telegram bot
    application.run_polling()
