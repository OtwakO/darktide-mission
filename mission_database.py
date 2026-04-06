import asyncio
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

from report_notifier import internal_notify
from structures.mission import Mission

DB_DIR = Path("database")
DB_DIR.mkdir(exist_ok=True, parents=True)
DB_PATH = Path(DB_DIR, "missions.db")

DATABASE_COLUMNS = "(mission_id, map_code, map_name, mission_type, mission_category, mission_flags, challenge_level, resistance_level, side_mission, modifier_code, experience, credits, starting_timestamp, expiring_timestamp, keywords)"


async def initialize_database() -> None:
    print("Initializing database...")
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS missions (
                mission_id TEXT,
                map_code TEXT,
                map_name TEXT,
                mission_type TEXT,
                mission_category TEXT,
                mission_flags TEXT,
                challenge_level TEXT,
                resistance_level TEXT,
                side_mission TEXT,
                modifier_code TEXT,
                experience INTEGER,
                credits INTEGER,
                starting_timestamp INTEGER,
                expiring_timestamp INTEGER,
                keywords TEXT,
                UNIQUE {DATABASE_COLUMNS}
            )
        """)

        # Create FTS5 table for full-text search
        # The base_term column is for the NOT Unary workaround
        # Reference: https://sqlite.org/forum/info/9dafa0de932dda34
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS missions_search USING fts5(
                mission_id,
                map_code,
                map_name,
                mission_type,
                mission_category,
                mission_flags,
                challenge_level,
                resistance_level,
                side_mission,
                modifier_code,
                experience,
                credits,
                starting_timestamp,
                expiring_timestamp,
                keywords,
                base_term
            )
        """)

        conn.commit()

    await create_fts5_sync_trigger()


async def create_fts5_sync_trigger():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Insert sync trigger to add new entries to mission_search
            sync_script = """
                CREATE TRIGGER IF NOT EXISTS missions_search_sync_insert
                AFTER INSERT ON missions
                BEGIN
                    INSERT OR IGNORE INTO missions_search
                    VALUES (NEW.mission_id, NEW.map_code, NEW.map_name, NEW.mission_type, NEW.mission_category, NEW.mission_flags, NEW.challenge_level, NEW.resistance_level, NEW.side_mission, NEW.modifier_code, NEW.experience, NEW.credits, NEW.starting_timestamp, NEW.expiring_timestamp, NEW.keywords, "ALL");
                END;
            """
            cursor.execute(sync_script)

            conn.commit()
    except sqlite3.Error as e:
        asyncio.create_task(
            internal_notify(
                f"Database FTS5 Create Sync Trigger Error: {str(e)}", sender="Database"
            )
        )
        ...


async def add_mission_to_database(mission: Mission):
    query = f"""
        INSERT OR IGNORE INTO missions {DATABASE_COLUMNS}
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                query,
                (
                    mission.mission_id,
                    mission.map_code,
                    mission.map_name,
                    mission.mission_type,
                    mission.mission_category,
                    mission.mission_flags,
                    mission.challenge_level,
                    mission.resistance_level,
                    mission.side_mission,
                    mission.modifier_code,
                    mission.experience,
                    mission.credits,
                    mission.starting_timestamp,
                    mission.expiring_timestamp,
                    mission.keywords,
                ),
            )
            conn.commit()
    except sqlite3.Error as e:
        asyncio.create_task(
            internal_notify(
                f"""Database Add Mission Error: {str(e)}

