# Jeraptha_V2 <img src="https://github.com/user-attachments/assets/fedcb240-d190-47c0-9be8-5c20cb2ce0ce" width="75" height="75">

## Table of Contents

1. [Introduction](#introduction)
2. [Features](#features)
3. [Games and Commands](#games-and-commands)
4. [Database and Data Handling](#database-and-data-handling)
5. [Setup Guide](#setup-guide)
6. [Contributing](#contributing)
7. [License](#license)
8. [Contact](#contact)

## Introduction

Welcome to Jeraptha_V2, a Discord bot that adds a virtual economy to your server! You can make wagers with other users, play fun games to earn more coins and use your coins to buy rewards. 

The name is a reference to the Expeditionary Force book series by Craig Alanson: the Jeraptha are a beetle-like species that have a culture heavily focused on gambling.


Built with [Pycord](https://github.com/Pycord-Development/pycord) in Python using the [Discord API](https://discord.com/developers/docs/intro).
The data is stored in a MongoDB database using the [PyMongo](https://pymongo.readthedocs.io/en/stable/) library.

## Features

- 💰 Make wagers with other users
- 🎮 Daily games (Wordle-like Beetdle)
- 🎲 Gambling games (Blackjack, Roulette, Chinchirorin)
- 📊 Virtual economy with leaderboards and rewards

## Wagers
Users can create and bet in wagers, using the coins they earned.
- `/wager start [title] [option_list] [duration]`: Creates a wager with the given title and possible betting options. Users can place bets until the end of the defined duration.
- `/wager bet [wager_id] [bet_option] [bet_amount]`: Bet on a bet wager's option. Users can only bet on one option per wager, but they can raise it later.
- `/wager settle [wager_id] [winning_option]`: Settle a wager by choosing the winning option. Only the wager's creator or admins can do this command.
- `/wager cancel [wager_id]`: Cancel a wager, returning all bets. Only the wager's creator or admins can do this command.
- `/wager info [wager_id]`: Get the info on a wager.
- `/wager list`: Get the list of wagers.


## Games

This bot includes several mini-games that can be played directly in your Discord server. Each game has its own set of commands to start, play, and manage it. Here's a breakdown:

### 1. **Beetdle**

Test your English proficiency with this Wordle-like game!

Players will need to guess a word from a dictionary database. With each guess, the correct letters and positions will be displayed to the user in order to help find the selected word.

The first word of the day is the same for every user in the server, and it's worth extra coins. The bot tracks correct answers and maintains a leaderboard.

- `/beetdle guess [your_guess]`: Starts a new Beetdle game or continues the current game.
- `/beetdle remind`: Remind yourself the previous guesses for the current word.
- `/leaderboard Beetdle Daily`: Display the total daily wins for each user.
- `/leaderboard Beetdle Total`: Display the total wins for each user.

### 2. **Roulette**

Classic european roulette game. Play alone or create a lobby with other users.

- `/roulette start [betting_time]`: Start a new lobby of roulette. You may select the time for making bets.
- `/roulette bet [amount] [option] [sub_option]`: Insert your bet amount, your bet option (color, dozen, number...) and corresponding sub option (red, 2nd dozen, 14...).

### 3. **Blackjack**

Standard blackjack game. Play alone or create a lobby with other users.
- `/blackjack start [wait_time]`: Start a new lobby of blackjack. You may select the time for making bets.
- `/blackjack bet [amount]`: Insert your bet amount.
- In your turn, you can make the following commands, if they are available: `hit`, `stand`, `double`, `split`.

### 4. **Chinchirorin**

A dice game in which you roll 3 dice and try to get a scoring hand. 

- `/chinchirorin play [bet_amount]`: Play a round of Chinchirorin and place your bet.
- `/chinchirorin ruleset`: Check the rules of the game.

## Rewards, Leaderboards and other commands

### Rewards
#### Daily
- `/daily`: Once per day, gives a random amount of coins. 

#### 8 Ball
- `/8ball roll [question]`: Pay to ask a question to the magic 8 ball and get a random answer from a list.
- `/8ball add [answer]`: Pay to add an answer to the magic 8 ball answer list.

#### Fortune Cookie
- `/fortune_cookie wisdom`: Pay to receive a random quote from a list.
- `/fortune_cookie add [wisdom]`: Pay to add a quote to the fortune cookie wisdom list.

#### Lootbox
 - `/lootbox`: Pay coins to get a random reward: a coin bag, shake the 8-ball, open a fortune cookie or get a refund. More rewards can be added.
   
#### Punishments
- `/punish [punishment] [target_user]`: Pay coins to punish a user: change their nickname, mute them for 30 seconds or disconnect them from the voice chat.

### Leaderboards
- `/leaderboard [option]`: Check the leaderboard for: most wagers won, most coins in wallet, total earned from bets, best profit/loss from bets and most games won.

### Help
- `/help [module]`: Description of the commands available for each module.

---

## Database and Data Handling

This bot uses a database to manage game data, user statistics, and server-specific settings. Here's how the data is structured and how you can set it up:

### 1. **Database Type**
- The bot uses [SQLite/MySQL/PostgreSQL] for data persistence. You can change the database type in the configuration file if needed.

### 2. **Data Stored**
- **User Data**: Stores user IDs, usernames, and game statistics like wins, losses, and leaderboards.
- **Game Data**: Tracks ongoing games, such as current game state, player turns, and scores.
- **Server Settings**: Each server can have customized settings like command prefixes and bot behavior.

### 3. **Database Setup**

1. **For SQLite** (default):
    - The bot will automatically create an `sqlite.db` file in the root directory to store data.
    - No additional setup is required unless you want to change the database type.

2. **For MySQL/PostgreSQL**:
    - Update the `.env` file with your database credentials:

    ```env
    DB_TYPE=mysql
    DB_HOST=localhost
    DB_USER=root
    DB_PASSWORD=yourpassword
    DB_NAME=yourbotdb
    ```

    - Ensure your MySQL/PostgreSQL server is running and the database is created.

3. **Migrations**:
    - The bot comes with built-in migrations to set up the necessary tables. Run:

    ```bash
    npm run migrate  # For Node.js
    # or
    python manage.py migrate  # For Python
    ```

4. **Backup and Restore**:
    - For backup, export the database to a `.sql` or `.db` file.
    - For restoring, import the file back into your database server.

---

## Setup Guide

Follow these steps to set up the bot on your Discord server:

### Requirements

- **Node.js** or **Python**
- **Discord Bot Token** (from [Discord Developer Portal](https://discord.com/developers/applications))
- **Database Server** (for MySQL/PostgreSQL setups)

### Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/yourusername/yourbot.git
    cd yourbot
    ```

2. Install the dependencies:

    **For Node.js**:

    ```bash
    npm install
    ```

    **For Python**:

    ```bash
    pip install -r requirements.txt
    ```

3. Create a `.env` file with the following content:

    ```env
    DISCORD_TOKEN=your_bot_token_here
    PREFIX=!
    DB_TYPE=sqlite  # Change to mysql or postgres if needed
    ```

4. Start the bot:

    **For Node.js**:

    ```bash
    npm start
    ```

    **For Python**:

    ```bash
    python bot.py
    ```

5. **Invite the bot** to your server using the following link:

    ```url
    https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&scope=bot&permissions=8
    ```

---

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository.
2. Create a branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -m 'Add your feature'`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a pull request.

---

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/yourusername/yourbot/blob/main/LICENSE) file for details.

---

## Contact

- Discord: [Join Our Server](https://discord.gg/your-invite-link)
- Email: your-email@example.com

