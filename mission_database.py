import sqlite3
from typing import List, Dict, Any
from pathlib import Path

from structures.mission import Mission
from report_notifier import internal_notify

DB_DIR = Path("database")
DB_DIR.mkdir(exist_ok=True, parents=True)
DB_PATH = Path(DB_DIR, "missions.db")

DATABASE_COLUMNS = "(mission_id, map_code, map_name, mission_type, mission_category, challenge_level, side_mission, modifier_code, experience, credits, starting_timestamp, expiring_timestamp, keywords)"


def initialize_database() -> None:
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

        conn.commit()


def add_mission_to_database(mission: Mission):
    initialize_database()

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
        internal_notify(
            f"""Database Add Mission Error: {str(e)}

Mission: {str(mission)}
""",
            sender="Database",
        )


def prune_expired_missions(current_timestamp: int):
    query = """
        DELETE FROM missions WHERE expiring_timestamp <= ?
    """

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(query, (current_timestamp,))
            conn.commit()
    except sqlite3.Error as e:
        internal_notify(
            f"Database Prune Expired Mission Error: {str(e)}", sender="Database"
        )


def search_with_keywords(
    columns: List[str],
    positive_keywords: List[str] | None = None,
    negative_keywords: List[str] | None = None,
) -> List[Dict[str, Any]]:
    """
    Search SQLite database with positive and negative keyword filters.

    Args:
        columns: List of column names to search within
        positive_keywords: List of partial strings that must all be present
        negative_keywords: List of partial strings that must not be present

    Returns:
        List of dictionaries, each containing a matching row with column names as keys
    """
    # Input validation
    if not columns:
        raise ValueError("Table name and at least one column must be provided")

    # Construct LIKE conditions for each keyword and column combination
    def build_column_conditions(keyword: str, negate: bool = False) -> str:
        conditions = [f"{col} LIKE '%' || ? || '%' COLLATE NOCASE" for col in columns]
        combined = " OR ".join(conditions)
        return f"NOT ({combined})" if negate else f"({combined})"

    # Build the complete WHERE clause
    if not positive_keywords:
        positive_keywords = []
    if not negative_keywords:
        negative_keywords = []
    positive_conditions = [build_column_conditions(kw) for kw in positive_keywords]
    negative_conditions = [
        build_column_conditions(kw, True) for kw in negative_keywords
    ]
    all_conditions = positive_conditions + negative_conditions

    where_clause = " AND ".join(all_conditions) if all_conditions else "1"

    # Construct the complete SQL query
    query = f"""
        SELECT DISTINCT *
        FROM missions
        WHERE {where_clause}
    """

    # Create parameter list by repeating each keyword for each column
    params = []
    for kw in positive_keywords + negative_keywords:
        params.extend([kw] * len(columns))

    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = (
                sqlite3.Row
            )  # Enable row factory for dictionary-like access
            cursor = conn.cursor()
            rows = cursor.execute(query, params).fetchall()
            # Convert sqlite3.Row objects to regular dictionaries
            missions = [dict(row) for row in rows]
            sorted_missions = sorted(missions, key=lambda x: x["starting_timestamp"])
            return sorted_missions
    except sqlite3.Error as e:
        internal_notify(f"""Database Mission Search Error: {str(e)}
                        
Positive keywords: {positive_keywords}
Negative keywords: {negative_keywords}""")


if __name__ == "__main__":
    initialize_database()
