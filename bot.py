import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, PreCheckoutQueryHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")  # Read from environment
PRICE_STARS = 1000

premium_users = set()

def is_premium(user_id: int) -> bool:
    return user_id in premium_users

def grant_premium(user_id: int):
    premium_users.add(user_id)
    logger.info(f"User {user_id} granted premium access.")

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("❓ Help", callback_data="help"),
            InlineKeyboardButton("⭐ Upgrade to Premium", callback_data="premium"),
        ]
    ])

def help_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ Upgrade Now", callback_data="premium")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_premium(user_id):
        text = "👋 Welcome back, Premium user! You have full access."
    else:
        text = "👋 Welcome! You are on the free plan. Upgrade to Premium for 1000 Stars (~$10)."
    await update.message.reply_text(text, reply_markup=main_menu_keyboard())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await send_help_message(update, context, user_id, edit=False)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    if query.data == "help":
        await send_help_message(update, context, user_id, edit=True)
    elif query.data == "premium":
        if is_premium(user_id):
            await query.edit_message_text("✅ You already have premium!", reply_markup=main_menu_keyboard())
            return
        await send_invoice(update, context, user_id)
        await query.edit_message_text("💳 Complete the payment using the invoice sent above.")
    elif query.data == "main_menu":
        text = "👋 Welcome back!" if is_premium(user_id) else "👋 Welcome! You are on the free plan."
        await query.edit_message_text(text, reply_markup=main_menu_keyboard())

async def send_help_message(update, context, user_id, edit=False):
    if is_premium(user_id):
        text = "🌟 You are Premium! Enjoy all features."
        reply_markup = main_menu_keyboard()
    else:
        text = (
            "🚀 **Unlock Full Access with Premium!**\n\n"
            "Get unlimited usage, advanced features, and priority support.\n"
            "💎 Price: 1000 Stars (~$10) – one-time payment for lifetime access.\n\n"
            "Tap Upgrade Now below!"
        )
        reply_markup = help_keyboard()

    if edit:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)

async def send_invoice(update, context, user_id):
    await context.bot.send_invoice(
        chat_id=user_id,
        title="Premium Access",
        description="Lifetime premium features",
        payload="premium-payload",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice("Premium Access", PRICE_STARS)],
        start_parameter="premium-upgrade",
    )

async def pre_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    grant_premium(user_id)
    await update.message.reply_text(
        "🎉 Payment successful! You now have Premium Access.",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_premium(user_id):
        await update.message.reply_text("✅ You are premium.")
    else:
        await update.message.reply_text("❌ Free plan. Upgrade using /start.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CallbackQueryHandler(button_callback, pattern="^(help|premium|main_menu)$"))
    app.add_handler(PreCheckoutQueryHandler(pre_checkout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

    # Webhook mode for Render
    PORT = int(os.environ.get("PORT", 8443))
    WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL")  # Render provides this

    if WEBHOOK_URL:
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=f"{WEBHOOK_URL}/webhook"
        )
    else:
        # Fallback to polling if running locally
        app.run_polling()

if __name__ == "__main__":
    main()
