import datetime
import json
from geopy.geocoders import Nominatim
import logging
from timezonefinder import TimezoneFinder
import pytz
import spacy


# import the required Telegram modules
from telegram import Update
from telegram.ext import (
    CommandHandler,
    ApplicationBuilder,
    ContextTypes,
    filters,
    MessageHandler,
    CallbackContext,
)

# import the Telegram API token from config.py
from config import TELEGRAM_API_TOKEN

TELEGRAM_API_TOKEN = TELEGRAM_API_TOKEN

# enable logging
logging.basicConfig(level=logging.INFO)

user_timezone = None


# this handler responds when the /start command is used for the first time
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open("en_strings.json", "r") as f:
        strings = json.load(f)
    welcome_message = strings["welcome_message"]
    await update.message.reply_text(welcome_message)


# load pre-trained spacy model
nlp = spacy.load("en_core_web_sm")


# identify entities (location, date, time) in user input
def extract_entities(text):
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ in ["GPE", "LOC"] and "city" in ent.text.lower():
            return ent.text.strip()
    return None


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # get the text from the message sent by the user
    user_text = update.message.text
    # use spaCy to extract the city name from the user's message
    city_name = extract_city_name(user_text)
    # call get_user_timezone with the city_name as a parameter
    timezone_name = await get_user_timezone(update, context, city_name)
    # reply with the user's timezone
    await update.message.reply_text(f"Your timezone is {timezone_name}")


async def get_user_timezone(
    update: Update, context: ContextTypes.DEFAULT_TYPE, city_name: str
):
    geolocator = Nominatim(user_agent="timezone_bot")
    location = geolocator.geocode(city_name, timeout=10)
    tf = TimezoneFinder()
    timezone_name = tf.timezone_at(lng=location.longitude, lat=location.latitude)
    return timezone_name


async def get_time_in_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    geolocator = Nominatim(user_agent="timezone_bot")
    location = geolocator.geocode(city_name, timeout=10)
    timezone = get_user_timezone(city_name)
    city_time = datetime.datetime.now(pytz.timezone(timezone))
    return city_time.strftime("%Y-%m-%d %H:%M:%S")


async def convert_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from_tz = pytz.timezone(from_timezone)
    to_tz = pytz.timezone(to_timezone)
    from_dt = from_tz.localize(datetime.datetime.strptime(time, "%Y-%m-%d %H:%M:%S"))
    to_dt = from_dt.astimezone(to_tz)
    return to_dt.strftime("%Y-%m-%d %H:%M:%S")


# entry point for the bot's functionality
async def process_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # extract entities from user input using spacy
    entities = extract_entities(input_str)

    if "GPE" in entities:
        # get current time in requested city
        city_time = get_city_time(entities["GPE"])
        return f"The current time in {entities['GPE']} is {city_time}"
    else:
        # handle invalid input
        return "I'm sorry, I couldn't understand your request."

    global user_timezone

    # parse the user input message
    user_input = update.message.text
    chat_id = update.message.chat_id

    # code to handle the user input and extract the required functionality

    if input_str == "what's my timezone":
        if user_timezone is None:
            # get user timezone and store in global var
            pass

    elif user_input.startswith("what's the time in "):
        # extract the city name from the user input
        city_name = user_input.replace("what's the time in ", "").strip()
        city_time = get_time_in_city(city_name)
        await bot.send_message(
            chat_id=chat_id, text=f"The time in {city_name} is {city_time}"
        )

    elif input_str == "what's the time difference between New York and Mumbai":
        # calculate the time difference between the two cities
        pass

    elif user_input.startswith("convert "):
        # parse the input to get the time, from timezone and to timezone
        converted_time = convert_time(time, from_timezone, to_timezone)
        await bot.send_message(
            chat_id=chat_id, text=f"The time in {to_timezone} is {converted_time}"
        )

    elif input_str.startswith("what's the time in Sydney at "):
        # parse the input to get the date & time
        # calculate the time in Sydney for the given date & time
        pass

    else:
        # handle invalid user inputs
        pass


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command.",
    )


def main():
    # set Telegram bot
    application = ApplicationBuilder().token(TELEGRAM_API_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start))
    application.add_handler(MessageHandler(filters.COMMAND, unknown))

    # start the Telegram bot
    application.run_polling()


if __name__ == "__main__":
    main()
