"""
A Telegram bot demonstrating Star payments functionality.
This bot allows users to purchase digital items using Telegram Stars and request refunds.
"""

import os
import hashlib
import logging
import sqlite3
from datetime import datetime, timezone
from collections import defaultdict
from typing import DefaultDict, Dict
from dotenv import load_dotenv
from telegram import Update, LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    PreCheckoutQueryHandler,
    CallbackContext
)

from config import ITEMS, MESSAGES, PREVIEW_URL

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_USER_IDS = {
    part.strip()
    for part in os.getenv('ADMIN_USER_IDS', '').split(',')
    if part.strip()
}
DB_PATH = os.path.join(os.path.dirname(__file__), 'payment_proofs.db')

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('telegram.ext.Application').setLevel(logging.INFO)
logger = logging.getLogger(__name__)

# Store statistics
STATS: Dict[str, DefaultDict[str, int]] = {
    'purchases': defaultdict(int)
}


def build_store_keyboard() -> InlineKeyboardMarkup:
    """Build the main store keyboard with preview and start-menu shortcuts."""
    keyboard = [[
        InlineKeyboardButton("Server Preview", url=PREVIEW_URL),
        InlineKeyboardButton("Start Menu", callback_data="start_menu")
    ]]
    for item_id, item in ITEMS.items():
        keyboard.append([InlineKeyboardButton(
            f"{item['name']} - {item['price']} ⭐",
            callback_data=item_id
        )])
    return InlineKeyboardMarkup(keyboard)


def init_db() -> None:
    """Create payment proof table if it does not exist."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS payment_proofs (
                charge_id TEXT PRIMARY KEY,
                receipt_code TEXT UNIQUE NOT NULL,
                item_id TEXT NOT NULL,
                item_name TEXT NOT NULL,
                user_id TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
            """
        )


def save_payment_proof(
    charge_id: str,
    receipt_code: str,
    item_id: str,
    item_name: str,
    user_id: str,
    timestamp: str
) -> None:
    """Persist payment proof data so it survives bot restarts."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO payment_proofs
            (charge_id, receipt_code, item_id, item_name, user_id, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (charge_id, receipt_code, item_id, item_name, user_id, timestamp)
        )


def get_payment_by_charge_id(charge_id: str) -> Dict[str, str] | None:
    """Fetch payment proof by Telegram charge id."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT charge_id, receipt_code, item_id, item_name, user_id, timestamp
            FROM payment_proofs
            WHERE charge_id = ?
            """,
            (charge_id,)
        ).fetchone()

    return dict(row) if row else None


def get_payment_by_receipt_code(receipt_code: str) -> Dict[str, str] | None:
    """Fetch payment proof by generated receipt code."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT charge_id, receipt_code, item_id, item_name, user_id, timestamp
            FROM payment_proofs
            WHERE receipt_code = ?
            """,
            (receipt_code,)
        ).fetchone()

    return dict(row) if row else None


def get_latest_payment_by_user(user_id: str) -> Dict[str, str] | None:
    """Fetch latest payment proof for a user."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT charge_id, receipt_code, item_id, item_name, user_id, timestamp
            FROM payment_proofs
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            (user_id,)
        ).fetchone()

    return dict(row) if row else None


def is_admin(user_id: int) -> bool:
    """Check whether the user is an authorized admin checker."""
    return str(user_id) in ADMIN_USER_IDS


def build_receipt_code(user_id: int, charge_id: str) -> str:
    """Build a short deterministic payment proof code from user and charge IDs."""
    payload = f"{user_id}:{charge_id}".encode("utf-8")
    digest = hashlib.sha1(payload).hexdigest()[:10].upper()
    return f"CKB-{digest}"


