import asyncio
import logging
import signal
import sys
from typing import TYPE_CHECKING, cast

import sentry_sdk
import telegram.ext
from bs_nats_updater import create_updater
from telegram.ext import Application, ApplicationBuilder, filters
from timhatdiehandandermaus_sdk import TimApi

from telegram_bot import bot, poll
from telegram_bot.config import Config, load_config

if TYPE_CHECKING:
    from collections.abc import Awaitable

_logger = logging.getLogger(__name__)


def _run_application(
    application: Application,
    api_client: TimApi,
) -> None:
    # tbot: telegram.Bot = application.bot
    bot.api = api_client

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
    application.run_polling(
        stop_signals=[
            signal.SIGINT,
            signal.SIGTERM,
        ]
    )


def _setup_monitoring(config: Config) -> None:
    logging.basicConfig()

    logging.root.level = logging.WARNING
    logging.getLogger(__package__).level = logging.DEBUG

    sentry_dsn = config.sentry_dsn
    if sentry_dsn is not None:
        sentry_sdk.init(
            dsn=sentry_dsn,
            release=config.app_version,
        )
    else:
        _logger.warning("Sentry is disabled")


async def _run_with_client(client: TimApi, awaitable: Awaitable) -> None:
    try:
        await awaitable
    finally:
        await client.close()


def main():
    config = load_config()
    _setup_monitoring(config)
    api_client = TimApi(config.api.token, api_url=config.api.base_url)
    application = (
        ApplicationBuilder()
        .updater(create_updater(config.telegram.token, config.nats))
        .post_shutdown(lambda _: api_client.close())
        .build()
    )
    telegram_bot = cast(telegram.Bot, application.bot)

    args = sys.argv[1:]
    _logger.info("args: %s", args)
    match args:
        case []:
            _run_application(application, api_client)
        case ["poll"]:
            asyncio.run(
                _run_with_client(
                    api_client,
                    poll.send_movie_poll(
                        api=api_client,
                        bot=telegram_bot,
                        chat_id=config.telegram.poll_chat_id,
                    ),
                )
            )
        case ["participation-poll"]:
            asyncio.run(
                _run_with_client(
                    api_client,
                    poll.send_participation_poll(
                        chat_id=config.telegram.poll_chat_id,
                        bot=telegram_bot,
                    ),
                )
            )
        case other:
            _logger.error("unknown command: %s", other)
            asyncio.run(api_client.close())


if __name__ == "__main__":
    main()
