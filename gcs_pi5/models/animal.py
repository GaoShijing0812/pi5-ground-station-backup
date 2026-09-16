"""动物种类枚举 - 2025 H 题 5 种"""
from enum import IntEnum


class AnimalType(IntEnum):
    """
    动物种类。int 值同时用作:
    (a) 内部索引
    (b) 通信协议里的动物 ID (与飞控 User.Flight.animal_cnt[] 索引一致)

    2026-07-23 阶段 2 对齐飞控编码:飞控 for(type=0..4) 遍历,
    顺序即下方枚举顺序。
    """
    ELEPHANT = 0   # 象   (飞控 animal_cnt[0])
    MONKEY   = 1   # 猴   (飞控 animal_cnt[1])
    PEACOCK  = 2   # 孔雀 (飞控 animal_cnt[2])
    WOLF     = 3   # 狼   (飞控 animal_cnt[3])
    TIGER    = 4   # 虎   (飞控 animal_cnt[4])


# UI 显示用的中文名
ANIMAL_NAMES_CN = {
    AnimalType.ELEPHANT: "象",
    AnimalType.TIGER:    "虎",
    AnimalType.WOLF:     "狼",
    AnimalType.MONKEY:   "猴",
    AnimalType.PEACOCK:  "孔雀",
}


def name_of(animal: AnimalType) -> str:
    """获取动物中文名"""
    return ANIMAL_NAMES_CN[animal]
