import asyncio
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

from report_notifier import internal_notify
from structures.mission import Mission

DB_DIR = Path("database")
DB_DIR.mkdir(exist_ok=True, parents=True)
DB_PATH = Path(DB_DIR, "missions.db")

DATABASE_COLUMNS = "(mission_id, map_code, map_name, mission_type, mission_category, challenge_level, side_mission, modifier_code, experience, credits, starting_timestamp, expiring_timestamp, keywords)"


def initialize_database() -> None:
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
                challenge_level TEXT,
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
                challenge_level,
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

    create_fts5_sync_trigger()


def create_fts5_sync_trigger():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Insert sync trigger to add new entries to mission_search
            sync_script = """
                CREATE TRIGGER IF NOT EXISTS missions_search_sync_insert
                AFTER INSERT ON missions
                BEGIN
                    INSERT OR IGNORE INTO missions_search
                    VALUES (NEW.mission_id, NEW.map_code, NEW.map_name, NEW.mission_type, NEW.mission_category, NEW.challenge_level, NEW.side_mission, NEW.modifier_code, NEW.experience, NEW.credits, NEW.starting_timestamp, NEW.expiring_timestamp, NEW.keywords, "ALL");
                END;
            """
            cursor.execute(sync_script)

            conn.commit()
    except sqlite3.Error as e:
        asyncio.run(
            internal_notify(
                f"Database FTS5 Create Sync Trigger Error: {str(e)}", sender="Database"
            )
        )


def add_mission_to_database(mission: Mission):
    query = f"""
        INSERT OR IGNORE INTO missions {DATABASE_COLUMNS}
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
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
                    mission.challenge_level,
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
        asyncio.run(
            internal_notify(
                f"""Database Add Mission Error: {str(e)}

Mission: {str(mission)}
""",
                sender="Database",
            )
        )


def prune_expired_missions(current_timestamp: int):
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
        asyncio.run(
            internal_notify(
                f"Database Prune Expired Mission Error: {str(e)}", sender="Database"
            )
        )


def search_with_keywords(
    positive_keywords: List[str] | None = None,
    negative_keywords: List[str] | None = None,
) -> List[Dict[str, Any]]:
    # starting_time = time.time()
    """
    Search SQLite database using FTS5 with advanced keyword filtering.

    Args:
        positive_keywords: List of partial strings that must all be present (AND)
        negative_keywords: List of partial strings to exclude, supports '+' for AND within a negative keyword group

    Returns:
        List of dictionaries, each containing a matching row with column names as keys
    """
    # Initialize empty lists if None
    positive_keywords = positive_keywords or []
    negative_keywords = negative_keywords or []

    # Build FTS5 query string
    fts_terms = []

    # Handle positive keywords - each must be present (AND logic)
    for keyword in positive_keywords:
        # Wrap each term in quotes to handle partial matches
        fts_terms.append(f'"{keyword}"')

    # Handle negative keywords with AND groups
    for neg_group in negative_keywords:
        and_keywords = neg_group.split("+")
        if len(and_keywords) > 1:
            # For AND groups, create a NOT (term1 AND term2) condition
            and_terms = [f'"{kw}"' for kw in and_keywords]
            fts_terms.append(f"NOT ({' AND '.join(and_terms)})")
        else:
            # For single negative terms
            fts_terms.append(f'NOT "{neg_group}"')

    # Combine all terms with AND
    fts_query = (
        " AND ".join(fts_terms).replace("AND NOT", "NOT") if fts_terms else "ALL"
    )

    # If only negative keywords are provided, include a wildcard search to avoid standalone NOT
    if not positive_keywords and negative_keywords:
        fts_query = f'"ALL" {fts_query}'

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
        asyncio.run(
            internal_notify(f"""Database Mission Search Error: {str(e)}
                        
FTS Query: {fts_query}
Positive keywords: {positive_keywords}
Negative keywords: {negative_keywords}""")
        )
        return []


if __name__ == "__main__":
    initialize_database()
