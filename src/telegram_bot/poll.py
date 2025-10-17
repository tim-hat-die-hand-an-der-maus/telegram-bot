from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import telegram
    from timhatdiehandandermaus_sdk import TimApi


async def send_movie_poll(*, api: TimApi, bot: telegram.Bot, chat_id: int) -> None:
    MAX_POLL_OPTIONS = 10

    question = "Which movie do you want to watch?"
    default_options = ["Mir egal"]

    movie_count = MAX_POLL_OPTIONS - len(default_options)
    movie_options = await api.queued_movies(limit=movie_count)
    options = [movie.metadata.title for movie in movie_options]
    options.extend(default_options)

    await bot.send_poll(
        chat_id=chat_id,
        question=question,
        options=options,
        is_anonymous=False,
        allows_multiple_answers=True,
    )


async def send_participation_poll(*, bot: telegram.Bot, chat_id: int) -> None:
    question = "Ich bin"
    options = ["dabei", "nicht dabei", "vielleicht dabei"]

    await bot.send_poll(
        chat_id=chat_id,
        question=question,
        options=options,
        is_anonymous=False,
        allows_multiple_answers=False,
    )
