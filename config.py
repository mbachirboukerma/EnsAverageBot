import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
WEBHOOK_HOST = os.getenv('WEBHOOK_HOST', 'ens-average-bot-599688285140.europe-west1.run.app')
ADMIN_ID = int(os.getenv('ADMIN_ID', '5909420341'))

# Database Configuration
DB_PATH = os.getenv('DB_PATH', 'AverageBotDatabase.db')

# Channels Configuration
CHANNELS = ["@infotouchcommunity", "@hqlaptop"]

# Webhook Configuration
WEBHOOK_URL_PATH = BOT_TOKEN
WEBHOOK_URL = f"https://{WEBHOOK_HOST}/{WEBHOOK_URL_PATH}" 
