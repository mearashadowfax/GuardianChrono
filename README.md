# GuardianChrono Telegram Bot

![GuardianChronoPoster](https://github.com/mearashadowfax/GuardianChrono/assets/125820963/47d384e7-8f8e-49bf-9b39-2b2ef1d4c486)

GuardianChrono is a Telegram bot built with Python's python-telegram-bot library. It is designed to provide a range of useful time-related features, including obtaining the current time and timezone of any city, converting timezones, and calculating the time difference between cities. To use the bot, simply send a message with the name of a city you're interested in, and GuardianChrono will promptly respond with the current local time and timezone.

## Getting started
To get started with this project, follow these steps:  
1. Create a new Telegram Bot and obtain a token following the [instructions](https://core.telegram.org/bots#how-do-i-create-a-bot)
2. Clone this repository and navigate to the project directory
3. Install the required dependencies using `pip install -r requirements.txt`
4. Create a `config.py` file in the project directory and define a variable named `TELEGRAM_API_TOKEN` with your Telegram Bot token. The contents of your `config.py` file should look like this:
```
TELEGRAM_API_TOKEN = 'YOUR_TELEGRAM_API_TOKEN'
```
5. Run `python3 bot.py` script
6. Start the bot in Telegram by searching for the bot name and clicking on the `start` button

## Usage
This Telegram bot offers the following features:  
1. Discover Local Time: Type the name of a city to get the current local time.
2. Get City Timezone: Enter a city name to retrieve its timezone.
3. Convert Timezone: Convert a specific time to your local timezone.  
4. Compare Time Difference: Easily compare the time difference between two cities.

To learn more about the bot's features, visit the bot at [GuardianChrono](https://t.me/GuardianChronoBot).
## Contributing
If you'd like to contribute to this project, feel free to fork the repository and submit a pull request. You can also create an issue to report bugs or suggest new features.

## License
This project is licensed under the MIT License - see the [LICENSE.md](https://github.com/mearashadowfax/GuardianChrono/blob/main/LICENSE) file for details.
