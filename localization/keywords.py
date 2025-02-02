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
    "Engagement Zone": {
        "en": "Engagement Zone",
        "zh-tw": "交戰區",
        "zh-cn": "交战区",
    },
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
        "zh-cn": "清扫通风",
    },
    "Sniper": {
        "en": "Sniper",
        "zh-tw": "狙擊手",
        "zh-cn": "狙击手",
    },
    "Toxic Gas": {
        "en": "Toxic Gas",
        "zh-tw": "瘟疫毒氣",
        "zh-cn": "瘟疫毒气",
    },
    "Twin Toxic Gas": {
        "en": "Twin Toxic Gas",
        "zh-tw": "雙頭犬瘟疫毒氣",
        "zh-cn": "双头犬瘟疫毒气",
    },
    "Power Supply Interruption": {
        "en": "Power Supply Interruption",
        "zh-tw": "斷電",
        "zh-cn": "断电",
    },
    "Monstrous": {
        "en": "Monstrous",
        "zh-tw": "怪物",
        "zh-cn": "怪物",
    },
    "Nurgle-Blessed": {
        "en": "Nurgle-Blessed",
        "zh-tw": "納垢賜福",
        "zh-cn": "纳垢祝福",
    },
    "Cooldowns Reduced": {
        "en": "Cooldowns Reduced",
        "zh-tw": "冷卻時間減少",
        "zh-cn": "冷却时间减少",
    },
    "Scab Enemies Only": {
        "en": "Scab Enemies Only",
        "zh-tw": "僅血痂敵人",
        "zh-cn": "仅血痂敌人",
    },
    "Melee": {
        "en": "Melee",
        "zh-tw": "近戰敵人",
        "zh-cn": "近战敌人",
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
    "Brute Conscripts": {
        "en": "Brute Conscripts",
        "zh-tw": "野蠻人動員兵",
        "zh-cn": "蛮子动员兵",
    },
}

if __name__ == "__main__":
    alphabetical = dict(sorted(STANDARD_KEYWORDS.items()))
    print(alphabetical)
