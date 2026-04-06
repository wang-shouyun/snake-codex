# Snake Legends

`Snake Legends` 是一个使用 `Python + pygame` 编写的多模式贪吃蛇项目，包含基础玩法、道具系统、AI 演示、局域网联机、难度系统、节奏模式和策略模式。

## 运行方式

1. 安装依赖：

```powershell
pip install pygame
```

2. 进入项目目录并启动：

```powershell
cd c:\Users\m1884\Desktop\snake-codex\snake_game
python main.py
```

如果你使用仓库自带虚拟环境，也可以直接运行：

```powershell
cd c:\Users\m1884\Desktop\snake-codex\snake_game
..\.venv\Scripts\python.exe main.py
```

## 新玩法概览

- `限时单人`
  - 自定义小时、分钟、秒。
  - 撞墙或咬到自己立即结束。
- `人机对战`
  - 与 AI 抢食物、争路线，HUD 会显示 AI 状态与预测路径。
- `本地对决`
  - 同屏双人对抗，支持道具、障碍和传送门。
- `双人合作`
  - 两人合作冲团队分数，适合练习配合。
- `局域网开房 / 局域网加入`
  - 主机权威同步。
  - 支持房间发现、实时比分和对局统计。
- `节奏模式`
  - 蛇移动与食物刷新跟随节拍。
  - HUD 显示当前拍点、连击和节奏状态。
  - 音频文件可放在 `assets/music/`。
- `策略模式`
  - 吃食物或触发道具可获得技能点。
  - 随机事件和分支选择会影响对局。
  - AI 会根据策略偏向调整行为。

## 道具与地图元素

- `加速果`
  - 临时提升移动速度。
- `冻结果`
  - 让对手进入减速状态。
- `反弹果`
  - 撞墙时可触发反弹。
- `磁吸果`
  - 吸附附近食物。
- `穿越果`
  - 临时穿越障碍。
- `黄金果`
  - 更高分值和成长收益。
- `障碍物`
  - 对局推进后动态增加。
- `传送门`
  - 将蛇从一端传送到另一端。

## 难度系统

- `简单`
  - 蛇更慢，食物刷新更慢，障碍更少。
- `普通`
  - 当前默认难度。
- `困难`
  - 蛇更快，食物刷新更快，障碍更多。

HUD 会实时显示当前模式、难度、分数、速度、剩余时间，以及技能点、连击、AI 风险等扩展信息。

## 快捷键

### 菜单与设置

- `左右方向键`
  - 切换语言或难度。
- `上下方向键`
  - 切换模式或设置项。
- `Enter / 空格`
  - 确认。
- `Esc`
  - 返回上一级或主菜单。

### 对局中

- `方向键`
  - 玩家一移动。
- `W A S D`
  - 玩家二移动。
- `P`
  - 暂停 / 继续。
- `R`
  - 重新开始当前模式。
- `M`
  - 返回主菜单。
- `Tab`
  - 显示 / 隐藏 AI 路径预测。

### 局域网模式

- `LAN Host`
  - 创建房间并显示主机 IP 与房间码。
- `LAN Join`
  - 输入 IP 加入，或从自动发现列表中选择房间。

## 统计与存档

游戏会把以下信息保存到 `data/player_stats.json`：

- 总局数
- 总吃到食物数
- 各模式最佳分数
- 胜率
- 道具使用次数
- 局域网对局实时统计摘要

## 项目结构

```text
snake_game/
├─ main.py
├─ ui.py
├─ settings.py
├─ game.py
├─ assets/
│  └─ music/
├─ data/
│  └─ player_stats.json
├─ entities/
│  ├─ snake.py
│  └─ food.py
├─ systems/
│  ├─ ai_controller.py
│  ├─ collision.py
│  ├─ data_store.py
│  ├─ game_modes.py
│  ├─ input_handler.py
│  ├─ localization.py
│  ├─ network_session.py
│  ├─ renderer.py
│  ├─ rhythm_mode.py
│  └─ strategy_mode.py
└─ utils/
   └─ helpers.py
```
