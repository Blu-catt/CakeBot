from typing import Dict, Any

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
        "You can continue with the purchase below."
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
        "5. Wait for admin instructions"
    )
}
