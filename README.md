# ZEZ — Pygame 肉鸽跑酷

用 Python 和 Pygame 编写的 2D 横版跑酷学习项目。通过跳跃、下蹲和技能躲避障碍，挑战 Boss，并从随机天赋中选择强化，争取更高分数。

**项目分类：游戏开发 · Python 学习项目**  
**技术：Python · Pygame**

游戏代码位于 [`python-games/ZEZ`](python-games/ZEZ)。更多说明见子项目的 [한국어 / English / 中文文档](python-games/ZEZ/README.md)。

## 玩法亮点

- **横版跑酷**：背景循环滚动，地面与空中障碍随机出现，难度逐步提高。
- **跳跃与技能**：支持二段跳、下蹲和技能弹；天赋可增加跳跃次数或强化技能。
- **Boss 挑战**：达到指定分数触发战斗，击败 Boss 并完成传送门流程后获得 50 分奖励。
- **随机天赋**：每次完成 Boss 挑战后，从 3 张随机天赋卡中选择 1 张；天赋池包含 9 种能力。
- **最高分存档**：游戏结算时将最高分写入 `highscore.txt`。

## 快速开始

原项目文档要求 Python 3.10+ 和支持桌面窗口的运行环境，记录的开发环境为 Python 3.12.4、Pygame 2.6.1。

```bash
git clone https://github.com/Majino12/game.git
cd game/python-games/ZEZ
python -m pip install pygame==2.6.1
python main.py
```

建议在 Python 虚拟环境中安装依赖。若系统使用 `python3` 命令，请将上面的 `python` 替换为 `python3`。

**请从 `python-games/ZEZ` 目录启动游戏。** 图片、音频及最高分存档使用相对路径；只在仓库根目录执行 `python python-games/ZEZ/main.py` 会导致资源路径不正确。

## 操作说明

| 按键 | 动作 |
| --- | --- |
| `Enter` | 在开始菜单进入游戏；在结束界面重新开始 |
| `Space` | 跳跃 / 二段跳；取得相关天赋后可增加空中跳跃次数 |
| 按住左 `Ctrl` | 下蹲 |
| `J` | 发射技能弹；普通跑酷默认消耗 5 个技能点，Boss 阶段无需消耗技能点 |
| `1` / `2` / `3` | 在天赋界面直接选择对应卡片 |
| `←` / `→`，然后 `Enter` | 切换并确认天赋卡 |
| `Esc` | 在 Boss 阶段放弃本局并进入结束界面；在结束界面退出游戏 |

Boss 阶段依次经历进场警告、战斗和传送门结算。只有完成传送门流程才会增加 Boss 击败计数并进入天赋选择；按 `Esc` 放弃不会获得本次 Boss 的结算奖励。

## 项目结构

```text
python-games/ZEZ/
├── main.py                  # 游戏入口、最高分读写
├── consts.py                # 窗口、物理、难度与战斗参数
├── highscore.txt            # 本地最高分存档
├── modules/
│   ├── perks.py             # 9 种天赋及随机抽取
│   ├── interface/loadres.py # 图片与音频加载
│   ├── scene/               # 开始、跑酷、天赋选择、结束场景
│   └── sprites/             # 玩家、障碍、Boss、传送门和地面
└── resources/               # 图片、背景音乐与音效
```

## 技术与学习内容

- **Python + Pygame**：窗口、输入、精灵、绘制及音频。
- **场景与状态管理**：开始菜单、游戏循环、天赋选择、结束界面，以及 Boss 战斗阶段。
- **游戏机制**：重力跳跃、碰撞判定、渐进难度、技能弹与可叠加天赋。
- **本地数据**：使用文本文件保存最高分。

窗口尺寸为 800 × 600，循环目标为 60 FPS。上面的安装与启动步骤依据现有文档和源码整理，尚未运行验证。
