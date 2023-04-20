import json
import pytz
import spacy
import logging
import datetime
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

# import the required Telegram modules
from telegram import Update
from telegram.ext import (
    CommandHandler,
    ApplicationBuilder,
    ContextTypes,
    filters,
    MessageHandler,
    ConversationHandler,
)

# import the Telegram API token from config.py
from config import TELEGRAM_API_TOKEN

TELEGRAM_API_TOKEN = TELEGRAM_API_TOKEN

# enable logging
logging.basicConfig(level=logging.INFO)

# load pre-trained spacy model
nlp = spacy.load("en_core_web_sm")

# declare constants for ConversationHandler
CITY, NEW_CITY = range(2)


# this handler responds when the /start command is used
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open("en_strings.json", "r") as f:
        strings = json.load(f)
    welcome_message = strings["welcome_message"]
    await update.message.reply_text(welcome_message)
    # ask the user for a city name
    await update.message.reply_text("Please enter a city name.")
    # return CITY state to indicate that the next message should be a city name
    return CITY


# extracts entities (location, date, time) in the user input using spaCy
async def extract_entities(text):
    doc = nlp(text)
    entities = {}
    for ent in doc.ents:
        if ent.label_ in ["GPE", "LOC"] and "city" in ent.text.lower():
            entities[ent.label_] = ent.text.strip()
    return entities


# handles incoming messages from the user
async def handle_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    timezone = await get_user_timezone(update, context, user_text)
    if timezone is None:
        await update.message.reply_text(
            f"I'm sorry, I couldn't recognize {user_text} as a city."
        )
    else:
        city_time = datetime.datetime.now(pytz.timezone(timezone))
        await update.message.reply_text(
            f"The time in {user_text} is {city_time.strftime('%Y-%m-%d %H:%M:%S')}.\n\nIf you want to check "
            f"another city, please enter its name."
        )
        # change the current state to NEW_CITY to indicate that we're waiting for a new city name
        return NEW_CITY


async def handle_new_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    timezone = await get_user_timezone(update, context, user_text)
    if timezone is None:
        await update.message.reply_text(
            f"I'm sorry, I couldn't recognize {user_text} as a city."
        )
    else:
        city_time = datetime.datetime.now(pytz.timezone(timezone))
        await update.message.reply_text(
            f"The time in {user_text} is {city_time.strftime('%Y-%m-%d %H:%M:%S')}.\n\nIf you want to check "
            f"another city, please enter its name."
        )
    # stay in the NEW_CITY state
    return NEW_CITY


async def get_user_timezone(
    update: Update, context: ContextTypes.DEFAULT_TYPE, city_name: str
):
    try:
        geolocator = Nominatim(user_agent="timezone_bot")
        location = geolocator.geocode(city_name, timeout=10)
        tf = TimezoneFinder()
        timezone_name = tf.timezone_at(lng=location.longitude, lat=location.latitude)
        return timezone_name
    except:
        return None


#  gets the current time in the given city and returns it as a string
async def get_time_in_city(
    update: Update, context: ContextTypes.DEFAULT_TYPE, city_name: str
):
    timezone = await get_user_timezone(update, context, city_name=city_name)
    city_time = datetime.datetime.now(pytz.timezone(timezone))
    return city_time.strftime("%Y-%m-%d %H:%M:%S")


# converts time from one timezone to another and returns it as a string
async def convert_time(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    time: str,
    from_timezone: str,
    to_timezone: str,
):
    from_tz = pytz.timezone(from_timezone)
    to_tz = pytz.timezone(to_timezone)
    from_dt = from_tz.localize(datetime.datetime.strptime(time, "%Y-%m-%d %H:%M:%S"))
    to_dt = from_dt.astimezone(to_tz)
    return to_dt.strftime("%Y-%m-%d %H:%M:%S")


def main():
    # set Telegram bot
    application = ApplicationBuilder().token(TELEGRAM_API_TOKEN).build()

    # create a conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CITY: [MessageHandler(filters.TEXT, handle_city)],
            NEW_CITY: [MessageHandler(filters.TEXT, handle_new_city)],
        },
        fallbacks=[],
    )
    application.add_handler(conv_handler)

    # start the Telegram bot
    application.run_polling()


if __name__ == "__main__":
    main()
