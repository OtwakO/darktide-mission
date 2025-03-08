STANDARD_KEYWORDS = {
    "Default": {
        "en": "Default",
        "zh-tw": "普通",
        "zh-cn": "普通",
    },
    "Low-Intensity": {
        "en": "Low-Intensity",
        "zh-tw": "低強度",
        "zh-cn": "低强度",
    },
    "Hi-Intensity": {
        "en": "Hi-Intensity",
        "zh-tw": "高強度",
        "zh-cn": "高强度",
    },
    # "Engagement Zone": {
    #     "en": "Engagement Zone",
    #     "zh-tw": "交戰區",
    #     "zh-cn": "交战区",
    # },
    "Shock Troop": {
        "en": "Shock Troop",
        "zh-tw": "突擊兵部隊",
        "zh-cn": "突击兵部队",
    },
    "Hunting Grounds": {
        "en": "Hunting Grounds",
        "zh-tw": "狩獵場",
        "zh-cn": "狩猎场",
    },
    "Ventilation Purge": {
        "en": "Ventilation Purge",
        "zh-tw": "清掃通風",
        "zh-cn": "通风净化",
    },
    "Sniper": {
        "en": "Sniper",
        "zh-tw": "狙擊手",
        "zh-cn": "狙击手",
    },
    "Power Supply Interruption": {
        "en": "Power Supply Interruption",
        "zh-tw": "供電中斷",
        "zh-cn": "供电中断",
    },
    "Monstrous": {
        "en": "Monstrous",
        "zh-tw": "怪物專家",
        "zh-cn": "怪物专家",
    },
    "Nurgle-Blessed": {
        "en": "Nurgle-Blessed",
        "zh-tw": "納垢賜福",
        "zh-cn": "纳垢祝福",
    },
    "Mutants": {
        "en": "Mutants",
        "zh-tw": "變種人",
        "zh-cn": "变种人",
    },
    "Poxbursters": {
        "en": "Poxbursters",
        "zh-tw": "自爆",
        "zh-cn": "自爆",
    },
    "Cooldowns Reduced": {
        "en": "Cooldowns Reduced",
        "zh-tw": "冷卻時間減少",
        "zh-cn": "冷却时间减少",
    },
    "Melee": {
        "en": "Melee",
        "zh-tw": "近戰敵人",
        "zh-cn": "近战敌人",
    },
    "Ranged": {
        "en": "Ranged",
        "zh-tw": "遠程敵人",
        "zh-cn": "远程敌人",
    },
    "Scab Enemies Only": {
        "en": "Scab Enemies Only",
        "zh-tw": "僅血痂敵人",
        "zh-cn": "仅血痂敌人",
    },
    "Extra Grenades": {
        "en": "Extra Grenades",
        "zh-tw": "額外手榴彈",
        "zh-cn": "额外手榴弹",
    },
    "Extra Barrels": {
        "en": "Extra Barrels",
        "zh-tw": "額外爆炸桶",
        "zh-cn": "额外爆炸桶",
    },
    "Toxic Gas": {
        "en": "Toxic Gas",
        "zh-tw": "瘟疫毒氣",
        "zh-cn": "瘟疫毒气",
    },
    "Twin Toxic Gas": {
        "en": "Twin Toxic Gas",
        "zh-tw": "雙頭犬瘟疫毒氣 (雙子)",
        "zh-cn": "双头犬瘟疫毒气 (双子)",
    },
}

SPECIAL_EVENT_KEYWORDS = {
    # "Infected Moebian 21st": {
    #     "en": "Infected Moebian 21st",
    #     "zh-tw": "染疫的莫比亞第21師",
    #     "zh-cn": "被感染的莫比亚21团士兵",
    # },
    # "Mutated Horrors": {
    #     "en": "Mutated Horrors",
    #     "zh-tw": "突變驚懼",
    #     "zh-cn": "变异惧妖",
    # },
    # "Brute Conscripts": {
    #     "en": "Brute Conscripts",
    #     "zh-tw": "野蠻人動員兵",
    #     "zh-cn": "蛮子动员兵",
    # },
}

MISSION_TYPE_KEYWORDS = {
    "Assassination": {
        "en": "Assassination",
        "zh-tw": "刺殺任務",
        "zh-cn": "暗杀任务",
    },
    "Disruption": {
        "en": "Disruption",
        "zh-tw": "破壞任務",
        "zh-cn": "破坏任务",
    },
    "Espionage": {
        "en": "Espionage",
        "zh-tw": "諜報任務",
        "zh-cn": "谍报任务",
    },
    "Investigation": {
        "en": "Investigation",
        "zh-tw": "調查任務",
        "zh-cn": "调查任务",
    },
    "Operations": {
        "en": "Operations",
        "zh-tw": "行動任務",
        "zh-cn": "行动任务",
    },
    "Raid": {
        "en": "Raid",
        "zh-tw": "突擊任務",
        "zh-cn": "突袭任务",
    },
    "Repair": {
        "en": "Repair",
        "zh-tw": "修理任務",
        "zh-cn": "修理任务",
    },
    "Special": {
        "en": "Special",
        "zh-tw": "特殊任務",
        "zh-cn": "特殊任务",
    },
    "Strike": {
        "en": "Strike",
        "zh-tw": "打擊任務",
        "zh-cn": "打击任务",
    },
}

if __name__ == "__main__":
    alphabetical = dict(sorted(MISSION_TYPE_KEYWORDS.items()))
    print(alphabetical)
