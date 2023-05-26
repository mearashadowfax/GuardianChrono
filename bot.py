# Standard Library Imports
import asyncio  # Asynchronous programming support
import json  # JSON serialization and deserialization
import logging  # Logging utility
import datetime  # Date and time manipulation
from decimal import Decimal  # Decimal arithmetic
from functools import wraps  # Function decorator utility
import random  # Random number generation

# Third-Party Imports
import pytz  # Timezone manipulation
import spacy  # Natural language processing
import dateparser
from geopy.geocoders import Nominatim  # Geocoding service
from timezonefinder import TimezoneFinder  # Timezone lookup

# import the required Telegram modules
from telegram.constants import ChatAction
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    ApplicationBuilder,
    ContextTypes,
    filters,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
)

# import the Telegram API token from config.py
from config import TELEGRAM_API_TOKEN

# enable logging
logging.basicConfig(level=logging.INFO)

# load pre-trained spacy model
nlp = spacy.load("en_core_web_sm")

# Geocoding service
geolocator = Nominatim(user_agent="timezone_converter")
timezone_finder = TimezoneFinder()

# declare constants for ConversationHandler
CITY, NEW_CITY, CONVERSION, DIFFERENCE, TIME = range(5)

# specify the reply markup layout
reply_markup = [
    [
        InlineKeyboardButton("Convert", callback_data="conversion"),
        InlineKeyboardButton("Difference", callback_data="difference"),
    ],
    [
        InlineKeyboardButton("New City", callback_data="new_city"),
        InlineKeyboardButton("Help", callback_data="help"),
    ],
]
# combine the buttons into a markup layout
markup = InlineKeyboardMarkup(reply_markup)


# define the send_action decorator
def send_action(action, delay=1):
    def decorator(func):
        @wraps(func)
        async def command_func(update, context, *args, **kwargs):
            await context.bot.send_chat_action(
                chat_id=update.effective_message.chat_id, action=action
            )
            await asyncio.sleep(delay)  # wait for the specified delay time
            return await func(update, context, *args, **kwargs)

        return command_func

    return decorator


# set the aliases with custom delays
send_typing_action = send_action(
    ChatAction.TYPING, delay=1
)  # change the delay time as needed


# function to create markup with specific number of buttons
def generate_markup(num_buttons):
    if num_buttons == 3:
        # return a markup with the first three buttons only
        return InlineKeyboardMarkup(
            [reply_markup[0][:num_buttons]] + [reply_markup[1][:1]]
        )
    else:
        # return the full markup with all four buttons
        return InlineKeyboardMarkup(reply_markup)


# handler function for /start command
async def start(update, context):
    with open("en_strings.json", "r") as f:
        strings = json.load(f)
    welcome_message = strings["welcome_message"]
    await update.message.reply_text(welcome_message, parse_mode="HTML")
    await update.message.reply_text("Please enter a city name:")
    return CITY


# send a typing indicator in the chat
@send_typing_action
# handler function for user input city name
async def handle_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # get user's city name input
    user_text = update.message.text
    # format the user input (capitalize first letter of each word)
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
    formatted_city_time = city_time_obj.strftime("%I:%M %p on %B %dth, %Y")
    # send the current time, timezone abbreviation and offset to the user and propose next actions
    await update.message.reply_text(
        f"It's currently {formatted_city_time} in {city_name}. Timezone: {timezone_abbr} ({timezone_offset_formatted})"
        "\n\nWhat do you want to do next?",
        reply_markup=generate_markup(4),
    )


# send a typing indicator in the chat
@send_typing_action
# handler function for when 'New City' button is pressed
async def handle_new_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
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
    formatted_city_time = city_time_obj.strftime("%I:%M %p on %B %dth, %Y")
    reply1 = f"The time in {city_name} right now is {formatted_city_time}. Timezone: {timezone_abbr} ({timezone_offset_formatted})"
    reply2 = f"It's currently {formatted_city_time} in {city_name}. Timezone: {timezone_abbr} ({timezone_offset_formatted})"
    reply = random.choice([reply1, reply2])
    await update.message.reply_text(
        reply,
        reply_markup=generate_markup(4),
    )
    # switch the conversation context to 'NEW_CITY'
    return NEW_CITY


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
        return NEW_CITY


