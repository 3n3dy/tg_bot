import logging
import traceback
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# --- Логування ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Стани ---
CHOOSING_PRODUCT, ASK_EMAIL, PAYMENT_DECISION, NEXT_STEP = range(4)

# --- Google Sheets ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(
    "smooth-calling-470117-h2-5475aabd3ec1.json", scope
)
client = gspread.authorize(creds)
sheet = client.open("Name2").sheet1


# --- Хендлери ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🛒 Товар 1", callback_data="Товар 1")],
        [InlineKeyboardButton("🛒 Товар 2", callback_data="Товар 2")],
        [InlineKeyboardButton("🛒 Товар 3", callback_data="Товар 3")],
        [InlineKeyboardButton("🛒 Товар 4", callback_data="Товар 4")],
    ]
    await update.message.reply_text("Виберіть товар:", reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSING_PRODUCT


async def choose_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["product"] = query.data

    await query.edit_message_text(f"Ви обрали {query.data}. Введіть ваш email:")
    return ASK_EMAIL


async def save_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text
    product = context.user_data.get("product")

    # Знайти наступний вільний рядок
    next_row = len(sheet.get_all_values()) + 1
    sheet.update(f"A{next_row}:B{next_row}", [[product, email]])

    context.user_data["row"] = next_row

    keyboard = [
        [InlineKeyboardButton("✅ Оплатив", callback_data="paid")],
        [InlineKeyboardButton("⏳ Оплачу пізніше", callback_data="later")],
    ]
    await update.message.reply_text("Ви бажаєте оплатити зараз?", reply_markup=InlineKeyboardMarkup(keyboard))
    return PAYMENT_DECISION


async def payment_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    row = context.user_data["row"]
    decision = "Оплачено" if query.data == "paid" else "Відкладено"

    sheet.update(f"C{row}", [[decision]])

    keyboard = [
        [InlineKeyboardButton("🛍 До товарів", callback_data="restart_products")],
        [InlineKeyboardButton("🏠 На головну", callback_data="restart_main")],
    ]
    await query.edit_message_text("Дякуємо! Що далі?", reply_markup=InlineKeyboardMarkup(keyboard))
    return NEXT_STEP


async def next_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "restart_products":
        return await start(query, context)
    else:
        await query.edit_message_text("Вітаю! Ви знову на головній. Введіть /start")
        return ConversationHandler.END


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception: %s", traceback.format_exc())


def main():
    app = ApplicationBuilder().token("5387944433:AAH5rqjcxdHOJ3itGKUg8-BZu_jrfyybUF0").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_PRODUCT: [CallbackQueryHandler(choose_product)],
            ASK_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_email)],
            PAYMENT_DECISION: [CallbackQueryHandler(payment_decision)],
            NEXT_STEP: [CallbackQueryHandler(next_step)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv_handler)
    app.add_error_handler(error_handler)

    app.run_polling()


if __name__ == "__main__":
    main()
