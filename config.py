from typing import Dict, Any

PREVIEW_URL = 'https://t.me/+u0x4CI2Nh3IzYjI9'

ITEMS: Dict[str, Dict[str, Any]] = {
    'purchase': {
        'name': 'purchase',
        'price': 200,
        'description': 'Purchase for access setup',
        'secret': 'PURCHASE-ACCESS'
    }
}

MESSAGES = {
    'welcome': (
        "Hello!. I'm CakeBot, and I'm ready to grant you access to the server.\n\n"
        "Membership is available for 200 Stars per month.\n"
        "If you would like to see a preview of the server before joining, use the Server Preview button below.\n\n"
        "_Note: After your purchase is successful, you will be given an account to contact for final access setup._"
    ),
    'help': (
        "🛍 *Digital Store Bot Help*\n\n"
        "Commands:\n"
        "/start - View available items\n"
        "/help - Show this help message\n"
        "/receipt - Show your payment proof\n"
        "/checkproof - Admin verification command\n\n"
        "How to use:\n"
        "1. Use /start to see available items\n"
        "2. Click on the purchase button\n"
        "3. Pay with Stars\n"
        "4. Receive your proof code\n"
        "5. Contact @luciiyan for final access setup"
    )
}
