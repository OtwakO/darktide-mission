# -*- coding: utf-8 -*-
import asyncio
import time
from pathlib import Path

import msgspec
import requests

from localization.map_name import MAPS
from localization.mission_modifier import MISSION_MODIFIERS
from localization.mission_type import MISSION_TYPES
from mission_database import (
    add_mission_to_database,
    prune_expired_missions,
)
from report_notifier import internal_notify
from structures.mission import Mission

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0"
SAVE_RAW_JSON_PATH = Path("database", "raw_missions.json")


def refresh_token():
    print("- Obtaining new access token...")
    try:
        with open(Path("refresh_token.txt"), "r", encoding="utf-8") as f:
            REFRESH_TOKEN = f.read().strip()
        url = "https://bsp-auth-prod.atoma.cloud/queue/refresh"

        headers = {
            "authorization": f"Bearer {REFRESH_TOKEN}",
            "user-agent": USER_AGENT,
        }
        response = requests.get(url, headers=headers)

        result = response.json()
        new_token = result["AccessToken"]
        auth_sub = result["Sub"]
        with open(Path("refresh_token.txt"), "w", encoding="utf-8") as f:
            f.write(result["RefreshToken"])
        return new_token, auth_sub
    except Exception as e:
        internal_notify(f"Failed to refresh token: {e}", sender="Mission Fetcher")
        return None, None


def fetch_missions(access_token):
    print("- Fetching missions from API...")
    try:
        url = "https://bsp-td-prod.atoma.cloud/mission-board"
        headers = {
            "authorization": f"Bearer {access_token}",
            "user-agent": USER_AGENT,
        }
        response = requests.get(url, headers=headers)
        return response.json()
    except Exception as e:
        internal_notify(f"Failed to fetch missions: {e}", sender="Mission Fetcher")
        return {}


def save_raw_mission_json(mission_json):
    print("- Saving raw mission JSON to file...")

    def prune_expired_mission_from_json(all_missions):
        if all_missions:
            current_time = int(time.time() * 1000)
            all_active_missions = [
                mission
                for mission in all_missions
                if (int(mission["start"]) + (86400 * 1000) > current_time)
            ]
        else:
            all_active_missions = []
        return all_active_missions

    try:
        with open(SAVE_RAW_JSON_PATH, "rb") as f:
            existing_json = msgspec.json.decode(f.read())
    except FileNotFoundError:
        existing_json = {"missions": []}
    except msgspec.DecodeError:
        existing_json = {"missions": []}

    for mission in mission_json["missions"]:
        existing_json["missions"].append(mission)

    existing_json["missions"] = prune_expired_mission_from_json(
        existing_json["missions"]
    )

    with open(SAVE_RAW_JSON_PATH, "wb") as f:
        f.write(msgspec.json.encode(existing_json))


def parse_missions(missions_json):
    print("- Parsing missions to human-readable format...")
    try:
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
    except Exception as e:
        internal_notify(f"Failed to parse missions: {e}", sender="Mission Fetcher")
        return []


def add_fetched_missions_to_db(missions: list[Mission]):
    print("- Adding fetched missions to database...")
    for mission in missions:
        add_mission_to_database(mission)


async def update_mission_database():
    print("Fetching Missions from Fatshark...")
    access_token, auth_sub = refresh_token()
    missions_json = fetch_missions(access_token)
    save_raw_mission_json(missions_json)
    missions = parse_missions(missions_json)
    add_fetched_missions_to_db(missions)
    prune_expired_missions(int(time.time() * 1000))
    print("Mission Fetched!")


if __name__ == "__main__":
    asyncio.run(update_mission_database())
