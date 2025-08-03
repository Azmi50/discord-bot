# 🎮 Discord Tournament Bot

A simple Discord bot that manages 1v1-style tournaments, tracks match results, and displays outcomes using images.

---

## 🚀 Features

- Slash command `/match @player1 @player2 winner`
- Automatically generates match result images
- Uses custom fonts (you can modify them)
- Simple setup and lightweight

---

## 🛠 Tech Stack

- Python 3
- [discord.py](https://github.com/Rapptz/discord.py)
- [Pillow (PIL)](https://pillow.readthedocs.io/en/stable/)
- [python-dotenv](https://pypi.org/project/python-dotenv/)

---

## ⚙️ Setup Instructions

1. **Clone the repo**
   ```bash
   git clone https://github.com/yourusername/tournament-discord-bot.git
   cd tournament-discord-bot

   
### 2.Install dependencies

    bash

    pip install -r requirements.txt

### 3.Add your bot token

     Create a .env file and paste:



  DISCORD_TOKEN=your_token_here
### 4.Run the bot


   python bot.py


### ⚠️ Disclaimer
This bot is for personal use or small community tournaments.
Do not expose your token. Keep .env private and listed in .gitignore.