async def start(update: Update, context: CallbackContext) -> None:
    """Handle /start command - show available items."""
    reply_markup = build_store_keyboard()
    await update.message.reply_text(
        MESSAGES['welcome'],
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def help_command(update: Update, context: CallbackContext) -> None:
    """Handle /help command - show help information."""
    await update.message.reply_text(
        MESSAGES['help'],
        parse_mode='Markdown'
    )


async def receipt_command(update: Update, context: CallbackContext) -> None:
    """Show payment proof details from charge id or latest user payment."""
    user_id = str(update.effective_user.id)

    if context.args:
        charge_id = context.args[0]
        proof = get_payment_by_charge_id(charge_id)
    else:
        proof = get_latest_payment_by_user(user_id)

    if not proof:
        await update.message.reply_text(
            "Belum ada transaksi yang tersimpan.\n"
            "Gunakan: /receipt TELEGRAM_PAYMENT_CHARGE_ID"
        )
        return

    if proof['user_id'] != user_id:
        await update.message.reply_text(
            "Kamu tidak punya akses ke bukti transaksi ini."
        )
        return

    await update.message.reply_text(
        "✅ Bukti Pembayaran\n"
        f"Item: {proof['item_name']}\n"
        f"Kode Bukti: `{proof['receipt_code']}`\n"
        f"Charge ID: `{proof['charge_id']}`\n"
        f"Waktu: {proof['timestamp']}\n"
        "Simpan kode bukti ini untuk verifikasi.",
        parse_mode='Markdown'
    )


async def checkproof_command(update: Update, context: CallbackContext) -> None:
    """Admin command to verify any proof by receipt code or charge id."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Command ini hanya untuk admin checker.")
        return

    if not context.args:
        await update.message.reply_text(
            "Gunakan: /checkproof RECEIPT_CODE_ATAU_CHARGE_ID"
        )
        return

    query = context.args[0].strip()
    proof = get_payment_by_charge_id(query)
    if not proof:
        proof = get_payment_by_receipt_code(query.upper())

    if not proof:
        await update.message.reply_text("Bukti pembayaran tidak ditemukan.")
        return

    await update.message.reply_text(
        "✅ Verifikasi Pembayaran\n"
        f"Item: {proof['item_name']}\n"
        f"User ID: `{proof['user_id']}`\n"
        f"Kode Bukti: `{proof['receipt_code']}`\n"
        f"Charge ID: `{proof['charge_id']}`\n"
        f"Waktu: {proof['timestamp']}",
        parse_mode='Markdown'
    )


async def button_handler(update: Update, context: CallbackContext) -> None:
    """Handle button clicks for item selection."""
    query = update.callback_query
    if not query or not query.message:
        return

    try:
        await query.answer()

        item_id = query.data
        if item_id == "start_menu":
            await query.message.reply_text(
                MESSAGES['welcome'],
                reply_markup=build_store_keyboard(),
                parse_mode='Markdown'
            )
            return

        item = ITEMS[item_id]

        # Make sure message exists before trying to use it
        if not isinstance(query.message, Message):
            return

        await context.bot.send_invoice(
            chat_id=query.message.chat_id,
            title=item['name'],
            description=item['description'],
            payload=item_id,
            provider_token="",  # Empty for digital goods
            currency="XTR",  # Telegram Stars currency code
            prices=[LabeledPrice(item['name'], int(item['price']))],
            start_parameter="start_parameter"
        )

    except Exception as e:
        logger.error(f"Error in button_handler: {str(e)}")
        if query and query.message and isinstance(query.message, Message):
            await query.message.reply_text(
                "Sorry, something went wrong while processing your request."
            )


async def precheckout_callback(update: Update, context: CallbackContext) -> None:
    """Handle pre-checkout queries."""
    query = update.pre_checkout_query
    if query.invoice_payload in ITEMS:
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message="Something went wrong...")


async def successful_payment_callback(update: Update, context: CallbackContext) -> None:
    """Handle successful payments."""
    payment = update.message.successful_payment
    item_id = payment.invoice_payload
    item = ITEMS[item_id]
    user_id = update.effective_user.id
    charge_id = payment.telegram_payment_charge_id
    receipt_code = build_receipt_code(user_id, charge_id)
    paid_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Update statistics
    STATS['purchases'][str(user_id)] += 1
    save_payment_proof(
        charge_id=charge_id,
        receipt_code=receipt_code,
        item_id=item_id,
        item_name=item['name'],
        user_id=str(user_id),
        timestamp=paid_at
    )

    logger.info(
        f"Successful payment from user {user_id} "
        f"for item {item_id} (charge_id: {charge_id})"
    )

    await update.message.reply_text(
        f"Thank you for your purchase! 🎉\n\n"
        f"Here's your secret code for {item['name']}:\n"
        f"`{item['secret']}`\n\n"
        f"Payment proof code:\n"
        f"`{receipt_code}`\n\n"
        "Please contact @luciiyan to confirm and finalize your server access setup.\n\n"
        "To show payment proof again, use:\n"
        f"`/receipt {charge_id}`\n\n"
        "Save this message for your records.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[ 
            InlineKeyboardButton("Server Preview", url=PREVIEW_URL),
            InlineKeyboardButton("Start Menu", callback_data="start_menu")
        ]])
    )


async def error_handler(update: Update, context: CallbackContext) -> None:
    """Handle errors caused by Updates."""
    logger.error(f"Update {update} caused error {context.error}")


def main() -> None:
    """Start the bot."""
    try:
        init_db()
        application = Application.builder().token(BOT_TOKEN).build()

        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("receipt", receipt_command))
        application.add_handler(CommandHandler("checkproof", checkproof_command))
        application.add_handler(CallbackQueryHandler(button_handler))
        application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
        application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))

        # Add error handler
        application.add_error_handler(error_handler)

        # Start the bot
        logger.info("Bot started")
        application.run_polling()

    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")


if __name__ == '__main__':
    main()