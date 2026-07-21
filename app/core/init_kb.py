"""
Initialize and populate knowledge base with support documents
"""

from app.core.qdrant_client import add_documents, get_collection_stats
from app.core.logger import app_logger

# Support knowledge base documents
SUPPORT_DOCUMENTS = [
    {
        "text": "If you're charged twice for a payment, this is usually a pending authorization hold. The duplicate charge should disappear within 3-5 business days. If it doesn't, contact support for a refund.",
        "metadata": {"category": "billing", "topic": "duplicate_charges"},
    },
    {
        "text": "Payment failures can occur due to insufficient funds, expired cards, or bank restrictions. Please verify your payment method and try again. You can update your payment method in account settings.",
        "metadata": {"category": "billing", "topic": "payment_failure"},
    },
    {
        "text": "To request a refund, provide your transaction ID and reason. Refunds are processed within 3-5 business days and will appear in your original payment method.",
        "metadata": {"category": "billing", "topic": "refunds"},
    },
    {
        "text": "Account locked? This happens after multiple failed login attempts for security. Wait 30 minutes or use 'Forgot Password' to reset. Contact support if issue persists.",
        "metadata": {"category": "account", "topic": "locked_account"},
    },
    {
        "text": "Cannot login? Common fixes: 1) Check caps lock, 2) Clear browser cache, 3) Try incognito mode, 4) Reset password. Email must match registered account.",
        "metadata": {"category": "account", "topic": "login_issues"},
    },
    {
        "text": "To update your email address, go to Settings > Account > Email. You'll receive a verification link at the new address. Old email remains active for 24 hours.",
        "metadata": {"category": "account", "topic": "email_change"},
    },
    {
        "text": "App crashes on startup? Try: 1) Restart device, 2) Clear app cache, 3) Update to latest version, 4) Reinstall app. Make sure you have iOS 14+ or Android 10+.",
        "metadata": {"category": "technical", "topic": "app_crashes"},
    },
    {
        "text": "Slow performance? Check internet connection first. Close background apps. Clear cache in settings. If on mobile, ensure you have 2GB+ free storage.",
        "metadata": {"category": "technical", "topic": "performance"},
    },
    {
        "text": "Features not loading? This is usually a temporary server issue. Try refreshing the page or restarting the app. Check status.company.com for system status.",
        "metadata": {"category": "technical", "topic": "features_not_loading"},
    },
    {
        "text": "Premium subscription includes: priority support, advanced analytics, API access, custom integrations, and no usage limits. Billed monthly or annually.",
        "metadata": {"category": "billing", "topic": "premium_features"},
    },
    {
        "text": "Cancel subscription anytime in Settings > Billing. No cancellation fees. Access continues until end of billing period. Automatic refund if canceled within 14 days.",
        "metadata": {"category": "billing", "topic": "cancellation"},
    },
    {
        "text": "Two-factor authentication (2FA) adds extra security. Enable in Settings > Security. Use authenticator app or SMS. Backup codes provided for recovery.",
        "metadata": {"category": "account", "topic": "2fa"},
    },
    {
        "text": "API rate limits: Free tier = 100 requests/hour, Premium = 10,000 requests/hour. Enterprise has custom limits. Use exponential backoff for retries.",
        "metadata": {"category": "technical", "topic": "api_limits"},
    },
    {
        "text": "Data export available in Settings > Data & Privacy. Exports include all your data in JSON format. Processing takes 24-48 hours. Download link sent via email.",
        "metadata": {"category": "account", "topic": "data_export"},
    },
    {
        "text": "Privacy policy: We don't sell your data. Data encrypted at rest and in transit. GDPR and CCPA compliant. Delete account anytime with full data removal.",
        "metadata": {"category": "account", "topic": "privacy"},
    },
]


def initialize_knowledge_base():
    """Load support documents into vector database"""
    app_logger.info("Initializing knowledge base...")

    try:
        count = add_documents(SUPPORT_DOCUMENTS)
        stats = get_collection_stats()

        app_logger.info(f"Successfully added {count} documents to knowledge base")
        app_logger.info(f"Total documents in collection: {stats['total_documents']}")

        return True
    except Exception as e:
        app_logger.error(f"Error initializing knowledge base: {e}")
        return False


if __name__ == "__main__":
    initialize_knowledge_base()
