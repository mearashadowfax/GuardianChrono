# standard Library Imports
import asyncio  # asynchronous programming support
import datetime  # date and time manipulation
from functools import wraps  # function decorator utility

# import the required Telegram modules
from telegram.constants import ChatAction
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# third-Party Imports
import pytz  # timezone manipulation
from geopy.geocoders import Nominatim  # geocoding service
from timezonefinder import TimezoneFinder  # timezone lookup


# define the send_action decorator
def send_action(action, delay=0.5):
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


# set the aliases with custom delays
send_typing_action = send_action(
    ChatAction.TYPING, delay=0.5
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

    # define the questions list globally


questions = [
    "How can I assist you? Check the time in cities, convert timezones, or compare time differences:",
    "Convert time, check time in cities, or calculate time differences. What would you like?",
    "Is there a specific city you'd like to know the time for, or do you have other questions in mind?",
    "What's your next time-related request? Time in cities, timezone conversion, or time difference?",
    "City time, timezone conversion, or time difference? Your choice:",
    "Time in a city, timezone conversion, or time difference? Let me know:",
    "Explore city time, timezone conversion, or time difference. What's your pick?",
]


# function to get timezone details
# given a timezone name, return its offset from UTC and abbreviation
def get_timezone_details(timezone_name):
    timezone_offset = datetime.datetime.now(pytz.timezone(timezone_name)).strftime("%z")
    timezone_offset_formatted = f"{timezone_offset[:-2]}:{timezone_offset[-2:]}"
    timezone_abbr = (
        pytz.timezone(timezone_name).localize(datetime.datetime.now()).strftime("%Z")
    )
    return timezone_abbr, timezone_offset_formatted


# initialize the geocoder and timezone finder
geolocator = Nominatim(user_agent="timezone_converter")
timezone_finder = TimezoneFinder()


# function to get timezone from location
# given a city name, return its timezone name
def get_timezone_from_location(city_name):
    location = geolocator.geocode(city_name, timeout=10)
    if location is None:
        return None
    tf = TimezoneFinder()
    timezone_name = tf.timezone_at(lng=location.longitude, lat=location.latitude)
    return timezone_name


# get the appropriate suffix for a day of the month
def get_day_suffix(day):
    if 10 <= day % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return suffix


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
