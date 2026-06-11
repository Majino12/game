# ZEZ — Pygame Runner

---

## 목차 / Table of Contents / 目录

- [한국어](#한국어)
- [English](#english)
- [中文（简体）](#中文简体)

---

<br>

# 한국어

## ZEZ — 로그라이크 러너 게임

> Pygame으로 제작된 2D 사이드스크롤 런게임입니다.  
> 끝없이 달리며 장애물을 피하고, 보스를 처치하고, 퍽을 선택하며 점점 강해지세요.

---

### 스크린샷 미리보기

```
┌────────────────────────────────────────┐
│  Score: 42   Best: 120                 │
│  Skill: ■■■□□   Shield: ◆◆            │
│                                        │
│    [플레이어 달리는 중...]              │
│                                        │
│  ── 지면 ─────────────────────────── │
└────────────────────────────────────────┘
```

---

### 주요 기능

| 기능 | 설명 |
|------|------|
| 무한 스크롤 | 배경·지면이 끝없이 흐르며 난이도가 점진적으로 상승 |
| 이중(더블) 점프 | 공중에서 한 번 더 점프 가능, 스킬 발동 시 자동 사용 |
| 스킬 시스템 | 5개 포인트를 모아 `J`키로 스킬 발사 |
| 보스 방 | 점수 도달 시 보스 등장 → 처치 후 탈출 포탈 통과 |
| 로그라이크 퍽 | 보스 처치마다 무작위 능력 3개 중 하나 선택 |
| 최고 점수 저장 | `highscore.txt`에 자동 저장·불러오기 |

---

### 설치 방법

**요구 사항**

- Python 3.10 이상 (개발 환경: Python 3.12.4)
- pygame 2.x (개발 환경: pygame 2.6.1 / SDL 2.28.4)

```bash
# pygame 설치
pip install pygame
```

---

### 실행 방법

```bash
# 프로젝트 루트 디렉터리에서 실행
python main.py
```

---

### 조작 방법

| 키 | 동작 |
|----|------|
| `Space` | 점프 / 더블 점프 |
| `Left Ctrl` (누르는 동안) | 앉기(크라우치) |
| `J` | 스킬 발사 (포인트 5개 필요) |
| `1` / `2` / `3` | 퍽 선택 화면에서 카드 직접 선택 |
| `◄` / `►` + `Enter` | 퍽 선택 화면에서 카드 탐색 후 확인 |
| `ESC` | 보스 방 탈주 (보스 처치 점수 없음) |
| `Enter` | 게임 오버 화면에서 재시작 |

---

### 보스 방 흐름

```
점수 도달
    │
    ▼
[ENTRY] 1초 경고 + 빨간 화면 깜빡임 (보스 동결)
    │
    ▼
[FIGHT] 보스 탄환 발사 · J키로 스킬 공격
    │ 보스 HP = 0
    ▼
[CLEAR] 녹색 탈출 포탈 등장 → 포탈 통과 시 보스 처치 카운트 +1
    │                            + 점수 +50
    ▼
[PERK SELECTION] 무작위 퍽 3장 중 선택
    │
    ▼
일반 런 재개
```

> **ESC로 탈주하면 보스 처치 카운트가 증가하지 않습니다.**

---

### 퍽 목록 (9종)

| 퍽 | 효과 |
|----|------|
| 도약 강화 | 점프 높이 크게 상승 |
| 이중 도약 | 더블 점프 높이 향상 |
| 에어 마스터 | 공중에서 1회 추가 점프 가능 |
| 파워 서지 | 스킬 데미지 2배 (중첩 가능) |
| 철갑 방어막 | 치명타 1회 무효화 |
| 이중 방어막 | 치명타 2회 무효화 |
| 빠른 충전 | 스킬 충전 필요량 -1 |
| 연속 사격 | 동시 발사 슬롯 +2 |
| 점수 사냥꾼 | 장애물 통과 득점 +1 |

---

### 프로젝트 구조

```
ZEZ/
├── main.py                        # 진입점, 최고 점수 관리
├── consts.py                      # 전역 상수
├── highscore.txt                  # 최고 점수 저장 파일
├── modules/
│   ├── perks.py                   # 퍽 데이터 정의 (9종)
│   ├── interface/
│   │   └── loadres.py             # 리소스 로더 (예외 처리 포함)
│   ├── scene/
│   │   ├── startMenu.py           # 시작 메뉴
│   │   ├── gameRun.py             # 메인 게임 루프 (BossPhase 상태 머신)
│   │   ├── perkSelect.py          # 퍽 선택 UI 씬
│   │   └── gameOver.py            # 게임 오버 화면
│   └── sprites/
│       ├── role.py                # 플레이어 (상태 머신 + 퍽 속성)
│       ├── obstacle.py            # 장애물 (지면 / 공중)
│       ├── boss.py                # 보스 + 보스 스킬 탄환
│       ├── portal.py              # 탈출 포탈 (SRCALPHA 펄스 효과)
│       └── floor.py               # 지면
└── resources/
    ├── background/                # bg.png
    ├── role/                      # run_1~10.png, jump.png, crouch.png, skill.png, boss.png
    ├── obstacles/                 # ground_0~3.png, sky_0~3.png
    └── sound/                     # background_music.mp3, jump.wav, game_over.wav
```

---

### 기술 스택

- **언어**: Python 3.12
- **프레임워크**: Pygame 2.6.1 (SDL 2.28.4)
- **아키텍처**: OOP 씬 상태 머신 (`startMenu → gameRun → perkSelect → gameOver`)
- **물리**: 고정 스텝 60 FPS, 중력 기반 포물선 점프

---

<br>
<br>

---

# English

## ZEZ — Roguelike Runner Game

> A 2D side-scrolling runner built with Pygame.  
> Run forever, dodge obstacles, defeat bosses, choose perks, and grow stronger with every clear.

---

### Features

| Feature | Description |
|---------|-------------|
| Infinite scroll | Background and ground loop endlessly; difficulty scales over time |
| Double jump | A second jump is available while airborne |
| Skill system | Collect 5 skill points, then press `J` to fire a projectile |
| Boss rooms | Bosses appear at score thresholds; escape through the exit portal after defeating them |
| Roguelike perks | After each boss clear, choose one of three random perks |
| High-score save | Automatically saved to and loaded from `highscore.txt` |

---

### Requirements

- Python 3.10 or higher (developed on Python 3.12.4)
- pygame 2.x (developed on pygame 2.6.1 / SDL 2.28.4)

```bash
pip install pygame
```

---

### Running the Game

```bash
# From the project root directory
python main.py
```

---

### Controls

| Key | Action |
|-----|--------|
| `Space` | Jump / Double jump |
| `Left Ctrl` (hold) | Crouch |
| `J` | Fire skill (requires 5 skill points) |
| `1` / `2` / `3` | Select perk card directly |
| `◄` / `►` + `Enter` | Browse and confirm perk cards |
| `ESC` | Flee the boss room (no boss-clear credit) |
| `Enter` | Restart on the Game Over screen |

---

### Boss Room Flow

```
Score threshold reached
        │
        ▼
  [ENTRY]  1-second warning + red screen flash  (boss is frozen)
        │
        ▼
  [FIGHT]  Boss fires projectiles · attack with J
        │  Boss HP reaches 0
        ▼
  [CLEAR]  Green exit portal scrolls in
           → Pass through to earn boss-clear credit (+50 score)
        │
        ▼
  [PERK SELECTION]  Choose one of three random perks
        │
        ▼
  Normal run resumes
```

> **Pressing ESC to flee does NOT award boss-clear credit.**

---

### Perk List (9 total)

| Perk | Effect |
|------|--------|
| Leap Boost | Significantly increases jump height |
| Bounce Back | Increases double-jump height |
| Air Master | Grants one additional mid-air jump |
| Power Surge | Doubles skill damage (stackable) |
| Iron Shield | Absorbs 1 fatal hit |
| Twin Shield | Absorbs 2 fatal hits |
| Quick Charge | Reduces skill point threshold by 1 |
| Rapid Fire | +2 concurrent skill projectile slots |
| Score Hunter | +1 score per obstacle cleared |

---

### Project Structure

```
ZEZ/
├── main.py                        # Entry point, high-score management
├── consts.py                      # Global constants
├── highscore.txt                  # Persisted high score
├── modules/
│   ├── perks.py                   # Perk definitions (9 perks)
│   ├── interface/
│   │   └── loadres.py             # Resource loader (with fallbacks)
│   ├── scene/
│   │   ├── startMenu.py           # Start menu scene
│   │   ├── gameRun.py             # Main game loop (BossPhase state machine)
│   │   ├── perkSelect.py          # Perk selection UI scene
│   │   └── gameOver.py            # Game over screen
│   └── sprites/
│       ├── role.py                # Player (state machine + perk attributes)
│       ├── obstacle.py            # Ground and sky obstacles
│       ├── boss.py                # Boss + boss projectiles
│       ├── portal.py              # Exit portal (SRCALPHA pulse animation)
│       └── floor.py               # Ground floor
└── resources/
    ├── background/                # bg.png
    ├── role/                      # run_1~10.png, jump.png, crouch.png, skill.png, boss.png
    ├── obstacles/                 # ground_0~3.png, sky_0~3.png
    └── sound/                     # background_music.mp3, jump.wav, game_over.wav
```

---

### Architecture Notes

- **Scene state machine**: `startMenu → gameRun ⇄ perkSelect → gameOver → (loop)`
- **Boss state machine** (`BossPhase`): `NONE → ENTRY → FIGHT → CLEAR → NONE`
- **Fixed-step loop**: 60 FPS via `clock.tick(FPS)`, no delta-time
- **Inset hitboxes**: 8 px horizontal / 5 px vertical shrink for a more forgiving feel
- **Perk system**: each perk's `apply(player)` directly mutates `Player` attributes; effects stack across boss clears within a single run

---

### Tech Stack

- **Language**: Python 3.12
- **Framework**: Pygame 2.6.1 (SDL 2.28.4)
- **Pattern**: OOP scene state machine
- **Physics**: Fixed-step gravity, parabolic jump

---

<br>
<br>

---

# 中文（简体）

## ZEZ — 肉鸽跑酷游戏

> 基于 Pygame 开发的 2D 横版跑酷游戏。  
> 无限奔跑、躲避障碍、击败 Boss、选择天赋，在每次通关中越来越强大。

---

### 功能特性

| 功能 | 说明 |
|------|------|
| 无限卷轴 | 背景与地面循环滚动，难度随时间逐步提升 |
| 二段跳 | 在空中可再跳一次 |
| 技能系统 | 积累 5 个技能点后，按 `J` 键发射弹幕 |
| Boss 房间 | 达到分数阈值时 Boss 登场，击败后穿越传送门逃离 |
| 肉鸽天赋 | 每次击败 Boss 后，从 3 张随机天赋卡中选择 1 张 |
| 最高分保存 | 自动保存并读取 `highscore.txt` |

---

### 环境要求

- Python 3.10 或更高版本（开发环境：Python 3.12.4）
- pygame 2.x（开发环境：pygame 2.6.1 / SDL 2.28.4）

```bash
pip install pygame
```

---

### 运行方法

```bash
# 在项目根目录下执行
python main.py
```

---

### 操作说明

| 按键 | 动作 |
|------|------|
| `Space` | 跳跃 / 二段跳 |
| `Left Ctrl`（按住） | 下蹲 |
| `J` | 发射技能（需要 5 个技能点） |
| `1` / `2` / `3` | 在天赋选择界面直接选牌 |
| `◄` / `►` + `Enter` | 浏览并确认天赋卡 |
| `ESC` | 逃离 Boss 房间（不计入击败记录） |
| `Enter` | 在游戏结束界面重新开始 |

---

### Boss 房间流程

```
达到分数阈值
      │
      ▼
 [进场 ENTRY]  1 秒警告 + 红色画面闪烁（Boss 静止）
      │
      ▼
 [战斗 FIGHT]  Boss 发射子弹 · 按 J 键用技能攻击
      │  Boss HP 降至 0
      ▼
 [通关 CLEAR]  绿色逃脱传送门从右侧滚入
               → 穿越传送门获得击败记录 (+50 分)
      │
      ▼
 [天赋选择]  从 3 张随机天赋卡中选择 1 张
      │
      ▼
 恢复普通跑酷
```

> **按 ESC 逃跑不会增加 Boss 击败计数。**

---

### 天赋列表（共 9 种）

| 天赋 | 效果 |
|------|------|
| 强化跃升 | 大幅提升跳跃高度 |
| 强化二段跳 | 提升二段跳高度 |
| 空中大师 | 在空中额外多跳一次 |
| 能量涌动 | 技能伤害翻倍（可叠加） |
| 钢铁护盾 | 抵挡 1 次致命伤害 |
| 双层护盾 | 抵挡 2 次致命伤害 |
| 急速充能 | 技能点需求减少 1 |
| 连续射击 | 同时技能弹槽 +2 |
| 分数猎人 | 每通过一个障碍额外得 1 分 |

---

### 项目结构

```
ZEZ/
├── main.py                        # 入口，管理最高分
├── consts.py                      # 全局常量
├── highscore.txt                  # 最高分存档
├── modules/
│   ├── perks.py                   # 天赋定义（9 种）
│   ├── interface/
│   │   └── loadres.py             # 资源加载器（含异常回退）
│   ├── scene/
│   │   ├── startMenu.py           # 开始菜单
│   │   ├── gameRun.py             # 主游戏循环（BossPhase 状态机）
│   │   ├── perkSelect.py          # 天赋选择 UI 场景
│   │   └── gameOver.py            # 游戏结束界面
│   └── sprites/
│       ├── role.py                # 玩家（状态机 + 天赋属性）
│       ├── obstacle.py            # 地面与空中障碍物
│       ├── boss.py                # Boss 及其弹幕
│       ├── portal.py              # 逃脱传送门（SRCALPHA 脉冲动画）
│       └── floor.py               # 地板
└── resources/
    ├── background/                # bg.png
    ├── role/                      # run_1~10.png, jump.png, crouch.png, skill.png, boss.png
    ├── obstacles/                 # ground_0~3.png, sky_0~3.png
    └── sound/                     # background_music.mp3, jump.wav, game_over.wav
```

---

### 架构说明

- **场景状态机**：`startMenu → gameRun ⇄ perkSelect → gameOver → （循环）`
- **Boss 状态机**（`BossPhase`）：`NONE → ENTRY → FIGHT → CLEAR → NONE`
- **固定步长循环**：60 FPS，通过 `clock.tick(FPS)` 实现
- **内缩碰撞箱**：水平 8px / 垂直 5px 内缩，提供更宽松的判定手感
- **天赋系统**：每张天赋的 `apply(player)` 直接修改 `Player` 属性，效果可在单次游玩内跨 Boss 叠加

---

### 技术栈

- **语言**：Python 3.12
- **框架**：Pygame 2.6.1（SDL 2.28.4）
- **架构**：面向对象场景状态机
- **物理**：固定步长重力，抛物线跳跃

---

<br>

---

*ZEZ — Made with Pygame*
