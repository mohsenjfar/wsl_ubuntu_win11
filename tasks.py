import logging
import json
from datetime import date, time, datetime, timedelta
import sqlite3
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

with open("/root/config.json", "r") as config_file:
    config = json.load(config_file)
    config_file.close()

SUMMARY, DESCRIPTION, DATE, CONFIRM = range(4)

main_keyboard = [
        ["/timer_start", "/timer_stop"],
        ["/insert", "/update", "/delete", "/query"],
        ["/today", "/clear", "/cancel", "/help"]
    ]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation"""

    await update.message.reply_text(
        "Need help? use /help button",
        reply_markup=ReplyKeyboardMarkup(
            main_keyboard, one_time_keyboard=True, resize_keyboard=True
        ),
    )


def return_time():
    start_time = datetime.combine(date.today(), time(7,0))
    end_time = datetime.combine(date.today(), time(22,0))
    periods = [25,5,25,5,25,5,25,15]
    states = {
        25:"Session started", 
        5:"Short break", 
        15:"Long break\nDon't forget to drink water"
    }
    times = {}
    while start_time < end_time:
        for p in periods:
            times[start_time.strftime('%H:%M')] = states[p]
            start_time += timedelta(minutes=p)
    return times


async def notification(context: ContextTypes.DEFAULT_TYPE) -> None:
    
    job = context.job

    now  = datetime.now().strftime('%H:%M')

    if now in job.data:
        await context.bot.send_message(job.chat_id, text=job.data[now])


def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Remove job with given name. Returns whether job was removed."""

    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


async def timer_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    data = return_time()

    chat_id = update.effective_message.chat_id

    job_removed = remove_job_if_exists(str(chat_id), context)

    context.job_queue.run_repeating(notification, 60, chat_id=chat_id, name=str(chat_id), data=data, first=1)

    text = "Timer successfully set!"
    if job_removed:
        text += " Old one was removed."

    await update.message.reply_text(text)


async def timer_stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove the job if the user changed their mind."""
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = "Timer successfully cancelled!" if job_removed else "You have no active timer."
    await update.message.reply_text(text)


async def today_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    job = context.job
    
    context.user_data['message_id'] = update.message.message_id
    
    date = datetime.now().strftime('%Y-%m-%d%')
    sql_command = "SELECT * FROM tasks WHERE date LIKE ?"
    crsr.execute(sql_command, (date,))
    tasks = crsr.fetchall()
    if tasks:
        for task in tasks:
            text = f"Summary: {task[1]}\nDate: {task[2]}\nDescription: {task[3]}"
            await update.effective_message.reply_text(text)
    else:
        await update.effective_message.reply_text("Nothing to present!")


async def insert(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    reply_keyboard = [
        ["/cancel"]
    ]

    context.user_data['values'] = {}

    await update.message.reply_text(
        "Please send me a summary for your task:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
    )

    return SUMMARY


async def task_summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the info about the user and ends the conversation."""
    
    context.user_data['values']['summary'] = update.message.text

    reply_keyboard = [
        ["/skip", "/cancel"]
    ]

    await update.message.reply_text(
        "Do you have any descriptions?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
    )

    return DESCRIPTION

async def task_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the info about the user and ends the conversation."""
    
    context.user_data['values']['description'] = update.message.text

    reply_keyboard = [
        ["/cancel"]
    ]

    await update.message.reply_text(
        "Please send me date and time",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, 
            one_time_keyboard=True, 
            resize_keyboard=True,
            input_field_placeholder="yyyy-mm-dd hh:mm frq"
        ),
    )

    return DATE

async def description_skip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skips the location and asks for info about the user."""

    reply_keyboard = [
        ["/cancel"]
    ]

    await update.message.reply_text(
        "Please send me date and time",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, 
            one_time_keyboard=True, 
            resize_keyboard=True,
            input_field_placeholder="yyyy-mm-dd hh:mm frq"
        ),
    )

    return DATE


async def task_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    """Stores the info about the user and ends the conversation."""
    
    context.user_data['values']['date'] = update.message.text

    text = ""

    for value in context.user_data['values']:
        text += f"{value}: {context.user_data['values'][value]}\n"

    reply_keyboard = [
        ["/confirm","/cancel"]
    ]

    await update.message.reply_text(
        "Here is the data you gave me, all ok?\n\n" + text,
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
    )

    return CONFIRM


async def data_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    # Create the tuple "params" with all the parameters inserted by the user
    values = context.user_data['values']
    params = (
        values['summary'],
        values['date'],
        values['description'] if 'description' in values else "NULL"

    )
    sql_command = "INSERT INTO tasks VALUES (NULL, ?, ?, ?);" 
    crsr.execute(sql_command, params)
    conn.commit()

    await update.message.reply_text(
        f"{values['summary']} successfully added.",
        reply_markup=ReplyKeyboardMarkup(main_keyboard, one_time_keyboard=True, resize_keyboard=True),
    )

    del context.user_data['values']

    return ConversationHandler.END

async def cancel_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skips the photo and asks for a location."""

    await update.message.reply_text(
        "Request cancelled",
        reply_markup=ReplyKeyboardMarkup(main_keyboard, one_time_keyboard=True, resize_keyboard=True),
    )

    del context.user_data['values']

    return ConversationHandler.END

async def delete_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
    current_id = update.message.message_id + 1

    for message_id in range(context.user_data['message_id'],current_id):
        await context.bot.deleteMessage(message_id = message_id, chat_id = update.message.chat_id)


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(config["API_TOKEN"]).build()

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("insert", insert)],
        states={
            SUMMARY : [MessageHandler(filters.TEXT & ~filters.COMMAND, task_summary)],
            DESCRIPTION : [
                MessageHandler(filters.TEXT & ~filters.COMMAND, task_description),
                CommandHandler("skip", description_skip),
            ],
            DATE : [
                MessageHandler(filters.TEXT & ~filters.COMMAND, task_date),
                
            ],
            CONFIRM : [CommandHandler("confirm", data_confirm),],
        },
        fallbacks=[CommandHandler("cancel", cancel_request)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("timer_start", timer_start))
    application.add_handler(CommandHandler("timer_stop", timer_stop))
    application.add_handler(CommandHandler("today", today_tasks))
    application.add_handler(CommandHandler("clear", delete_message))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":

    print("Initializing Database...")
    # Connect to local database
    db_name = '/root/db.sqlite'
    conn = sqlite3.connect(db_name, check_same_thread=False)
    # Create the cursor
    crsr = conn.cursor() 
    print("Connected to the database")

    # Command that creates the "oders" table 
    sql_command = """CREATE TABLE IF NOT EXISTS tasks ( 
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        summary VARCHAR(200),
        date VARCHAR(200),
        description VARCHAR(500));"""
    crsr.execute(sql_command)
    print("Tables ready")

    main()