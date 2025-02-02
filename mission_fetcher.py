# -*- coding: utf-8 -*-
import requests
import json
import time
import asyncio
from structures.mission import Mission
from localization.map_name import MAPS
from localization.mission_type import MISSION_TYPES
from localization.mission_modifier import MISSION_MODIFIERS
from report_notifier import internal_notify
from mission_database import (
    add_mission_to_database,
    prune_expired_missions,
    initialize_database,
)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0"


def refresh_token():
    with open("refresh_token.txt", "r", encoding="utf-8") as f:
        REFRESH_TOKEN = f.read()
    print("Fetching Access Token...")
    url = "https://bsp-auth-prod.atoma.cloud/queue/refresh"

    headers = {
        "authorization": f"Bearer {REFRESH_TOKEN}",
        "user-agent": USER_AGENT,
    }
    response = requests.get(url, headers=headers)

    result = response.json()
    new_token = result["AccessToken"]
    auth_sub = result["Sub"]
    with open("refresh_token.txt", "w", encoding="utf-8") as f:
        f.write(result["RefreshToken"])
    return new_token, auth_sub


def fetch_missions(access_token):
    print("Fetching Missions...")
    url = "https://bsp-td-prod.atoma.cloud/mission-board"
    headers = {
        "authorization": f"Bearer {access_token}",
        "user-agent": USER_AGENT,
    }
    response = requests.get(url, headers=headers)
    return response.json()


def parse_missions(missions_json):
    print("Parsing Missions...")
    missions = []
    for mission in missions_json["missions"]:
        # Check if map code has corresponding map name
        map_name = MAPS.get(mission["map"], None)
        if not map_name:
            internal_notify(
                f"Unknown map code: {mission['map']}", sender="Mission Fetcher"
            )
            map_name = mission["map"]
        else:
            map_name = MAPS.get(mission["map"])["en"]

        # Check if map code has corresponding mission type
        mission_type = MISSION_TYPES.get(mission["map"], None)
        if not mission_type:
            internal_notify(
                f"Unknown mission type for map: {mission['map']}",
                sender="Mission Fetcher",
            )
            mission_type = "Unknown"
        else:
            mission_type = MISSION_TYPES.get(mission["map"])["en"]

        # Check if modifier code has corresponding modifiers then add all modifiers of all languages to keywords string
        modifiers = MISSION_MODIFIERS.get(mission["circumstance"], None)
        if not modifiers:
            internal_notify(
                f"Unknown modifier code: {mission['circumstance']}",
                sender="Mission Fetcher",
            )
            modifiers = mission["circumstance"]
            keywords = ""
        else:
            # keywords = " ".join(
            #     [
            #         value
            #         for key, value in MISSION_MODIFIERS.get(
            #             mission["circumstance"]
            #         ).items()
            #     ]
            # )
            keywords = MISSION_MODIFIERS.get(mission["circumstance"])["en"]

        # Calculate experience and credits
        experience = mission["xp"]
        credits = mission["credits"]
        for circumstance, bonus in mission["extraRewards"].items():
            experience += bonus.get("xp", 0)
            credits += bonus.get("credits", 0)

        # Set Expiry Timestamp (Add 24 hours to epoch timestamp)
        expiry_timestamp = int(mission["start"]) + (86400 * 1000)

        mission_entry = Mission(
            mission_id=mission["id"],
            map_code=mission["map"],
            map_name=map_name,
            mission_type=mission_type,
            mission_category=mission.get("category", "normal"),
            challenge_level=f"challenge_level_0{mission['challenge']}",
            side_mission=mission.get("sideMission", "no_side_mission"),
            modifier_code=mission["circumstance"],
            experience=experience,
            credits=credits,
            starting_timestamp=mission["start"],
            expiring_timestamp=expiry_timestamp,
            keywords=keywords,
        )
        missions.append(mission_entry)
    return missions


def add_fetched_missions_to_db(missions: list[Mission]):
    print("Adding fetched missions to database...")
    for mission in missions:
        add_mission_to_database(mission)


async def update_mission_database():
    print("Starting mission database fetching...")
    initialize_database()
    access_token, auth_sub = refresh_token()
    missions_json = fetch_missions(access_token)
    missions = parse_missions(missions_json)
    add_fetched_missions_to_db(missions)
    prune_expired_missions(int(time.time() * 1000))
    print("Mission database fetched complete.")


if __name__ == "__main__":
    asyncio.run(update_mission_database())
