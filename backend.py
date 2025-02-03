# -*- coding: utf-8 -*-
import asyncio
import uvicorn
import arrow
from pathlib import Path
from litestar import Litestar, Request, get, post
from litestar.config.cors import CORSConfig
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.response import Template
from litestar.template.config import TemplateConfig
from litestar.config.compression import CompressionConfig
from litestar.static_files import create_static_files_router
from localization.mission_modifier import MISSION_MODIFIERS
from localization.mission_difficulty import MISSION_DIFFICULTY
from localization.mission_type import MISSION_TYPES
from localization.map_name import MAPS
from localization.side_mission import SIDE_MISSIONS
from localization.web_ui import UI_TRANSLATIONS
from localization.keywords import (
    STANDARD_KEYWORDS,
    SPECIAL_EVENT_KEYWORDS,
    MISSION_TYPE_KEYWORDS,
)
from mission_database import search_with_keywords
from mission_fetcher import update_mission_database
from report_notifier import internal_notify, external_notify

cors_config = CORSConfig(allow_origins=["*"])
ASSETS_DIR = Path("assets")
EXCLUDED_KEYWORDS = ["language", "entry_point", "auric_maelstrom_only"]
SEARCH_IN_COLUMNS = [
    "map_code",
    "map_name",
    "mission_type",
    "mission_category",
    "modifier_code",
    "challenge_level",
    "side_mission",
    "keywords",
]

background_task = None


async def fetch_mission_routine():
    # Fetch missions every 2 minutes
    while True:
        await update_mission_database()
        await asyncio.sleep(2 * 60)


async def initialization():
    global background_task
    # Startup event handler
    background_task = asyncio.create_task(fetch_mission_routine())


async def cleanup_background_routine():
    global background_task
    if background_task:
        background_task.cancel()
        try:
            await background_task
        except asyncio.CancelledError:
            print("Background task cancelled.")


@post("/send_report")
async def send_report(request: Request) -> None:
    source_site = request.headers.get("hx-current-url", "")
    form_data = await request.form()
    username = form_data.get("report_author", None)
    content = form_data.get("report_content", None)
    if not username:
        username = "Anonymous"
    if content:
        external_notify(content, sender=username, source_site=source_site)


@get("/")
async def index(request: Request) -> Template:
    entry_point = request.query_params.get(
        "entry_point", f"http://{request.headers.get('host')}"
    )
    language = request.query_params.get("language", "en")
    context = {
        "server_entry_point": entry_point.strip("/"),
        "language": language,
        "maps": MAPS,
        "standard_keywords": STANDARD_KEYWORDS,
        "special_event_keywords": SPECIAL_EVENT_KEYWORDS,
        "mission_type_keywords": MISSION_TYPE_KEYWORDS,
        "mission_difficulties": MISSION_DIFFICULTY,
        "mission_types": MISSION_TYPES,
        "side_missions": SIDE_MISSIONS,
        "ui_translations": UI_TRANSLATIONS,
    }
    return Template("index.html", context=context)


@post("/get_missions")
async def get_missions(request: Request) -> None:
    if request.headers.get("hx-request", None) == "true":
        try:
            form_data = await request.form()
            language = form_data.get("language", "en")
            positive_keyword = [
                key
                for key, value in form_data.items()
                if value == "on" and key not in EXCLUDED_KEYWORDS
            ]
            negative_keyword = [
                key
                for key, value in form_data.items()
                if value == "off" and key not in EXCLUDED_KEYWORDS
            ]
            auric_maelstrom_only = form_data.get("auric_maelstrom_only", None)
            if auric_maelstrom_only:
                if auric_maelstrom_only == "on":
                    positive_keyword.extend(["auric", "Hi-Intensity", "flash_mission"])
                elif auric_maelstrom_only == "off":
                    negative_keyword.extend(["auric+Hi-Intensity+flash_mission"])

            #             print(f"""Language: {language}
            # Positive keywords: {positive_keyword}
            # Negative keywords: {negative_keyword}
            # Auric Maelstrom Only: {auric_maelstrom_only}""")
            missions = search_with_keywords(
                SEARCH_IN_COLUMNS,
                positive_keywords=positive_keyword,
                negative_keywords=negative_keyword,
            )
            # print(missions)

            # Add localized modifiers to missions
            for mission in missions:
                modifiers_string = MISSION_MODIFIERS.get(mission["modifier_code"])[
                    language
                ]
                modifiers = [
                    modifier.strip()
                    for modifier in modifiers_string.split("#")
                    if modifier != ""
                ]
                mission["modifiers"] = modifiers

                # Add localized humanized time delta to missions'
                starting_time = arrow.get(mission["starting_timestamp"])
                humanized_time_delta = starting_time.humanize(locale=language)
                mission["humanized_time_delta"] = humanized_time_delta

            context = {
                "language": language,
                "server_entry_point": form_data.get("entry_point", "").strip("/"),
                "missions": missions,
                "maps": MAPS,
                "ui_translations": UI_TRANSLATIONS,
                "mission_difficulties": MISSION_DIFFICULTY,
                "mission_types": MISSION_TYPES,
                "side_missions": SIDE_MISSIONS,
            }
            if missions:
                return Template("mission.html", context=context)
            else:
                return Template("empty_result.html", context=context)
        except Exception as e:
            source_site = request.headers.get("hx-current-url", "")
            error_form_data = "".join(
                [f"- {key}: {value}\n" for key, value in form_data.items()]
            )
            internal_notify(
                f"{e}\n\nForm data:\n{error_form_data}",
                sender="Backend Framework",
                source_site=source_site,
            )
            pass


app = Litestar(
    [
        index,
        get_missions,
        create_static_files_router(path="/assets", directories=[ASSETS_DIR]),
        send_report,
    ],
    template_config=TemplateConfig(directory="templates", engine=JinjaTemplateEngine),
    cors_config=cors_config,
    on_startup=[initialization],
    on_shutdown=[cleanup_background_routine],
    compression_config=CompressionConfig(backend="gzip", gzip_compress_level=9),
)

if __name__ == "__main__":
    uvicorn.run("backend:app", host="127.0.0.1", port=13131)
