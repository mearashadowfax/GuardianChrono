import json
import pytz
import spacy
import logging
import datetime
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from decimal import Decimal

# import the required Telegram modules
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    ApplicationBuilder,
    ContextTypes,
    filters,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler
)

# import the Telegram API token from config.py
from config import TELEGRAM_API_TOKEN

TELEGRAM_API_TOKEN = TELEGRAM_API_TOKEN

# enable logging
logging.basicConfig(level=logging.INFO)

# load pre-trained spacy model
nlp = spacy.load("en_core_web_sm")

# declare constants for ConversationHandler
CITY, NEW_CITY, CONVERSION, DIFFERENCE = range(4)

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
markup = InlineKeyboardMarkup(reply_markup)


def generate_markup(num_buttons):
    if num_buttons == 3:
        # return a markup with only first three buttons
        return InlineKeyboardMarkup(
            [reply_markup[0][:num_buttons]] + [reply_markup[1][:1]]
        )
    else:
        # return the full markup with four buttons
        return InlineKeyboardMarkup(reply_markup)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open("en_strings.json", "r") as f:
        strings = json.load(f)
    welcome_message = strings["welcome_message"]
    await update.message.reply_text(welcome_message, parse_mode="HTML")
    await update.message.reply_text("Please enter a city name:")
    return CITY


# define function to handle city messages
async def handle_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    city_name = user_text.title() if user_text.islower() else user_text
    timezone_name = get_timezone_from_location(user_text)
    if timezone_name is None:
        await update.message.reply_text(
            "Sorry, I couldn't recognize that city. Please enter another city name:"
        )
        return CITY
    else:
        context.user_data["timezone_name"] = timezone_name
        context.user_data["city_name"] = city_name
        city_time = get_current_time_in_timezone(timezone_name)
        timezone_abbr, timezone_offset_formatted = get_timezone_details(timezone_name)
        context.user_data["timezone_abbr"] = timezone_abbr
        context.user_data["timezone_offset_formatted"] = timezone_offset_formatted
        city_time_obj = datetime.datetime.strptime(
            city_time, "%H:%M:%S %d.%m.%Y"
        ).replace(microsecond=0)
        formatted_city_time = city_time_obj.strftime("%I:%M %p on %B %dth, %Y")
        await update.message.reply_text(
            f"It's currently {formatted_city_time} in {city_name}. Timezone: {timezone_abbr} ({timezone_offset_formatted})"
            "\n\nWhat do you want to do next?",
            reply_markup=generate_markup(4),
        )
        return CITY


async def handle_new_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    city_name = user_text.title() if user_text.islower() else user_text
    timezone_name = get_timezone_from_location(user_text)
    if timezone_name is None:
        await update.message.reply_text(
            f"Sorry, I couldn't recognize {user_text} as a city. Please enter another city name:"
        )
        return NEW_CITY
    else:
        context.user_data["timezone_name"] = timezone_name
        context.user_data["city_name"] = city_name
        city_time = get_current_time_in_timezone(timezone_name)
        timezone_abbr, timezone_offset_formatted = get_timezone_details(timezone_name)
        context.user_data["timezone_abbr"] = timezone_abbr
        context.user_data["timezone_offset_formatted"] = timezone_offset_formatted
        city_time_obj = datetime.datetime.strptime(
            city_time, "%H:%M:%S %d.%m.%Y"
        ).replace(microsecond=0)
        formatted_city_time = city_time_obj.strftime("%I:%M %p on %B %dth, %Y")
        await update.message.reply_text(
            f"The time in {city_name} right now is {formatted_city_time}. Timezone: {timezone_abbr} ({timezone_offset_formatted})",
            reply_markup=generate_markup(4),
        )
        return NEW_CITY


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "new_city":
        await query.message.reply_text("Please enter a new city:")
        return NEW_CITY
    elif query.data == "conversion":
        await query.message.reply_text(
            "Please enter the time you want to convert using the format 'hh:mm AM/PM City':"
        )
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