# send a typing indicator in the chat
@send_typing_action
async def handle_conversion(update, context):
    user_input = update.message.text
    # store user's city name
    context.user_data["initial_city_name"] = user_input
    # ask user which time they want to convert from
    await update.message.reply_text(
        "Please enter the time you want to convert using the format 'hh:mm AM/PM City'"
    )
    return TIME


# send a typing indicator in the chat
@send_typing_action
async def handle_time(update, context):
    user_input = update.message.text
    initial_city_name = context.user_data.get("initial_city_name")

    doc = nlp(user_input)

    # Extract time and city from user input using spaCy NLP
    time_string = None
    conversion_city_name = None

    for token in doc.ents:
        if token.label_ == "TIME":
            time_string = token.text
        elif token.label_ == "GPE":
            conversion_city_name = token.text

    # Make sure both time and conversion city are present
    if not time_string or not conversion_city_name:
        await update.message.reply_text(
            "Sorry, I couldn't recognize the time and city. Please try again with a valid format."
        )
        return

    # Parse the datetime from the time string using dateparser
    parsed_datetime = dateparser.parse(time_string)

    # Make sure datetime parsing was successful
    if not parsed_datetime:
        await update.message.reply_text(
            "Sorry, I couldn't parse the time. Please try again with a valid format."
        )
        return

    # Get the initial timezone and conversion timezone
    initial_timezone = get_timezone_from_location(initial_city_name)
    conversion_timezone = get_timezone_from_location(conversion_city_name)

    # Make sure timezones were found for both cities
    if not initial_timezone or not conversion_timezone:
        await update.message.reply_text(
            "Sorry, I couldn't recognize the timezones for the cities. Please try again with valid city names."
        )
        return

    # Convert the parsed datetime to the conversion city's timezone
    conversion_datetime = pytz.timezone(conversion_timezone).localize(parsed_datetime)

    # Convert the conversion datetime to the initial city's timezone
    initial_datetime = conversion_datetime.astimezone(pytz.timezone(initial_timezone))

    # Format the time strings
    conversion_time_string = conversion_datetime.strftime("%I:%M %p")
    initial_time_string = initial_datetime.strftime("%I:%M %p")

    response = f"The time in {initial_city_name} is {initial_time_string}."

    await update.message.reply_text(
        response,
        reply_markup=generate_markup(4),
    )
    return NEW_CITY


async def get_time_difference(update, context):
    user_text = update.message.text
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
    await update.message.reply_text(
        message,
        reply_markup=generate_markup(4),
    )
    return NEW_CITY


# function to get timezone details
# given a timezone name, return its offset from UTC and abbreviation
def get_timezone_details(timezone_name):
    timezone_offset = datetime.datetime.now(pytz.timezone(timezone_name)).strftime("%z")
    timezone_offset_formatted = f"{timezone_offset[:-2]}:{timezone_offset[-2:]}"
    timezone_abbr = (
        pytz.timezone(timezone_name).localize(datetime.datetime.now()).strftime("%Z")
    )
    return timezone_abbr, timezone_offset_formatted


# function to get timezone from location
# given a city name, return its timezone name
def get_timezone_from_location(city_name):
    geolocator = Nominatim(user_agent="timezone_bot")
    location = geolocator.geocode(city_name, timeout=10)
    if location is None:
        return None
    tf = TimezoneFinder()
    timezone_name = tf.timezone_at(lng=location.longitude, lat=location.latitude)
    return timezone_name


# function to get the current UTC time in a timezone
# given a timezone name, return the current UTC time
def get_current_utc_time(timezone_name):
    timezone = pytz.timezone(timezone_name)
    current_datetime = timezone.localize(datetime.datetime.now())
    utc_time = current_datetime.astimezone(pytz.utc)
    return utc_time.replace(tzinfo=None)


# function to get the current time in a timezone
# given a timezone name, return the current time in the specified timezone as a formatted string
def get_current_time_in_timezone(timezone_name):
    timezone = pytz.timezone(timezone_name)
    city_time = datetime.datetime.now(timezone).strftime("%H:%M:%S %d.%m.%Y")
    return city_time


def main():
    # set Telegram bot
    application = ApplicationBuilder().token(TELEGRAM_API_TOKEN).build()

    # create a conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
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
    )
    application.add_handler(conv_handler)

    # start the Telegram bot
    application.run_polling()


if __name__ == "__main__":
    main()
