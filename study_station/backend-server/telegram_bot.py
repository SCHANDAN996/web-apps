import telebot
from telebot.types import Poll
import os
import sys

# Import config
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from telegram_config import TELEGRAM_BOT_TOKEN, IS_TELEGRAM_ENABLED

# Import Flask app and Models to fetch questions
from app import app, db
from models import PracticeQuestion
import random

if not IS_TELEGRAM_ENABLED or TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    print("Telegram bot is not configured properly in telegram_config.py")
    print("Please set your TELEGRAM_BOT_TOKEN and set IS_TELEGRAM_ENABLED = True")
    sys.exit(1)

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "🎓 *Welcome to Study Station Bot!* 🎓\n\n"
        "I am your AI study companion. Here is what I can do:\n"
        "👉 Type /quiz to get a random practice question.\n"
        "👉 Type /latestjobs to see the latest job alerts (coming soon).\n\n"
        "Let's start learning! 🚀"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown")

@bot.message_handler(commands=['quiz'])
def send_quiz(message):
    with app.app_context():
        # Fetch a random question from the database
        questions = PracticeQuestion.query.all()
        if not questions:
            bot.reply_to(message, "Sorry, there are no questions available in the database right now.")
            return
            
        q = random.choice(questions)
        
        # Prepare options
        options = [q.option_a, q.option_b, q.option_c, q.option_d]
        
        # Determine correct option ID (0 to 3)
        correct_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
        correct_option_id = correct_map.get(q.correct_answer.upper(), 0)
        
        explanation = q.explanation if q.explanation else "Keep practicing on Study Station!"
        
        # Send Telegram Poll in Quiz Mode
        bot.send_poll(
            chat_id=message.chat.id,
            question=f"[{q.subject} - {q.class_level}] {q.question_text}",
            options=options,
            type="quiz",
            correct_option_id=correct_option_id,
            explanation=explanation,
            is_anonymous=False
        )

print("🤖 Study Station Quiz Bot is running...")
bot.infinity_polling()
