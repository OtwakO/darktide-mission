from dataclasses import dataclass


@dataclass
class Mission:
    mission_id: str
    map_code: str
    map_name: str
    mission_type: str
    mission_category: str
    challenge_level: str
    side_mission: str
    modifier_code: str
    experience: int
    credits: int
    starting_timestamp: int
    expiring_timestamp: int
    keywords: str
