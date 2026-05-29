
#BOT_TOKEN = "8640345902:AAFlqlPWJW3UHt-jYPMNKW1VgyhXvArO0Fk"
import sqlite3
from datetime import datetime

from telegram import (
    Update,
    ReplyKeyboardMarkup
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# PASTE YOUR BOT TOKEN HERE
BOT_TOKEN = "8640345902:AAFlqlPWJW3UHt-jYPMNKW1VgyhXvArO0Fk"


# TEMP USER CATEGORY
user_category = {}

# CATEGORY LIMITS
LIMITS = {
    "🧾 Essential": 20000,
    "🎯 Lifestyle": 10000,
    "📈 Investing": 4000
}


# DATABASE
conn = sqlite3.connect("expenses.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    category TEXT,
    amount INTEGER,
    cycle TEXT
)
""")

conn.commit()


# GET CURRENT BILLING CYCLE
def get_current_cycle():

    now = datetime.now()

    year = now.year
    month = now.month
    day = now.day

    if day >= 28:
        return f"{year}-{month}"

    else:

        if month == 1:
            return f"{year-1}-12"

        return f"{year}-{month-1}"


# STATUS FUNCTION
def get_status(category, amount):

    if category == "🧾 Essential":

        if amount >= 20000:
            return "🔴 Exceeded"

        elif amount >= 17000:
            return "🟡 Warning"

        else:
            return "🟢 Safe"

    elif category == "🎯 Lifestyle":

        if amount >= 10000:
            return "🔴 Exceeded"

        elif amount >= 5000:
            return "🟡 Warning"

        else:
            return "🟢 Safe"

    elif category == "📈 Investing":

        if amount >= 4000:
            return "🔴 Exceeded"

        elif amount >= 3000:
            return "🟡 Warning"

        else:
            return "🟢 Safe"


# MAIN MENU
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        ["➕ Add Expense"],
        ["📊 Summary", "💸 Remaining"],
        ["📅 Monthly Report"],
        ["🕒 Recent Transactions"]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "💰 Expense Tracker\n\nChoose an option:",
        reply_markup=reply_markup
    )


# HANDLE MESSAGES
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text
    user_id = update.message.from_user.id

    current_cycle = get_current_cycle()

    # ADD EXPENSE
    if text == "➕ Add Expense":

        keyboard = [
            ["🧾 Essential"],
            ["🎯 Lifestyle"],
            ["📈 Investing"]
        ]

        reply_markup = ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )

        await update.message.reply_text(
            "Choose category:",
            reply_markup=reply_markup
        )

    # CATEGORY SELECT
    elif text in ["🧾 Essential", "🎯 Lifestyle", "📈 Investing"]:

        user_category[user_id] = text

        await update.message.reply_text(
            f"{text} selected.\n\nEnter amount:"
        )

    # AMOUNT ENTRY
    elif text.isdigit():

        if user_id in user_category:

            category = user_category[user_id]
            amount = int(text)

            # SAVE TO DATABASE
            cursor.execute(
                """
                INSERT INTO expenses
                (user_id, category, amount, cycle)
                VALUES (?, ?, ?, ?)
                """,
                (
                    user_id,
                    category,
                    amount,
                    current_cycle
                )
            )

            conn.commit()

            await update.message.reply_text(
                f"✅ Added ₹{amount} to {category}"
            )

        else:

            await update.message.reply_text(
                "Please choose category first."
            )

    # SUMMARY
    elif text == "📊 Summary":

        summary_text = (
            f"📊 Current Summary\n"
            f"Cycle: {current_cycle}\n\n"
        )

        for category in LIMITS:

            cursor.execute(
                """
                SELECT SUM(amount)
                FROM expenses
                WHERE user_id=?
                AND category=?
                AND cycle=?
                """,
                (
                    user_id,
                    category,
                    current_cycle
                )
            )

            result = cursor.fetchone()[0]

            total = result if result else 0

            limit_amount = LIMITS[category]

            status = get_status(category, total)

            summary_text += (
                f"{category}\n"
                f"₹{total} / ₹{limit_amount}\n"
                f"{status}\n\n"
            )

        await update.message.reply_text(summary_text)

    # REMAINING
    elif text == "💸 Remaining":

        remaining_text = (
            f"💸 Remaining Budget\n"
            f"Cycle: {current_cycle}\n\n"
        )

        for category in LIMITS:

            cursor.execute(
                """
                SELECT SUM(amount)
                FROM expenses
                WHERE user_id=?
                AND category=?
                AND cycle=?
                """,
                (
                    user_id,
                    category,
                    current_cycle
                )
            )

            result = cursor.fetchone()[0]

            total = result if result else 0

            limit_amount = LIMITS[category]

            remaining = limit_amount - total

            status = get_status(category, total)

            if remaining < 0:
                remaining = 0

            remaining_text += (
                f"{category}\n"
                f"{status} ₹{remaining} left\n\n"
            )

        await update.message.reply_text(remaining_text)

    # RECENT TRANSACTIONS
    elif text == "🕒 Recent Transactions":

        cursor.execute(
            """
            SELECT category, amount
            FROM expenses
            WHERE user_id=?
            AND cycle=?
            ORDER BY id DESC
            LIMIT 5
            """,
            (
                user_id,
                current_cycle
            )
        )

        transactions = cursor.fetchall()

        if not transactions:

            await update.message.reply_text(
                "No transactions found."
            )

        else:

            recent_text = (
                f"🕒 Recent Transactions\n"
                f"Cycle: {current_cycle}\n\n"
            )

            for transaction in transactions:

                category = transaction[0]
                amount = transaction[1]

                recent_text += (
                    f"₹{amount} → {category}\n"
                )

            await update.message.reply_text(recent_text)

    # MONTHLY REPORT
    elif text == "📅 Monthly Report":

        report_text = (
            f"📅 Monthly Report\n"
            f"Cycle: {current_cycle}\n\n"
        )

        category_totals = {}

        total_spent = 0

        for category in LIMITS:

            cursor.execute(
                """
                SELECT SUM(amount)
                FROM expenses
                WHERE user_id=?
                AND category=?
                AND cycle=?
                """,
                (
                    user_id,
                    category,
                    current_cycle
                )
            )

            result = cursor.fetchone()[0]

            amount = result if result else 0

            category_totals[category] = amount

            total_spent += amount

            report_text += (
                f"{category}\n"
                f"₹{amount} spent\n\n"
            )

        highest_category = max(
            category_totals,
            key=category_totals.get
        )

        report_text += (
            f"💰 Total Spent\n₹{total_spent}\n\n"
            f"🏆 Highest Spending\n{highest_category}"
        )

        await update.message.reply_text(report_text)


app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message
    )
)

print("Bot is running...")

app.run_polling()