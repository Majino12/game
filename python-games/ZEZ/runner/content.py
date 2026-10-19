"""Shared, bilingual character and guardian descriptions for rules and UI."""

HEROES = {
    "beige": {
        "name": "奶油", "name_en": "Cream",
        "skill": "守护脉冲", "skill_en": "Guardian Pulse",
        "desc": "获得护盾和 1.2 秒保护，清除身边 260 像素内的障碍与敌弹",
        "desc_en": "Gain a shield and 1.2s protection; clear hazards within 260 px",
        "cooldown": 12.0, "color": "#e7ba76",
    },
    "pink": {
        "name": "莓莓", "name_en": "Berry",
        "skill": "流星跃", "skill_en": "Meteor Leap",
        "desc": "随时向上跃起，获得至少 4 秒磁铁和 0.8 秒保护，保留后续空跳",
        "desc_en": "Launch upward, gain 4s magnet and 0.8s protection; keep your air jumps",
        "cooldown": 10.0, "color": "#f58aa7",
    },
    "purple": {
        "name": "星云", "name_en": "Nova",
        "skill": "星环爆发", "skill_en": "Nova Ring",
        "desc": "清除敌弹和前方可见障碍，回复 30 能量，对可攻击守卫造成 35 伤害",
        "desc_en": "Clear enemy shots and visible hazards, gain 30 energy, deal 35 guardian damage",
        "cooldown": 14.0, "color": "#aa86eb",
    },
}

BOSS_SPECS = {
    "bee": {
        "name": "疾风蜂王", "name_en": "Gale Queen",
        "desc": "高低单波交替，观察预警后跳跃或滑铲",
        "desc_en": "Alternating low and high waves; jump or slide after reading the cue",
        "attacks": ("low", "high"), "burst": 1, "color": "#e3ad42",
    },
    "storm": {
        "name": "风暴守卫", "name_en": "Storm Guardian",
        "desc": "同一高度连续双波，低波可用二段跳，高波保持滑铲",
        "desc_en": "Two waves at the same height; double-jump low bursts or hold your slide",
        "attacks": ("high", "low", "low", "high"), "burst": 2, "color": "#9a76df",
    },
    "crystal": {
        "name": "晶岩巨像", "name_en": "Crystal Colossus",
        "desc": "瞄准弹在预警开始时锁定高度；离开危险带，再攻击弱点",
        "desc_en": "Aimed orbs lock your height when the warning begins; move out of the lane",
        "attacks": ("aim", "low", "high"), "burst": 1, "color": "#50a9b3",
    },
}
