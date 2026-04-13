from typing import Dict, Any

PREVIEW_URL = 'https://t.me/+u0x4CI2Nh3IzYjI9'

ITEMS: Dict[str, Dict[str, Any]] = {
    'purchase': {
        'name': 'purchase',
        'price': 1,
        'description': 'Test purchase for access setup trial',
        'secret': 'TRIAL-PURCHASE'
    }
}

MESSAGES = {
    'welcome': (
        "Welcome. I am CakeBot, and I am ready to grant you access to the server.\n\n"
        "Membership is available for 200 Stars per month.\n"
        "If you would like to see a preview of the server before joining, you can view it here:\n\n"
        "_Note: After your purchase is successful, you will be given an account to contact for final access setup._"
    ),
    'help': (
        "🛍 *Digital Store Bot Help*\n\n"
        "Commands:\n"
        "/start - View available items\n"
        "/help - Show this help message\n"
        "/refund - Request a refund (requires transaction ID)\n\n"
        "How to use:\n"
        "1. Use /start to see available items\n"
        "2. Click on an item to purchase\n"
        "3. Pay with Stars\n"
        "4. Receive your secret code\n"
        "5. Use /refund to get a refund if needed"
    ),
    'refund_success': (
        "✅ Refund processed successfully!\n"
        "The Stars have been returned to your balance."
    ),
    'refund_failed': (
        "❌ Refund could not be processed.\n"
        "Please try again later or contact support."
    ),
    'refund_usage': (
        "Please provide the transaction ID after the /refund command.\n"
        "Example: `/refund YOUR_TRANSACTION_ID`"
    )
}