async def handle_conversion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    time, city_name = extract_time_and_city(user_text)

    if time is None or city_name is None:
        await update.message.reply_text(
            "Sorry, the input format is invalid. Please try again."
        )
        return CONVERSION
    timezone_name = get_timezone_from_location(city_name)
    if timezone_name is None:
        await update.message.reply_text(
            f"Sorry, I couldn't recognize {city_name} as a city. Please try again."
        )
        return CONVERSION
    else:
        city_time = convert_time(
            time, timezone_name, context.user_data["timezone_name"]
        )
        context.user_data["conversion_time"] = city_time
        await update.message.reply_text(
            f"The time in {context.user_data['city_name']}({city_name}) is {time}."
            f"\nThe time in your timezone({context.user_data['timezone_name']}) is {city_time}."
            "\n\nDo you want to perform another operation?",
            reply_markup=generate_markup(4),
        )
        return NEW_CITY


async def handle_difference(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    city_name = user_text.title() if user_text.islower() else user_text
    try:
        timezone_name = get_timezone_from_location(user_text)
        city_time = get_current_time_in_timezone(timezone_name)
        context.user_data["difference_city_name"] = city_name
        context.user_data["difference_timezone_name"] = timezone_name
        context.user_data["difference_time"] = city_time
        await handle_difference_result(update, context)
    except ValueError:
        await update.message.reply_text(
            f"Sorry, I couldn't recognize {user_text} as a city. Please enter another city name:"
        )
        return DIFFERENCE


async def handle_difference_result(update, context):
    city_name_1 = context.user_data["city_name"]
    city_name_2 = context.user_data["difference_city_name"]
    difference_hours = get_time_difference_in_hours(
        context.user_data["difference_timezone_name"],
        context.user_data["difference_timezone_name"],
    )
    if difference_hours is None:
        await update.message.reply_text(
            f"Sorry, I could not determine the time difference between {city_name_1} and {city_name_2}.\n\nDo you "
            f"want to perform another operation?",
            reply_markup=generate_markup(4),
        )
        return CONVERSION
    abs_difference_hours = abs(difference_hours)
    if abs_difference_hours < 0.01:
        difference_text = "at the same time"
    elif difference_hours > 0:
        difference_text = f"{Decimal(abs_difference_hours):.2f} hours ahead"
    else:
        difference_text = f"{Decimal(abs_difference_hours):.2f} hours behind"
    await update.message.reply_text(
        f"The time difference between {context.user_data['city_name']} and {city_name_2} is {difference_text}.\n\nDo "
        f"you want to perform"
        f"another operation?",
        reply_markup=generate_markup(4),
    )
    return NEW_CITY


def extract_time_and_city(user_text):
    try:
        time, city_name = user_text.split(" ", 1)
        if not time.endswith(("am", "pm")):
            return None, None
        return time, city_name
    except ValueError:
        return None, None


def convert_time(time_string, from_timezone_name, to_timezone_name):
    from_timezone = pytz.timezone(from_timezone_name)
    to_timezone = pytz.timezone(to_timezone_name)
    time_obj = datetime.datetime.strptime(time_string, "%I:%M %p")
    loc_dt = from_timezone.localize(time_obj)
    utc_time = loc_dt.astimezone(pytz.utc)
    dest_dt = utc_time.astimezone(to_timezone)
    return dest_dt.strftime("%I:%M %p")


def get_timezone_details(timezone_name):
    timezone_offset = datetime.datetime.now(pytz.timezone(timezone_name)).strftime("%z")
    timezone_offset_formatted = f"{timezone_offset[:-2]}:{timezone_offset[-2:]}"
    timezone_abbr = (
        pytz.timezone(timezone_name).localize(datetime.datetime.now()).strftime("%Z")
    )
    return timezone_abbr, timezone_offset_formatted


def get_time_difference_in_hours(timezone_1: str, timezone_2: str) -> float:
    tz1 = pytz.timezone(timezone_1)
    tz2 = pytz.timezone(timezone_2)
    time1 = datetime.datetime.now(tz1)
    time2 = datetime.datetime.now(tz2)
    print(f"time1 ({timezone_1}): {time1}")
    print(f"time2 ({timezone_2}): {time2}")
    difference = (time2 - time1).total_seconds() / 3600.0
    print(difference)
    return round(difference, 2)


# define function to get timezone from the location
def get_timezone_from_location(city_name):
    geolocator = Nominatim(user_agent="timezone_bot")
    location = geolocator.geocode(city_name, timeout=10)
    if location is None:
        return None
    tf = TimezoneFinder()
    timezone_name = tf.timezone_at(lng=location.longitude, lat=location.latitude)
    return timezone_name


# define function to get the current time in a time zone
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
            DIFFERENCE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_difference)
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
