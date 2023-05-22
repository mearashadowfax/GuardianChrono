# GuardianChrono Telegram Bot
GuardianChrono is a practical Telegram bot project built on Python's `python-telegram-bot` library, designed to help users access a range of useful time-related features. With GuardianChrono, you can easily obtain the current time and timezone of any city, convert timezones, and calculate the time difference between cities. To use the bot, simply send a message with the name of a city you're interested in, and GuardianChrono will promptly respond with the current local time and timezone.

## Getting started
To get started with this project, you'll need to do the following:  
1. Set up a new Python environment with your preferred tools
2. Install the `python-telegram-bot` package using pip:
```
pip install python-telegram-bot
```
3. Download and install the spaCy model for your preferred language to detect named entities such as city names in the text: 
```
python3 -m spacy download en_core_web_sm
```
4. Clone this repository and navigate to the project directory
5. Create a new Telegram Bot and obtain a token following the [instructions](https://core.telegram.org/bots#how-do-i-create-a-bot)
6. Add your Telegram Bot token to the `config.py` file
7. Run the bot with the command `python3 bot.py`

You can then interact with the bot in a Telegram chat.

## Usage
This Telegram bot offers the following features:  
1. Discover Local Time: Type the name of a city, and bot will instantly reply with the current local time in that city.  
2. Get City Timezone: Enter the name of a city, and bot will indicate the name of its timezone.  
3. Convert Timezone: Type a time and the name of a city to convert the time to your local timezone.  
4. Compare Time Difference: Easily compare the time difference between any two cities.  

You can use any of these features by tapping the corresponding button in a chat to get quick and easy access to time zone information.
## Contributing
If you'd like to contribute to this project, feel free to fork the repository and submit a pull request. You can also create an issue to report bugs or suggest new features.

## License
This project is licensed under the MIT License - see the [LICENSE.md](https://github.com/mearashadowfax/GuardianChrono/blob/main/LICENSE) file for details.
