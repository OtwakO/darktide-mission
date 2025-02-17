# -*- coding: utf-8 -*-
import os
from datetime import datetime

import apprise
from dotenv import load_dotenv

load_dotenv()


def get_discord_service():
    discord_url = os.getenv("DISCORD_WEBHOOK_URL")
    discord_webhook_id = discord_url.split("/")[-2]
    discord_webhook_token = discord_url.split("/")[-1]
    discord_service = (
        f"discord://{discord_webhook_id}/{discord_webhook_token}/?avatar=No"
    )
    return discord_service


apobj = apprise.Apprise()
apobj.add(get_discord_service())


def external_notify(content, sender="Anonymous", source_site=None):
    current_time = int(datetime.timestamp(datetime.now()))
    discord_timestamp = f"<t:{current_time}:F>"

    message = f"""來自: {sender}

{content}\n
時間: {discord_timestamp}
來源網站: {source_site}
{"-" * 50}"""

    apobj.notify(
        title="Darktide Mission Board - 問題/意見回報",
        body=message,
    )


def internal_notify(content, sender="System", source_site="Internal"):
    current_time = int(datetime.timestamp(datetime.now()))
    discord_timestamp = f"<t:{current_time}:F>"

    message = f"""來自: {sender}

{content}\n
時間: {discord_timestamp}
來源網站: {source_site}
{"-" * 50}"""

    apobj.notify(
        title="Darktide Mission Board - 程式錯誤回報",
        body=message,
    )


if __name__ == "__main__":
    external_notify("This is a test issue.", "Test User")
    internal_notify("This is a test internal message.")
