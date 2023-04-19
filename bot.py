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
    ConversationHandler,
)

# import the Telegram API token from config.py
from config import TELEGRAM_API_TOKEN

TELEGRAM_API_TOKEN = TELEGRAM_API_TOKEN

# enable logging
logging.basicConfig(level=logging.INFO)

user_timezone = None

# load pre-trained spacy model
nlp = spacy.load("en_core_web_sm")
# declare constants for ConversationHandler
(CITY,) = range(1)


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


# this handler is called when the user enters a city name
async def handle_city(update, context):
    await handle_message(update, context)
    return ConversationHandler.END


# extracts entities (location, date, time) in the user input using spaCy
async def extract_entities(text):
    doc = nlp(text)
    entities = {}
    for ent in doc.ents:
        if ent.label_ in ["GPE", "LOC"] and "city" in ent.text.lower():
            entities[ent.label_] = ent.text.strip()
    return entities


async def contains_city(update):
    user_text = await update.message.text
    entities = await extract_entities(user_text)
    return "GPE" in entities


# handles incoming messages from the user
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # get the text from the message sent by the user
    user_text = update.message.text
    # use extract_entities to get the city name and timezone from the user's message
    entities = await extract_entities(user_text)
    if "GPE" in entities:
        # call get_time_in_city with the city name as a parameter
        city_time = await get_time_in_city(update, context, entities["GPE"])
        if city_time is None:
            # handle case where city cannot be recognized
            await update.message.reply_text(
                f"I'm sorry, I couldn't recognize {entities['GPE']} as a city."
            )
        else:
            # reply with the time in the requested city
            await update.message.reply_text(
                f"The time in {entities['GPE']} is {city_time}"
            )
    else:
        # use get_user_timezone to get the timezone for the user input
        timezone = await get_user_timezone(update, context, user_text)
        if timezone is None:
            # handle invalid input
            await update.message.reply_text(
                "I'm sorry, I couldn't understand your request."
            )
        else:
            # get the current time in the requested city
            city_time = datetime.datetime.now(pytz.timezone(timezone))
            # reply with the time in the requested city
            await update.message.reply_text(
                f"The time in {user_text} is {city_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )


# this handler will trigger on any message containing a city name
city_handler = MessageHandler(filters.TEXT & filters.COMMAND, handle_message)


# gets the timezone for the given city name
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


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command.",
    )


def main():
    # set Telegram bot
    application = ApplicationBuilder().token(TELEGRAM_API_TOKEN).build()

    # create a conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CITY: [MessageHandler(filters.TEXT, handle_city)],
        },
        fallbacks=[MessageHandler(filters.COMMAND, unknown)],
    )
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("timezone", get_user_timezone))
    application.add_handler(CommandHandler("city", get_time_in_city))
    application.add_handler(CommandHandler("convert", convert_time))
    application.add_handler(MessageHandler(filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.COMMAND, unknown))

    # start the Telegram bot
    application.run_polling()


if __name__ == "__main__":
    main()
