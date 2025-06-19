"""
Grade Calculator Bot - Main Application
A professional Telegram bot for calculating academic averages
"""

import asyncio
import logging
import os
import signal
import sys
from typing import Dict, List, Optional, Union
from contextlib import asynccontextmanager

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler
)
from telegram.error import TimedOut, Unauthorized, ChatMigrated
from flask import Flask, request
import threading
import time

# Import our custom modules
from config import BOT_TOKEN, CHANNELS, ADMIN_ID, WEBHOOK_URL
from database import DatabaseManager
from error_handler import safe_send_message, handle_telegram_errors, BotError
from grade_calculator import GradeCalculator, SubjectGrade, SubjectType

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Conversation states
class ConversationStates:
    SPECIALIZATION = 0
    LEVEL = 1
    SUB_LEVEL = 2
    FIRST = 3
    SECOND = 4
    TP = 5
    TD = 6
    NEXT_SUBJECT = 7

class GradeCalculatorBot:
    """Professional Grade Calculator Bot with advanced features"""
    
    def __init__(self):
        self.db = DatabaseManager("bot_newdata.db")
        self.calculator = GradeCalculator()
        self.app = Flask(__name__)
        self.application = None
        self._setup_flask_routes()
        
        # Rate limiting
        self.user_requests = {}
        self.rate_limit = 10  # requests per minute
        self.rate_limit_window = 60  # seconds
        
        # Performance monitoring
        self.request_count = 0
        self.start_time = time.time()
    
    def _setup_flask_routes(self):
        """Setup Flask routes for webhook"""
        @self.app.route(f'/{BOT_TOKEN}', methods=['POST'])
        def webhook():
            if self.application:
                update = Update.de_json(request.get_json(force=True), self.application.bot)
                asyncio.run(self.application.process_update(update))
            return 'ok'
        
        @self.app.route('/')
        def index():
            uptime = time.time() - self.start_time
            return {
                'status': 'running',
                'uptime': f"{uptime:.2f} seconds",
                'requests_processed': self.request_count,
                'active_users': self.db.get_visitor_count()
            }
        
        @self.app.route('/health')
        def health():
            return {'status': 'healthy'}
    
    def _rate_limit_check(self, user_id: int) -> bool:
        """Check if user has exceeded rate limit"""
        current_time = time.time()
        if user_id not in self.user_requests:
            self.user_requests[user_id] = []
        
        # Remove old requests outside the window
        self.user_requests[user_id] = [
            req_time for req_time in self.user_requests[user_id]
            if current_time - req_time < self.rate_limit_window
        ]
        
        # Check if user has exceeded limit
        if len(self.user_requests[user_id]) >= self.rate_limit:
            return False
        
        # Add current request
        self.user_requests[user_id].append(current_time)
        return True
    
    @handle_telegram_errors
    async def start_command(self, update: Update, context: CallbackContext) -> int:
        """Enhanced start command with rate limiting and better UX"""
        user_id = update.effective_user.id
        self.request_count += 1
        
        # Rate limiting
        if not self._rate_limit_check(user_id):
            await update.message.reply_text(
                "⚠️ You're making too many requests. Please wait a moment and try again.",
                parse_mode='HTML'
            )
            return ConversationHandler.END
        
        # Add visitor if not exists
        self.db.add_visitor(user_id)
        
        # Check subscription
        if not await self._check_subscription(update, context):
            return ConversationHandler.END
        
        # Welcome message with improved UX
        welcome_text = (
            "🎓 <b>Welcome to the Grade Calculator Bot!</b>\n\n"
            "I'll help you calculate your overall average grade for ENS.\n\n"
            "📚 <b>Available Specializations:</b>\n"
            "• Mathematics\n"
            "• Physics\n"
            "• Computer Science\n"
            "• Sciences\n"
            "• Music\n\n"
            "Please choose your specialization to begin:"
        )
        
        keyboard = [
            ["Mathematics", "Physics"],
            ["Computer Science", "Sciences"],
            ["Music"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='HTML')
        return ConversationStates.SPECIALIZATION
    
    async def _check_subscription(self, update: Update, context: CallbackContext) -> bool:
        """Check if user is subscribed to required channels"""
        user_id = update.effective_user.id
        
        try:
            for channel in CHANNELS:
                chat_member = await context.bot.get_chat_member(channel, user_id)
                if chat_member.status not in ["member", "administrator", "creator"]:
                    keyboard = [[InlineKeyboardButton(f"📢 Subscribe to {channel}", url=f"https://t.me/{channel[1:]}")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_text(
                        "❌ <b>Subscription Required</b>\n\n"
                        "You must subscribe to our channels to use this bot:\n\n"
                        f"1️⃣ {CHANNELS[0]}\n"
                        f"2️⃣ {CHANNELS[1]}\n\n"
                        "After subscribing, click /start again.",
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
                    return False
            return True
        except Exception as e:
            logger.error(f"Error checking subscription: {e}")
            return False
    
    async def choose_specialization(self, update: Update, context: CallbackContext) -> int:
        """Handle specialization selection with validation"""
        specialization = update.message.text.lower()
        
        # Map user-friendly names to internal names
        specialization_map = {
            "mathematics": "math",
            "physics": "physics", 
            "computer science": "info",
            "sciences": "sciences",
            "music": "musique"
        }
        
        if specialization not in specialization_map:
            await update.message.reply_text(
                "❌ Please choose a valid specialization from the keyboard.",
                parse_mode='HTML'
            )
            return ConversationStates.SPECIALIZATION
        
        context.user_data['specialization'] = specialization_map[specialization]
        
        # Get available levels for this specialization
        levels = self._get_available_levels(specialization_map[specialization])
        
        keyboard = [[level] for level in levels]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        
        await update.message.reply_text(
            f"📚 <b>{update.message.text}</b>\n\n"
            "Please choose your level:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        return ConversationStates.LEVEL
    
    def _get_available_levels(self, specialization: str) -> List[str]:
        """Get available levels for a specialization"""
        base_levels = [f"{specialization.capitalize()}1", f"{specialization.capitalize()}2", 
                      f"{specialization.capitalize()}3", f"{specialization.capitalize()}4", 
                      f"{specialization.capitalize()}5"]
        
        # Filter out unsupported levels
        supported_levels = []
        for level in base_levels:
            if not self._is_level_unsupported(level):
                supported_levels.append(level)
        
        return supported_levels
    
    def _is_level_unsupported(self, level: str) -> bool:
        """Check if a level is unsupported"""
        unsupported_levels = {
            "sciences4 (+4)", "sciences4 (+5)", "sciences5",
            "physics4 (+4)", "physics5", "math4 (+4)", "math5", "info5"
        }
        return level in unsupported_levels
    
    async def choose_level(self, update: Update, context: CallbackContext) -> int:
        """Handle level selection with sub-level support"""
        level = update.message.text.lower()
        
        if self._is_level_unsupported(level):
            await update.message.reply_text(
                "⚠️ This level is not available yet. Please wait for future updates.",
                parse_mode='HTML'
            )
            return ConversationHandler.END
        
        # Check for music specialization (not supported)
        if level.startswith("musique"):
            await update.message.reply_text(
                "❌ <b>Music specialization is not supported</b>\n\n"
                "For religious reasons, music education is not permitted in Islam.",
                parse_mode='HTML'
            )
            return ConversationHandler.END
        
        # Handle sub-levels
        if level in ["physics4", "math4", "sciences4", "info4", "sciences3", "physics3"]:
            context.user_data['level_base'] = level
            keyboard = [["+4"], ["+5"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
            
            await update.message.reply_text(
                "📊 Please choose your sub-level:",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            return ConversationStates.SUB_LEVEL
        
        # Regular level
        context.user_data['level'] = level
        return await self._initialize_grade_collection(update, context)
    
    async def choose_sub_level(self, update: Update, context: CallbackContext) -> int:
        """Handle sub-level selection"""
        sub_level = update.message.text
        
        if sub_level not in ["+4", "+5"]:
            await update.message.reply_text("Please choose a valid sub-level (+4 or +5).")
            return ConversationStates.SUB_LEVEL
        
        level_base = context.user_data['level_base']
        full_level = f"{level_base} ({sub_level})"
        
        if self._is_level_unsupported(full_level):
            await update.message.reply_text(
                "⚠️ This sub-level is not available yet. Please wait for future updates.",
                parse_mode='HTML'
            )
            return ConversationHandler.END
        
        context.user_data['level'] = full_level
        return await self._initialize_grade_collection(update, context)
    
    async def _initialize_grade_collection(self, update: Update, context: CallbackContext) -> int:
        """Initialize grade collection process"""
        context.user_data['current_subject_index'] = 0
        context.user_data['subject_grades'] = {}
        context.user_data['total_grades'] = 0
        context.user_data['total_coefficients'] = 0
        
        return await self._ask_for_grades(update, context)
    
    async def _ask_for_grades(self, update: Update, context: CallbackContext) -> int:
        """Ask for grades with improved UX"""
        specialization = context.user_data['specialization']
        level = context.user_data['level']
        subjects = self._get_subjects_for_level(specialization, level)
        current_index = context.user_data['current_subject_index']
        
        if current_index >= len(subjects):
            return await self._calculate_final_average(update, context)
        
        subject = subjects[current_index]
        context.user_data['current_subject'] = subject
        context.user_data['current_subject_grades'] = SubjectGrade()
        
        # Check if subject requires direct average
        if subject in self.calculator.special_subjects:
            await update.message.reply_text(
                f"📝 Enter the average grade for <b>{subject}</b>:",
                parse_mode='HTML'
            )
            return ConversationStates.NEXT_SUBJECT
        
        # Ask for first exam
        await update.message.reply_text(
            f"📝 Enter the grade for <b>{subject}</b> - Exam 1:",
            parse_mode='HTML'
        )
        return ConversationStates.FIRST
    
    def _get_subjects_for_level(self, specialization: str, level: str) -> List[str]:
        """Get subjects for a specific level and specialization"""
        # This would be implemented based on your specializations data structure
        # For now, returning a placeholder
        return ["subject1", "subject2"]  # Placeholder
    
    async def _calculate_final_average(self, update: Update, context: CallbackContext) -> int:
        """Calculate and display final average"""
        if context.user_data['total_coefficients'] == 0:
            await update.message.reply_text("❌ No valid grades provided.")
            return ConversationHandler.END
        
        average = context.user_data['total_grades'] / context.user_data['total_coefficients']
        self.db.increment_usage_count()
        
        # Format result
        result_text = (
            "🎯 <b>Your Grade Calculation Results</b>\n\n"
            f"📊 <b>Overall Average:</b> <code>{average:.2f}</code>\n\n"
        )
        
        if average >= 10.00:
            result_text += "🎉 <b>Congratulations! You passed!</b>"
        else:
            result_text += "📚 <b>Don't worry, you can retake the exams.</b>"
        
        # Add menu
        keyboard = [
            [InlineKeyboardButton("📱 Follow us on Facebook", url='https://m.facebook.com/hqlaptop')],
            [InlineKeyboardButton("📸 Follow us on Instagram", url='https://www.instagram.com/Hq.laptop')],
            [InlineKeyboardButton("🔄 Calculate Again", callback_data='restart')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            result_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        return ConversationHandler.END
    
    # Additional command handlers
    async def help_command(self, update: Update, context: CallbackContext) -> None:
        """Enhanced help command"""
        help_text = (
            "📚 <b>Grade Calculator Bot Help</b>\n\n"
            "🔹 <b>Commands:</b>\n"
            "/start - Begin grade calculation\n"
            "/help - Show this help message\n"
            "/cancel - Cancel current operation\n"
            "/stats - Show bot statistics\n"
            "/whatsnew - Show latest updates\n\n"
            "🔹 <b>Instructions:</b>\n"
            "1. Choose your specialization\n"
            "2. Select your level\n"
            "3. Enter your grades\n"
            "4. Get your average!\n\n"
            "📞 <b>Support:</b> @yassineboukerma"
        )
        await update.message.reply_text(help_text, parse_mode='HTML')
    
    async def stats_command(self, update: Update, context: CallbackContext) -> None:
        """Show bot statistics"""
        visitor_count = self.db.get_visitor_count()
        usage_count = self.db.get_usage_count()
        uptime = time.time() - self.start_time
        
        stats_text = (
            "📊 <b>Bot Statistics</b>\n\n"
            f"👥 <b>Total Users:</b> {visitor_count}\n"
            f"📈 <b>Calculations:</b> {usage_count}\n"
            f"⏱️ <b>Uptime:</b> {uptime:.1f} seconds\n"
            f"🔄 <b>Requests:</b> {self.request_count}"
        )
        await update.message.reply_text(stats_text, parse_mode='HTML')
    
    async def cancel_command(self, update: Update, context: CallbackContext) -> int:
        """Cancel current operation"""
        await update.message.reply_text(
            "❌ Operation cancelled.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    def setup_handlers(self):
        """Setup all command and message handlers"""
        # Conversation handler for grade calculation
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start_command)],
            states={
                ConversationStates.SPECIALIZATION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.choose_specialization)
                ],
                ConversationStates.LEVEL: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.choose_level)
                ],
                ConversationStates.SUB_LEVEL: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.choose_sub_level)
                ],
                ConversationStates.FIRST: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._receive_first_grade)
                ],
                ConversationStates.SECOND: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._receive_second_grade)
                ],
                ConversationStates.TP: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._receive_tp_grade)
                ],
                ConversationStates.TD: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._receive_td_grade)
                ],
                ConversationStates.NEXT_SUBJECT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._receive_subject_average)
                ],
            },
            fallbacks=[CommandHandler('cancel', self.cancel_command)]
        )
        
        self.application.add_handler(conv_handler)
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("whatsnew", self._whatsnew_command))
    
    async def _whatsnew_command(self, update: Update, context: CallbackContext) -> None:
        """Show what's new"""
        whatsnew_text = (
            "🎉 <b>Latest Updates</b>\n\n"
            "✨ New features and improvements:\n"
            "• Enhanced user interface\n"
            "• Better error handling\n"
            "• Improved performance\n"
            "• New specializations added\n\n"
            "📅 <b>Last Updated:</b> January 2025"
        )
        await update.message.reply_text(whatsnew_text, parse_mode='HTML')
    
    # Grade input handlers (simplified for brevity)
    async def _receive_first_grade(self, update: Update, context: CallbackContext) -> int:
        """Handle first grade input"""
        # Implementation would go here
        return ConversationStates.SECOND
    
    async def _receive_second_grade(self, update: Update, context: CallbackContext) -> int:
        """Handle second grade input"""
        # Implementation would go here
        return ConversationStates.TP
    
    async def _receive_tp_grade(self, update: Update, context: CallbackContext) -> int:
        """Handle TP grade input"""
        # Implementation would go here
        return ConversationStates.TD
    
    async def _receive_td_grade(self, update: Update, context: CallbackContext) -> int:
        """Handle TD grade input"""
        # Implementation would go here
        return await self._ask_for_grades(update, context)
    
    async def _receive_subject_average(self, update: Update, context: CallbackContext) -> int:
        """Handle direct subject average input"""
        # Implementation would go here
        return await self._ask_for_grades(update, context)
    
    def get_all_user_ids_for_broadcast(self) -> List[int]:
        return self.db.get_all_user_ids()
    
    def remove_user_if_blocked(self, user_id: int):
        self.db.remove_visitor(user_id)
    
    async def run(self):
        """Run the bot"""
        try:
            # Initialize application
            self.application = ApplicationBuilder().token(BOT_TOKEN).build()
            
            # Setup handlers
            self.setup_handlers()
            
            # Set webhook
            await self.application.bot.set_webhook(url=WEBHOOK_URL)
            logger.info(f"Webhook set to: {WEBHOOK_URL}")
            
            # Send startup notification
            try:
                await self.application.bot.send_message(
                    chat_id=ADMIN_ID, 
                    text="✅ Bot has started successfully with enhanced features!"
                )
            except Exception as e:
                logger.error(f"Failed to send startup message: {e}")
            
            # Run Flask app
            self.app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
            
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            raise

def main():
    """Main entry point"""
    bot = GradeCalculatorBot()
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info("Shutting down bot...")
        bot.db.close()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the bot
    asyncio.run(bot.run())

if __name__ == '__main__':
    main() 
