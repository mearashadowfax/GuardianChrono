# standard Library Imports
import asyncio  # asynchronous programming support
import json  # JSON serialization and deserialization
import logging  # logging utility
import datetime  # date and time manipulation
from decimal import Decimal  # decimal arithmetic
from functools import wraps  # function decorator utility
import random  # random number generation

# third-Party Imports
import pytz  # timezone manipulation
from geopy.geocoders import Nominatim  # geocoding service
from timezonefinder import TimezoneFinder  # timezone lookup

# import the required Telegram modules
from telegram.constants import ChatAction
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    ApplicationBuilder,
    filters,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
)

# import the Telegram API token from config.py
from config import TELEGRAM_API_TOKEN

# enable logging
logging.basicConfig(level=logging.INFO)

# initialize the geocoder and timezone finder
geolocator = Nominatim(user_agent="timezone_converter")
timezone_finder = TimezoneFinder()

# declare a global variable to hold the timer object
timeout_timer = None

# declare constants for ConversationHandler
CITY, NEW_CITY, CONVERSION, DIFFERENCE, TIME = range(5)
START_OVER = "start_over"

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
        # Return a markup with the first three buttons only
        return InlineKeyboardMarkup(
            [reply_markup[0][:num_buttons]] + [reply_markup[1][:1]]
        )
    else:
        # return the full markup with all four buttons
        return InlineKeyboardMarkup(reply_markup)


# handler function for /start command
async def start_conversation(update, context):
    with open("en_strings.json", "r") as f:
        strings = json.load(f)

    # set conversation flag to True
    context.user_data["conversation_active"] = True

    # use the global keyword to access the global variable
    global timeout_timer

    # if we're starting over we don't need to send a welcome_message
    if context.user_data.get(START_OVER):
        questions = [
            "What do you want to do next?",
            "What would you like to do next?",
            "How can I assist you further?",
            "Is there anything else I can help you with?",
            "What is your next query?",
            "Do you have any other requests?",
        ]
        random_question = random.choice(questions)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=random_question,
            reply_markup=generate_markup(4),
        )
    else:
        welcome_message = strings["welcome_message"]
        await update.message.reply_text(welcome_message, parse_mode="HTML")
        await update.message.reply_text("Please enter a city name:")

    # reset the START_OVER flag to False
    context.user_data[START_OVER] = False

    # cancel any previous timeout timers and start a new one
    if timeout_timer is not None:
        timeout_timer.cancel()
    timeout_timer = asyncio.create_task(timeout(update, context))
    context.user_data["timeout_timer"] = timeout_timer

    return CITY


async def timeout(update, context):
    await asyncio.sleep(300.0)  # Wait for 300 seconds

    # generate an inline keyboard with a button that starts a new conversation
    button = InlineKeyboardButton(text="Start Over", callback_data="start_over")
    keyboard = InlineKeyboardMarkup([[button]])

    messages = [
        "Sorry, it seems like our conversation timed out. Please tap below to start a new one.",
        "It appears that your session has expired. Kindly tap below to initiate a new one.",
        "It looks like our conversation has timed out. Tap the button below to start a new one.",
    ]
    random_message = random.choice(messages)
    # send the message with the inline keyboard
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=random_message, reply_markup=keyboard
    )
    # set conversation_active flag to False
    context.user_data["conversation_active"] = False
    # end conversation
    return ConversationHandler.END


async def start_conv_handler(update, context):
    callback_query = update.callback_query
    context.user_data.clear()
    if callback_query.data == "start_over":
        # set a flag to indicate that the conversation has been restarted
        context.user_data[START_OVER] = True

        # start a new conversation
        await start_conversation(update, context)
    await callback_query.answer()


# send a typing indicator in the chat
@send_typing_action
# handler function for user input city name
async def handle_city(update, context):
    # check if conversation is still active
    if not context.user_data.get("conversation_active"):
        return
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
async def handle_new_city(update, context):
    # check if conversation is still active
    if not context.user_data.get("conversation_active"):
        return
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
    formatted_city_time = city_time_obj.strftime("%I:%M %p on %B %dth, %Y")
    reply1 = f"The time in {city_name} right now is {formatted_city_time}."
    "Timezone: {timezone_abbr} ({timezone_offset_formatted})"
    reply2 = f"It's currently {formatted_city_time} in {city_name}."
    "Timezone: {timezone_abbr} ({timezone_offset_formatted})"
    reply = random.choice([reply1, reply2])
    await update.message.reply_text(
        reply,
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
    # check if conversation is still active
    if not context.user_data.get("conversation_active"):
        return
    user_input = update.message.text
    # store user's city name
    context.user_data["destination_city_name"] = user_input
    # ask user which time they want to convert from
    await update.message.reply_text(
        "Please enter the time and the city you are converting from using the format 'HH:MM AM/PM City'"
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
    context.user_data[START_OVER] = True
    await start_conversation(update, context)


async def get_time_difference(update, context):
    # check if conversation is still active
    if not context.user_data.get("conversation_active"):
        return
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
    context.user_data[START_OVER] = True
    await start_conversation(update, context)


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


def convert_time(source_time, initial_timezone, destination_timezone):
    # parse the source time using a specific format
    source_dt = datetime.datetime.strptime(source_time, "%I:%M %p")

    # get the initial and destination timezones
    initial_tz = pytz.timezone(initial_timezone)
    destination_tz = pytz.timezone(destination_timezone)

    # combine the source date with the source time
    source_date = datetime.datetime.now().date()
    source_dt = initial_tz.localize(
        datetime.datetime.combine(source_date, source_dt.time())
    )

    # convert the source time to the destination timezone
    destination_dt = source_dt.astimezone(destination_tz)

    # format the destination time as a string with AM/PM indicator
    destination_time = destination_dt.strftime("%I:%M %p")

    return destination_time


def main():
    # set Telegram bot
    application = ApplicationBuilder().token(TELEGRAM_API_TOKEN).build()

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
            ),
            CommandHandler("timeout", timeout),
        ],
    )
    # add ConversationHandler to application that will be used for handling updates
    application.add_handler(conv_handler)

    # add a callback query handler for when the user selects to start over
    application.add_handler(
        CallbackQueryHandler(start_conv_handler, pattern="^(start_over)$")
    )
    # start the Telegram bot
    application.run_polling()


if __name__ == "__main__":
    main()