Mission: {str(mission)}
""",
                sender="Database",
            )
        )
        ...


async def prune_expired_missions(current_timestamp: int):
    print("- Pruning expired missions...")
    # Prune expired missions from both tables
    query = f"""
        DELETE FROM missions WHERE expiring_timestamp <= {current_timestamp};
        DELETE FROM missions_search WHERE expiring_timestamp <= {current_timestamp};
    """

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.executescript(query)
            conn.commit()
    except sqlite3.Error as e:
        asyncio.create_task(
            internal_notify(
                f"Database Prune Expired Mission Error: {str(e)}", sender="Database"
            )
        )
        ...


async def search_with_keywords(
    positive_keywords: List[str] | None = None,
    negative_keywords: List[str] | None = None,
) -> List[Dict[str, Any]]:
    # starting_time = time.time()
    """
    Search SQLite database using FTS5 with advanced keyword filtering.

    Args:
        positive_keywords: List of keyword groups that are OR'd together by default.
                           Use '+' within a string to AND terms (e.g. "raid+daily").
        negative_keywords: List of keyword groups to exclude.
                           Use '+' within a string to AND terms before negating (e.g. "raid+daily").

    Returns:
        List of dictionaries, each containing a matching row with column names as keys
    """
    positive_keywords = positive_keywords or []
    negative_keywords = negative_keywords or []

    def build_and_group(keyword: str) -> str:
        """Split a keyword by '+' and join its parts with AND."""
        terms = keyword.split("+")
        joined = " AND ".join(f'"{t}"' for t in terms)
        return f"({joined})" if len(terms) > 1 else f'"{terms[0]}"'

    # Positive groups are OR'd together: ("raid") OR ("blitz") OR ("raid" AND "daily")
    positive_parts = [build_and_group(kw) for kw in positive_keywords]

    # Negative groups are each negated: NOT ("raid") NOT ("raid" AND "daily")
    negative_parts = [f"NOT {build_and_group(kw)}" for kw in negative_keywords]

    # Combine into final FTS5 query
    if positive_parts:
        pos_query = " OR ".join(positive_parts)
        # Wrap in parens when combining with negatives to avoid precedence issues
        if negative_parts and len(positive_parts) > 1:
            pos_query = f"({pos_query})"
        fts_query = " ".join([pos_query] + negative_parts)
    elif negative_parts:
        # FTS5 doesn't allow standalone NOT — prefix with a catch-all match
        fts_query = " ".join(['"ALL"'] + negative_parts)
    else:
        fts_query = "ALL"

    # Excludes map_code because there might be overlap (cm_raid vs raid mission types)
    # query = """
    #     SELECT DISTINCT missions.*
    #     FROM missions
    #     WHERE mission_id IN (
    #         SELECT mission_id
    #         FROM missions_search
    #         WHERE
    #             mission_id MATCH ? OR          -- Param 1
    #             map_name MATCH ? OR            -- Param 2
    #             mission_type MATCH ? OR        -- Param 3
    #             mission_category MATCH ? OR    -- Param 4
    #             challenge_level MATCH ? OR     -- Param 5
    #             side_mission MATCH ? OR        -- Param 6
    #             modifier_code MATCH ? OR       -- Param 7
    #             experience MATCH ? OR          -- Param 8
    #             credits MATCH ? OR             -- Param 9
    #             starting_timestamp MATCH ? OR  -- Param 10
    #             expiring_timestamp MATCH ? OR  -- Param 11
    #             keywords MATCH ? OR            -- Param 12
    #             base_term MATCH ?              -- Param 13
    #             -- map_code is omitted here
    #     )
    #     ORDER BY starting_timestamp
    # """

    query = """
        SELECT DISTINCT missions.*
        FROM missions
        WHERE mission_id IN (
            SELECT mission_id
            FROM missions_search 
            WHERE missions_search MATCH ?
        )
        ORDER BY starting_timestamp
    """

    params = (fts_query,) * 1  # 13 params in total

    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            rows = cursor.execute(query, params).fetchall()
            # print(f"Search took {time.time() - starting_time} seconds")
            # starting_time = time.time()
            # result = [dict(row) for row in rows]
            # print(f"Result processing took {time.time() - starting_time} seconds")
            return [dict(row) for row in rows]
    except sqlite3.Error as e:
        asyncio.create_task(
            internal_notify(f"""Database Mission Search Error: {str(e)}
                        
FTS Query: {fts_query}
Positive keywords: {positive_keywords}
Negative keywords: {negative_keywords}""")
        )

        return []


if __name__ == "__main__":
    asyncio.run(initialize_database())
