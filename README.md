# Jeraptha_V2 <img src="https://github.com/user-attachments/assets/fedcb240-d190-47c0-9be8-5c20cb2ce0ce" width="75" height="75">

## Table of Contents

1. [Introduction](#introduction)
2. [Features](#features)
3. [Games and Commands](#games-and-commands)

## Introduction

Welcome to Jeraptha_V2, a Discord bot that adds a virtual economy to your server! You can make wagers with other users, play fun games to earn more coins and use your coins to buy rewards. 

The name is a reference to the Expeditionary Force book series by Craig Alanson: the Jeraptha are a beetle-like species that have a culture heavily focused on gambling.
Built with Python using the [Discord API](https://discord.com/developers/docs/intro).

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
