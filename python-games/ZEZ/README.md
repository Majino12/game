# ZEZ · 云端冲刺 / Cloud Dash

跳过木箱，滑过飞行障碍，追着金币跑向下一片天空；蜂巢守卫出现时，一边躲波一边射击，击破后继续冒险。游戏围绕二段跳、滑铲、连击奖励、主动冲刺与 Boss 战展开，使用 Python + Pygame CE，支持中英文界面。

![主菜单与角色选择](docs/screenshots/menu.png)

## 安装与启动

需要 **Python 3.9+** 和桌面图形环境。唯一运行依赖为 `pygame-ce==2.5.6`，已固定在 [`requirements.txt`](requirements.txt)。

**macOS**：双击 [`play.command`](play.command)。也可在终端执行 `./play.command`；如下载后的文件没有执行权限，先运行 `chmod +x play.command`。

**Windows**：双击 [`play.bat`](play.bat)。脚本优先使用 Python 启动器 `py -3`，没有启动器时尝试 `python`。

两个脚本都会在游戏目录创建独立的 `.venv`。首次安装依赖需要联网，安装成功后启动时只检查本地依赖，可以离线游玩。脚本不会自动安装 Python。

手动安装与运行，在本目录执行：

```bash
# macOS / Linux
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py
```

```bat
:: Windows
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

图片和音频按源码所在位置加载，支持从任意工作目录通过 `main.py` 的绝对路径启动。例如从仓库根目录运行：

```bash
python-games/ZEZ/.venv/bin/python python-games/ZEZ/main.py
```

默认窗口为 1152 × 648，可调整大小；画面按 1280 × 720 等比例缩放。没有可用中文字体时自动使用英文，安装系统中文字体后可切换中文。无音频设备时仍可游玩。

## 操作

| 按键 | 动作 |
| --- | --- |
| `Enter` / `Space` | 菜单开始；结算后再跑一局 |
| `Space` / `W` / `↑` | 跳跃；空中再次按下为二段跳 |
| 按住 `S` / `↓` / `Ctrl` | 地面滑铲；空中首次按下快速下落 |
| `J` / `Shift` | 能量满时发动冲刺 |
| 按住 `K` / `X` | Boss 战中自动瞄准、连续射击 |
| `Esc` / `P` | 游戏中暂停或继续；结算界面返回菜单 |
| `Enter` | 暂停时继续 |
| `M` | 开关声音 |
| `L` | 中英文切换，需要系统中文字体 |
| `F11` | 切换全屏 |

屏幕按钮也支持鼠标操作，滑铲和射击按钮需要按住。窗口失去焦点会自动暂停并清除按住的动作；暂停不消耗道具、奖励或 Boss 阶段时间。

## 玩法与奖励

沿金币弧线起跳，遇到飞行障碍按住滑铲。前段逐步引入不同障碍，随后提高速度；障碍采用有安全间距的片段。二段跳可以补救起跳时机，空中速降可以提前落地。

连续拾取金币可提高金币得分，最高 **5 倍**；超过 **3 秒** 没有拾取金币，当前连击归零。达到 **30 连击** 可进入 **8 秒金币狂欢**，清除障碍并自动吸取可见金币，速度为基础速度的 **1.25 倍**。奖励触发后有冷却，避免奖励期间连续重复开启。

| 道具 / 技能 | 效果 |
| --- | --- |
| 磁铁 | 7 秒内吸取附近金币 |
| 护盾 | 抵挡一次碰撞，并给 0.9 秒保护 |
| 电池 | 补充 35 点冲刺能量 |
| 主动冲刺 | 能量达到 100 后发动，持续 3 秒；速度为基础速度的 1.55 倍，清除障碍并吸取附近金币 |
| 冲刺 / 狂欢结束 | 恢复基础速度，留出安全距离，并给 0.8 秒保护 |

金币和避开障碍都能补充能量。成绩由距离、金币得分、通过的障碍和 Boss 击破奖励组成；金币得分倍率不会放大结算时存入的钱包金币数量。

每局有三个独立目标：**500 米、60 金币、2 次主动冲刺**。完成一项，结算额外获得 **25 金币**，一局最多奖励 75 金币。

菜单可选择三个角色外观：

| 角色 | 解锁价格 | 能力 |
| --- | --- | --- |
| 奶油 / Cream | 免费 | 相同 |
| 莓莓 / Berry | 100 金币 | 相同 |
| 星云 / Nova | 250 金币 | 相同 |

![跑酷场景](docs/screenshots/run.png)

## 蜂巢守卫 Boss 战

首只守卫在 **350 米**后出现；如果此时仍在主动冲刺或金币狂欢，会等效果结束再入场。入场会清空普通障碍，并给 **2 秒**准备时间。战斗中里程继续增长，普通跑酷片段暂时停止生成。

守卫交替发射两种能量波，攻击前会显示路径和动作提示：**低波用跳跃越过，高波用滑铲穿过**。按住 `K` / `X` 或屏幕射击按钮即可连续自动瞄准，每 0.25 秒发射一次；不必松开射击再跳跃或滑铲。

| 战斗阶段 / 动作 | 规则 |
| --- | --- |
| 装甲预警 | 初始预警 1.35 秒，命中造成 2 点伤害 |
| 弱点开放 | 每次发射能量波后开放 2.5 秒，命中造成 8 点伤害 |
| 半血以下 | 下轮预警缩短为 1 秒，能量波加快；弱点期仍为 2.5 秒 |
| 主动冲刺 | 满能量时发动，每次对守卫造成一次 25 点伤害，同时抵挡能量波 |
| 击败守卫 | 本局获得 **50 金币、500 分、护盾和满能量** |

击破后有短暂退场与安全过渡，随后恢复跑酷。下一只守卫的触发点为**本次击败时的里程 +600 米**。Boss 战中不会触发金币狂欢；击破奖励不增加金币连击。

菜单中的 **Boss 练习**可直接带着护盾和满能量迎战。练习免费，击败后结束本次练习，也可立即重试；练习成绩、金币和局数不计入存档。命令行同样支持：

```bash
python main.py --scene boss
```

![蜂巢守卫与能量波](docs/screenshots/boss.png)

## 存档

新版使用 `save.json`，保存最高分、最远距离、金币余额、局数、已解锁角色、当前外观、声音和语言设置。普通冒险在游戏结束、从暂停返回菜单或关闭进行中的游戏时结算，重复结算不会重复发放金币。Boss 练习不结算到存档。

| 系统 | 默认位置 |
| --- | --- |
| macOS | `~/Library/Application Support/ZEZ/save.json` |
| Windows | `%LOCALAPPDATA%\ZEZ\save.json`；没有该变量时使用用户目录下的 `AppData\Local\ZEZ` |
| Linux | `$XDG_DATA_HOME/zez/save.json`；未设置时为 `~/.local/share/zez/save.json` |

可用环境变量 `ZEZ_SAVE_DIR` 指定存档文件夹。建议使用绝对路径，例如：

```bash
ZEZ_SAVE_DIR="/absolute/path/to/zez-save" .venv/bin/python main.py
```

写入采用临时文件和原子替换；损坏存档会尽量保留 `.corrupt-…` 备份，并用默认数据启动。写入失败会在界面提示，本次数据保留在内存中。新版计分规则已改变，旧 `highscore.txt` 不会自动导入。

## 开发与测试

```text
ZEZ/
├── main.py              # 命令行入口，可从任意工作目录启动
├── play.command         # macOS 启动与首次依赖安装
├── play.bat             # Windows 启动与首次依赖安装
├── requirements.txt
├── runner/
│   ├── model.py         # 跑酷与 Boss 规则、120Hz 固定步长、随机种子
│   ├── app.py           # 窗口、输入、菜单、HUD 与场景绘制
│   ├── assets.py        # 素材缓存、字体、音效与合成背景音乐
│   └── storage.py       # 存档校验、原子写入与角色解锁
├── assets/              # Kenney PNG/OGG、许可证与来源清单
├── docs/screenshots/    # 菜单、跑酷与 Boss 预览
└── tests/               # 跑酷、Boss、输入与存档自动测试
```

在本目录使用已安装依赖的 Python 运行：

```bash
python -m unittest discover -s tests -v
python main.py --headless --scene menu --frames 5
python main.py --headless --scene run --frames 120 --seed 42
python main.py --headless --scene boss --frames 240 --seed 42
python main.py --headless --scene pause --frames 5
python main.py --headless --scene over --frames 5
```

`--headless` 使用 SDL 的虚拟显示与音频驱动，不读取或写入玩家存档；可追加 `--screenshot /path/to/frame.png` 保存最后一帧。`--seed` 用于复现同一随机序列，`--frames` 指定退出前绘制的帧数。

仓库的 [GitHub Actions](https://github.com/Majino12/game/actions) 在 Linux、Python 3.9 和 3.12 上安装依赖，运行单元测试，并对菜单、跑酷、Boss、暂停、结算五个场景做无窗口渲染检查。Boss 场景另运行 240 帧，覆盖入场后的预警与攻击画面。自动模拟用于检查逻辑和障碍可通过性，实际手感仍可通过游玩继续调整。Windows 提供启动脚本，未在此次 macOS 开发环境中进行 Windows 实机验证。

## 素材与旧版本

本次重新下载并选用了 [Kenney New Platformer Pack](https://kenney.nl/assets/new-platformer-pack) 的 **103 个图片及音效文件**，使用 **CC0 1.0** 授权。保留了 [官方许可证](assets/KENNEY_LICENSE.txt)、[来源说明](assets/ASSETS.txt) 和包含逐文件 SHA-256 的 [manifest.json](assets/manifest.json)。

背景音乐由 [`runner/assets.py`](runner/assets.py) 的 `create_music()` 生成，是本项目编写的合成循环，无需额外下载音乐。运行游戏不需要访问素材网站。

蜂巢守卫使用现有蜜蜂素材和程序绘制的机械环、弱点及能量波，无需另外下载素材。当前 Boss 战与跑酷、连击和冲刺共用同一套游戏规则；旧版战斗、传送门与随机天赋实现保留在仓库 Git 历史中。

## English

**ZEZ: Cloud Dash** is an endless runner for Python 3.9+ and Pygame CE. Jump twice, slide under flying obstacles, collect coins, use magnets and shields, and spend full energy on a three-second dash. A 30-coin combo can activate an eight-second bonus with automatic coin collection. Complete three run goals for extra coins and unlock two cosmetic runners; all three characters have identical abilities.

The Hive Guardian first appears after 350 metres. Jump over low waves, slide under high waves, and hold `K/X` for automatic aimed fire. Each attack exposes a weak point for 2.5 seconds with four times the normal shot damage. A dash damages the boss once; below half health its attacks become faster. Defeat it for 50 coins, 500 score, a shield and full energy, then run another 600 metres from the defeat location to reach the next encounter. Menu Boss Practice (or `--scene boss`) starts with a shield and full energy, ends after a victory, and does not add coins, records or runs to the save.

Double-click `play.command` on macOS or `play.bat` on Windows. The launcher creates a local virtual environment and installs dependencies on the first launch; subsequent launches work offline. Manual commands and save locations are listed above. `Space/W/↑`: jump; `S/↓/Ctrl`: slide or fast fall; `J/Shift`: dash; hold `K/X`: fire during a boss fight; `Esc/P`: pause; `M`: sound; `L`: language; `F11`: fullscreen.

Saves are stored in the user's application-data directory, independently of the working directory. Set `ZEZ_SAVE_DIR` to override it. The 103 bundled Kenney art/audio files are CC0 and recorded in the asset manifest; music is synthesized by the game. CI covers Python 3.9/3.12 on Linux and headless rendering; Windows launcher support has not been verified on a Windows machine during this update.
