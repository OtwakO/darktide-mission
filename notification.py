# -*- coding: utf-8 -*-

import os
from datetime import datetime

import apprise
from dotenv import load_dotenv

load_dotenv()

apobj = apprise.Apprise()


def get_discord_service():
    discord_url = os.getenv("DISCORD_WEBHOOK_URL")
    discord_webhook_id = discord_url.split("/")[-2]
    discord_webhook_token = discord_url.split("/")[-1]
    discord_service = f"discord://{discord_webhook_id}/{discord_webhook_token}"
    return discord_service


def send_notification(author, content):
    current_time = int(datetime.timestamp(datetime.now()))
    discord_timestamp = f"<t:{current_time}:F>"

    message = f"""來自: {author}

{content}\n
時間: {discord_timestamp}
{"-"*50}"""
    apobj.add(get_discord_service())
    apobj.notify(
        title="Darktide Mission Board - 問題/意見回報",
        body=message,
    )


if __name__ == "__main__":
    send_notification("Test User", "This is a test issue.")