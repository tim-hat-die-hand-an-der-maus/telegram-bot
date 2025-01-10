import asyncio
import logging
import sys

import telegram.ext
from telegram.ext import Application, ApplicationBuilder, filters

from telegram_bot import bot, poll
from telegram_bot.utils import get_env_or_die

_logger = logging.getLogger(__name__)


def main(application: Application):
    # tbot: telegram.Bot = application.bot

    # configure bot
    # asyncio.ensure_future(tbot.set_my_commands(config.COMMANDS))
    # asyncio.ensure_future(tbot.set_my_name(config.NAME))
    # asyncio.ensure_future(tbot.set_my_description(config.DESCRIPTION))
    # asyncio.ensure_future(tbot.set_my_short_description(config.SHORT_DESCRIPTION))

    application.add_handler(
        telegram.ext.CommandHandler(
            "werhatdiehandandermaus", bot.werhatdiehandandermaus
        )
    )
    not_edited_message_filter = ~filters.UpdateType.EDITED_MESSAGE
    application.add_handler(
        telegram.ext.CommandHandler("add", bot.add, filters=not_edited_message_filter)
    )
    application.add_handler(
        telegram.ext.CommandHandler(
            "delete", bot.delete, filters=not_edited_message_filter
        )
    )
    application.add_handler(
        telegram.ext.CommandHandler(
            "watch", bot.watch, filters=not_edited_message_filter
        )
    )
    application.add_handler(
        telegram.ext.CommandHandler(
            "queue", bot.queue, filters=not_edited_message_filter
        )
    )
    application.add_handler(
        telegram.ext.CommandHandler(
            "wostream", bot.wostream, filters=not_edited_message_filter
        )
    )

    # noinspection PyTypeChecker
    application.add_error_handler(bot.error_handler)  # type: ignore

    _logger.info("Starting up")
    application.run_polling()


if __name__ == "__main__":
    bot_token = get_env_or_die("BOT_TOKEN", exit_code=1)
    _application = ApplicationBuilder().token(bot_token).build()

    args = sys.argv[1:]
    _logger.info("args: %s", args)
    if not args:
        main(_application)
    else:
        chat_id = get_env_or_die("POLL_CHAT_ID", exit_code=2)
        if args[0] == "poll":
            asyncio.run(poll.send_movie_poll(chat_id=chat_id, bot=_application.bot))
        elif args[0] == "participation-poll":
            asyncio.run(
                poll.send_participation_poll(chat_id=chat_id, bot=_application.bot)
            )
