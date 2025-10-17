import itertools
import logging
from typing import TYPE_CHECKING

import httpx
from httpx import HTTPError
from telegram import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
    User,
)
from timhatdiehandandermaus_sdk import (
    MissingToken,
    MovieStatusSearchRequestEnum,
    TelegramUserRequest,
    TimApi,
)

from telegram_bot.exceptions import MissingContextArgs
from telegram_bot.helper import TextMessage
from telegram_bot.utils import escape_markdown
from telegram_bot.wostream import search_multiple

if TYPE_CHECKING:
    from uuid import UUID

    from telegram.ext import ContextTypes

_logger = logging.getLogger(__name__)
api: TimApi = None  # type: ignore


def validate_context_args(context: ContextTypes.DEFAULT_TYPE, msg: str) -> list[str]:
    if not context.args:
        raise MissingContextArgs(msg)

    return context.args


async def werhatdiehandandermaus(update: Update, _: ContextTypes.DEFAULT_TYPE):
    return await TextMessage("Tim").send(update)


async def get_user_id(user: User) -> UUID | None:
    dto = TelegramUserRequest(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
    )
    try:
        response = await api.update_telegram_user(dto)
    except HTTPError as e:
        _logger.error("Could not update telegram user", exc_info=e)
        return None
    else:
        return response.id


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    imdb_url = validate_context_args(context, "IMDb/TMDB link required as argument")[0]

    user = update.effective_user
    user_id: UUID | None = None
    if user is not None:
        user_id = await get_user_id(user)

    movie = await api.add_movie(imdb_url=imdb_url, user_id=user_id)
    return await TextMessage(movie.telegram_markdown_v2()).send(
        update,
        disable_web_page_preview=True,
    )


async def handle_watch_delete(
    update: Update, context: ContextTypes.DEFAULT_TYPE, *, watched: bool
):
    title = " ".join(validate_context_args(context, "movie title required as argument"))
    command = "/watch" if watched else "/delete"
    # we always want to delete the old reply keyboard when a button on the reply keyboard has been pressed
    reply_markup: ReplyKeyboardRemove | ReplyKeyboardMarkup = ReplyKeyboardRemove()

    movie_choices = await api.fuzzy_search_movie(
        query=title, status=MovieStatusSearchRequestEnum.QUEUED
    )

    if not movie_choices:
        message = f"no match found for `{title}`"
    elif (
        len(movie_choices) == 1
        or movie_choices[0].metadata.title.lower() == title.lower()
    ):
        queue_id = movie_choices[0].id
        if watched:
            response = await api.mark_movie_as_watched(queue_id=queue_id)
        else:
            response = await api.mark_movie_as_deleted(queue_id=queue_id)
        message = response.telegram_markdown_v2()
    else:
        buttons = [
            KeyboardButton(text=f"{command} {movie.metadata.title}")
            for movie in movie_choices
        ]
        # display 2 buttons per row
        keyboard = list(itertools.pairwise(buttons))
        mark_as = "watched" if watched else "deleted"
        reply_markup = ReplyKeyboardMarkup(
            keyboard,
            one_time_keyboard=True,
            selective=True,
            resize_keyboard=True,
            input_field_placeholder=f"mark selected movie as {mark_as}",
        )
        message = r"Choose the matching movie from the reply keyboard \(does not work in telegram web\)"

    return await TextMessage(message).send(
        update, reply_markup=reply_markup, disable_web_page_preview=True
    )


async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await handle_watch_delete(update, context, watched=False)


async def watch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await handle_watch_delete(update, context, watched=True)


async def queue(update: Update, _: ContextTypes.DEFAULT_TYPE):
    queue_movies = await api.queued_movies()

    markdown_movies = [movie.telegram_markdown_v2() for movie in queue_movies]
    message = "\n".join(markdown_movies)
    return await TextMessage(message).send(update, disable_web_page_preview=True)


async def wostream(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(validate_context_args(context, "movie title required as argument"))

    movies = await api.fuzzy_search_movie(query=query)
    if not movies:
        message = "couldn't find any movie in tim which matches"
        return await TextMessage(message).send(update)

    providers = await search_multiple(movies)
    if not providers:
        titles = "\n".join(
            f"{escape_markdown(movie.metadata.title)} ({movie.metadata.year})"
            for movie in movies
        )
        message = f"Couldn't find any movies\n{titles}\non https://werstreamt.es"
    else:
        message = "\n\n".join(provider.telegram_markdown_v2() for provider in providers)

    return await TextMessage(message).send(update)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        raise context.error  # type: ignore
    except MissingToken:
        message = "Failed to complete action, missing token"
        _logger.exception(message)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            message = "Cannot complete action, failed to authorize to TimApi"
        elif e.response.status_code == 403:
            message = "Cannot complete action, it is forbidden"
        elif e.response.status_code == 409:
            message = "Movie is already enqueued/has been watched"
        else:
            message = f"Unhandled status code error:\n{str(e)}"
    except httpx.HTTPError as e:
        message = "failed to complete action"
        _logger.exception(message)
        message += f"\n{str(e)}"
    except MissingContextArgs as e:
        message = e.msg

    message = escape_markdown(message)
    return await TextMessage(message).send(
        update,
        reply_to_message_id=update.effective_message.message_id,  # type: ignore
        disable_web_page_preview=True,
    )
