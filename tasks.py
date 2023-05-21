import logging
import json
from datetime import datetime, timedelta
import sqlite3

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
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, JobQueue

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

with open("config.json", "r") as config_file:
    config = json.load(config_file)
    config_file.close()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends explanation on how to use the bot."""
    await update.message.reply_text("Hi there!")


async def notification(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the notification."""
    
    job = context.job
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    next_time = job.data['next_time'].strftime('%Y-%m-%d %H:%M')

    if job.data['state'] in [1,3,5,7] and now == next_time:
        await context.bot.send_message(job.chat_id, text="Session started")
        job.data['next_time'] += timedelta(minutes=25)
        job.data['state'] += 1
    
    elif job.data['state'] in [2,4,6] and now == next_time:
        await context.bot.send_message(job.chat_id, text="Short break")
        job.data['next_time'] += timedelta(minutes=5)
        job.data['state'] += 1

    elif job.data['state'] == 8 and now == next_time:
        await context.bot.send_message(job.chat_id, text="Long break")
        job.data['next_time'] += timedelta(minutes=15)
        job.data['state'] = 1


def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Remove job with given name. Returns whether job was removed."""

    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


async def timer_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a job to the queue."""
    chat_id = update.effective_message.chat_id

    try:

        job_removed = remove_job_if_exists(str(chat_id), context)
        
        data = {'next_time':datetime.now(), 'state':1}

        context.job_queue.run_repeating(notification, 60, chat_id=chat_id, name=str(chat_id), data=data, first=1)

        text = "Timer successfully set!"
        if job_removed:
            text += " Old one was removed."
        await update.effective_message.reply_text(text)

    except (IndexError, ValueError):
        await update.effective_message.reply_text("Usage: /timer_start")


async def timer_stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove the job if the user changed their mind."""
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = "Timer successfully cancelled!" if job_removed else "You have no active timer."
    await update.message.reply_text(text)

def next_time(time):
    
    values = time.split(';')
    now = datetime.strptime(values[0], '%Y-%m-%d-%H:%M')
    days = int(values[1])
    next_t = now + timedelta(days=days)
    return next_t.strftime(f'%Y-%m-%d-%H:%M;{days}')


async def due_tasks(context: ContextTypes.DEFAULT_TYPE) -> None:
    
    job = context.job

    date = datetime.now().strftime('%Y-%m-%d-%H:%M%')
    crsr.execute(f"SELECT * FROM tasks WHERE date LIKE {date}")
    tasks = crsr.fetchall()

    if tasks:
        for task in tasks:
            text = f"Task No: {task[0]}\nSummary: {task[1]}\nDate: {task[2]}\nDescription: {task[3]}"
            await context.bot.send_message(job.chat_id, text=text)
            sql_command = f"UPDATE tasks SET date={next_time(task[2])} WHERE id={task[0]}"
            crsr.execute(sql_command)
            conn.commit()


async def today_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    job = context.job
    
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


async def tasker_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a job to the queue."""
    chat_id = update.effective_message.chat_id

    try:

        job_removed = remove_job_if_exists(str(chat_id), context)

        context.job_queue.run_repeating(notification, 60, chat_id=chat_id, name=str(chat_id), first=1)

        text = "Tasker successfully started!"
        if job_removed:
            text += " Old one was removed."
        await update.effective_message.reply_text(text)

    except (IndexError, ValueError):
        await update.effective_message.reply_text("Usage: /tasker_start")


async def tasker_stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove the job if the user changed their mind."""
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = "Tasker successfully cancelled!" if job_removed else "You have no active Tasker."
    await update.message.reply_text(text)


async def insert(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    try:
        summary = context.args[0] 
        date = context.args[1]
        description = context.args[2]

        # Create the tuple "params" with all the parameters inserted by the user
        params = (summary, date, description)
        sql_command = "INSERT INTO tasks VALUES (NULL, ?, ?, ?);" 
        crsr.execute(sql_command, params)
        conn.commit()

        # If at least 1 row is affected by the query we send specific messages
        if crsr.rowcount < 1:
            text = "OOps! something wrong, please try again"
            await update.message.reply_text(text)
        else:
            text = f"Good news, {summary} successfully inserted!"
            await update.message.reply_text(text)
    
    except(IndexError, ValueError):
        await update.effective_message.reply_text("Usage: /insert summary date description")


async def select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    try:
        # Execute the query and get all (*) the oders
        crsr.execute("SELECT * FROM tasks")
        tasks = crsr.fetchall() # fetch all the results

        if tasks:
            text = "\n\n".join([
                f"Task No: {task[0]}\nSummary: {task[1]}\nDate: {task[2]}\nDescription: {task[3]}"
                for task in tasks
            ])
            
            await update.message.reply_text(text)
        
        # Otherwhise, print a default text
        else:
            text = "OOps! Nothing to show"
            await update.message.reply_text(text)

    except (IndexError, ValueError): 
        await update.effective_message.reply_text("Usage: /select")


async def update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        # Get the arguments
        id = context.args[0]
        summary = context.args[1] 
        date = context.args[2]
        description = context.args[3]

        # Create the tuple "params" with all the parameters inserted by the user
        params = (summary, date, description, id)

        # Create the UPDATE query, we are updating the product with a specific id so we must put the WHERE clause
        sql_command="UPDATE tasks SET summary=?, date=?, description=? WHERE id =?"
        crsr.execute(sql_command, params) # Execute the query
        conn.commit() # Commit the changes

        # If at least 1 row is affected by the query we send a specific message
        if crsr.rowcount < 1:
            text = "OOps! something wrong, please try again"
            await update.message.reply_text(text)
        else:
            text = f"Good news, {summary} successfully updated!"
            await update.message.reply_text(text)

    except (IndexError, ValueError): 
        await update.effective_message.reply_text("Usage: /update task_id summary date description")


async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        # Get the arguments
        id = context.args[0]

        sql_command = "DELETE FROM tasks WHERE id = (?);"
        crsr.execute(sql_command, (id,))
        conn.commit()

        # If at least 1 row is affected by the query we send a specific message
        if crsr.rowcount < 1:
            text = "OOps! something wrong, please try again"
            await update.message.reply_text(text)
        else:
            text = f"Maybe not very good news, but task with id {id} successfully deleted!"
            await update.message.reply_text(text)

    except (IndexError, ValueError): 
        await update.effective_message.reply_text("Usage: /delete task_id")


def main() -> None:
    """Run bot."""

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(config["TEST_TOKEN"]).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler(["start", "help"], start))
    application.add_handler(CommandHandler("timer_start", timer_start))
    application.add_handler(CommandHandler("timer_stop", timer_stop))
    application.add_handler(CommandHandler("insert", insert))
    application.add_handler(CommandHandler("select", select))
    application.add_handler(CommandHandler("update", update))
    application.add_handler(CommandHandler("delete", delete))
    application.add_handler(CommandHandler("tasker_start", tasker_start))
    application.add_handler(CommandHandler("tasker_stop", tasker_stop))
    application.add_handler(CommandHandler("today", today_tasks))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":

    print("Initializing Database...")
    # Connect to local database
    db_name = 'db.sqlite'
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