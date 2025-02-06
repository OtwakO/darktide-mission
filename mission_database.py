import sqlite3
from typing import List, Dict, Any
from pathlib import Path

from structures.mission import Mission
from report_notifier import internal_notify

DB_DIR = Path("database")
DB_DIR.mkdir(exist_ok=True, parents=True)
DB_PATH = Path(DB_DIR, "missions.db")

DATABASE_COLUMNS = "(mission_id, starting_timestamp)"


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
    Search SQLite database with advanced keyword filtering.

    Args:
        columns: List of column names to search within
        positive_keywords: List of partial strings that must all be present (AND)
        negative_keywords: List of partial strings to exclude, supports '+' for AND within a negative keyword group

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
    positive_keywords = positive_keywords or []
    negative_keywords = negative_keywords or []

    # Positive keywords conditions
    positive_conditions = [build_column_conditions(kw) for kw in positive_keywords]

    # Negative keywords conditions with support for AND within a group
    negative_conditions = []
    for neg_group in negative_keywords:
        # Split keywords within a group that are connected by '+'
        and_keywords = neg_group.split("+")

        if len(and_keywords) > 1:
            # Ensure ANY row with ALL specified keywords is excluded
            group_condition = " AND ".join(
                [f"({build_column_conditions(kw, False)})" for kw in and_keywords]
            )
            negative_conditions.append(f"NOT ({group_condition})")
        else:
            # Regular OR logic for single keywords
            negative_conditions.append(build_column_conditions(neg_group, True))

    # Combine all conditions
    all_conditions = positive_conditions + negative_conditions
    where_clause = " AND ".join(all_conditions) if all_conditions else "1"

    # Construct the complete SQL query
    query = f"""
        SELECT DISTINCT *
        FROM missions
        WHERE {where_clause}
    """

    # Prepare parameters
    params = []
    for kw in positive_keywords:
        params.extend([kw] * len(columns))

    for neg_group in negative_keywords:
        and_keywords = neg_group.split("+")
        for kw in and_keywords:
            params.extend([kw] * len(columns))

    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            rows = cursor.execute(query, params).fetchall()
            missions = [dict(row) for row in rows]
            sorted_missions = sorted(missions, key=lambda x: x["starting_timestamp"])
            return sorted_missions
    except sqlite3.Error as e:
        internal_notify(f"""Database Mission Search Error: {str(e)}
                        
Positive keywords: {positive_keywords}
Negative keywords: {negative_keywords}""")


if __name__ == "__main__":
    initialize_database()
