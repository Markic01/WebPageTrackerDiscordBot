
# Discord Webpage Change Tracker Bot

This is a Discord bot that tracks changes on static webpages and notifies users when the content has been updated. It allows users to follow and unfollow webpages and receive notifications via Discord when the content of these pages changes.

## Features

- `!follow <url>`: Follow a webpage. The bot will notify you when the content of the page changes.
- `!unfollow <url>`: Unfollow a webpage.
- `!pages`: List the webpages you are currently following.
- `!hello`: Greets the user.
- `!help`: Provides information on the bot’s commands.

## Requirements

- A MongoDB instance to store the data, either running locally or through a cloud service (e.g., MongoDB Atlas).
- Python 3.7 or higher.
- The following environment variables:
  - `BOT_TOKEN`: Your Discord bot token.
  - `DB_URI`: The MongoDB connection URI. Use this to connect to either a local or cloud MongoDB instance.
  - `DB_NAME`: The name of the database used for storing URLs and follow information.

## Installation and Setup

1. Clone this repository and navigate to the project directory.
2. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up the following environment variables in your environment:
   - `BOT_TOKEN`: Your Discord bot token.
   - `DB_URI`: The MongoDB connection URI (can point to a locally running MongoDB or a cloud instance).
   - `DB_NAME`: The name of the database.
   
   Example:

   ```bash
   export BOT_TOKEN="your-discord-bot-token"
   export DB_URI="mongodb://localhost:27017/"
   export DB_NAME="your-database-name"
   ```

4. Run the bot:

   ```bash
   python bot.py
   ```

## How It Works

- When the bot starts, it checks the webpages in the database periodically.
- If any webpage content has changed, users following that page will receive a direct message on Discord notifying them of the update.

## MongoDB Schema

- **urls** collection: Stores the URLs and their content hash.
  - Fields: 
    - `url`: The webpage URL.
    - `content_hash`: The hashed content of the webpage.
- **follows** collection: Stores which user follows which URL.
  - Fields:
    - `user_id`: The Discord user ID.
    - `url_id`: The ID of the URL in the `urls` collection.

## Contributing

Feel free to open issues or submit pull requests for improvements or bug fixes.

## License

This project is licensed under the MIT License.
