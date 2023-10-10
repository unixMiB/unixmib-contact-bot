#!/usr/bin/env python3
import os

from telethon import TelegramClient, events
from sqlalchemy import create_engine, Column, Integer, select
from sqlalchemy.orm import DeclarativeBase, Session


class Base(DeclarativeBase):
    pass


class DistributionList(Base):
    __tablename__ = "distribution_lists"

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, unique=True)

    def __repr__(self):
        return f"DistributionList(chat_id={self.chat_id})"


def main():
    api_id = os.environ["TELEGRAM_API_ID"]
    api_hash = os.environ["TELEGRAM_API_HASH"]
    api_token = os.environ["TELEGRAM_API_TOKEN"]
    provided_super_admins = os.environ.get("TELEGRAM_SUPER_ADMINS", "")

    distribution_lists: set[int] = set()

    super_admins: list[str] = [
        int(value)
        for value in provided_super_admins.split(",")
        if value.isnumeric()
    ]

    database_url = os.environ.get(
        "DATABASE_URL", "sqlite:///unixmib_contact_bot.db"
    )
    engine = create_engine(database_url)

    Base.metadata.create_all(engine)
    with Session(engine) as session:
        stmt = select(DistributionList)
        for row in session.scalars(stmt):
            distribution_lists.add(row.chat_id)

    with TelegramClient("telegram", api_id, api_hash).start(
        bot_token=api_token
    ) as client:

        @client.on(
            events.NewMessage(pattern="/start", func=lambda e: e.is_private)
        )
        async def handler(event):
            await event.respond(
                """Ciao, sono il bot di contatto di UnixMiB!
Scrivi un messaggio e sarai ricontattato al più presto."""
            )

        @client.on(
            events.NewMessage(
                pattern="/add_distribution_list", from_users=super_admins
            )
        )
        async def add_distribution_list(event):
            current_chat_id = event.chat_id
            distribution_lists.add(current_chat_id)
            with Session(engine) as session:
                session.add(DistributionList(chat_id=current_chat_id))
                session.commit()
            await event.respond(
                f"Aggiunta lista di distribuzione {current_chat_id} con successo."
            )

        @client.on(
            events.NewMessage(pattern="[^/]", func=lambda e: e.is_private)
        )
        async def handler2(event):
            if event.sender.username is None:
                await event.respond(
                    """Non possiamo risponderti se non hai uno username.
Vai nelle impostazioni e scegline uno."""
                )
                return

            for distr in distribution_lists:
                await client.send_message(
                    distr,
                    f"""Nuovo messaggio da @{event.sender.username}:
{event.text}""",
                )
            await event.respond(
                """Grazie per averci contattato!
Riceverai una risposta al più presto."""
            )

        while True:
            try:
                client.run_until_disconnected()
            except KeyboardInterrupt:
                break


if __name__ == "__main__":
    main()
