# GuardianChrono Telegram Bot
GuardianChrono is a simple Telegram bot project that utilizes Python and the `python-telegram-bot` library to provide users with a range of useful timezone-related functions. With GuardianChrono, you can easily find the timezone of any city around the world, convert timezones, and even calculate the time difference between cities. To get started, simply send the name of a city you're interested in and the bot will reply with the current local time and timezone there.

## Getting started
To get started with this project, you'll need to do the following:  
1. Set up a new Python environment with your preferred tools
2. Install the `python-telegram-bot` package using pip:
```
pip install python-telegram-bot
```
3. Download the spaCy model for your preferred language. For example, if you want to detect city names in English text, you can download the "en_core_web_sm" model:
```
python -m spacy download en_core_web_sm
```
4. Clone this repository and navigate to the project directory:
5. Create a new Telegram Bot and get a token. You can follow the instructions [here](https://core.telegram.org/bots#how-do-i-create-a-bot).
6. Add your Telegram Bot token to the `config.py` file.
7. Run the bot using the following command:
```
python bot.py
```
You can then interact with the bot in a Telegram chat.

## Usage
This Telegram bot offers the following features:  
1. Find local time: Send the name of a city and receive the current time in that city. 
2. Get city timezone: Send the name of a city and receive the name of the timezone for that city.
3. Convert time: Send a time and the name of a city to convert the time to the user's local timezone.
4. Compare time difference: Easily compare the time difference between two cities.

To use any of these features, simply tap the corresponding button. The bot will provide a quick and easy way to access time zone information.
## Contributing
If you'd like to contribute to this project, feel free to fork the repository and submit a pull request. You can also create an issue to report bugs or suggest new features.

## License
This project is licensed under the MIT License - see the [LICENSE.md](https://github.com/mearashadowfax/GuardianChrono/blob/main/LICENSE) file for details.