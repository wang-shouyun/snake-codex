# Snake Legends

一个使用 **Python + pygame** 编写的多模式贪吃蛇项目。  
它不只是基础版贪吃蛇，还加入了 **AI 对战、局域网联机、难度系统、节奏模式、策略模式、道具系统、统计系统、多语言界面** 等内容，适合作为：

- Python 初学者的完整练手项目
- pygame 游戏开发入门项目
- 课程设计 / 毕业设计 / 作品集项目
- 想学习“如何把一个小游戏逐步做复杂”的示例工程

---

## 1. 项目特色

本项目包含以下玩法和系统：

- 基础贪吃蛇玩法
- 多模式菜单
- AI 自动演示 / 人机对战
- 本地双人对战
- 双人合作模式
- 局域网开房 / 加入
- 三档难度系统
- 节奏模式
- 策略模式
- 多种特殊食物和状态效果
- 障碍物与传送门
- HUD 实时信息显示
- 本地 JSON 统计存档
- 中文 / English / Deutsch 多语言界面

---

## 2. 你能玩到什么

### 2.1 基础模式
- `Timed Solo`
  单人限时冲分模式，可自定义小时、分钟、秒。

- `Human Vs AI`
  玩家与 AI 同场竞争食物、生存和路线控制。

- `Local Duel`
  两名玩家在同一台电脑上对战。

- `Co-op Run`
  两名玩家合作冲击团队目标分数。

### 2.2 联机模式
- `LAN Host`
  在局域网内创建房间，等待别人加入。

- `LAN Join`
  输入主机 IP，或从自动发现列表中加入房间。

### 2.3 高级模式
- `Rhythm Mode`
  节奏模式。蛇移动、食物刷新会跟随节拍，支持音乐文件。

- `Strategy Mode`
  策略模式。包含技能点、随机事件、AI 策略偏向等玩法。

---

## 3. 技术栈

本项目主要使用了这些模块：

- `pygame`
  游戏窗口、绘图、按键、时钟、音频播放

- `socket`
  局域网联机、房间广播、主机与客户端通信

- `json`
  保存分数、胜率、道具使用次数等统计数据

- `pathlib`
  处理资源路径、数据路径、打包后路径

- `dataclasses`
  节奏模式、策略模式、难度配置等数据结构

- `collections.deque`
  AI 路径搜索中的 BFS 队列

- `random`
  随机事件、房间码、食物刷新、技能卡抽取

- `time`
  局域网房间广播与发现

---

## 4. 项目目录结构

```text
snake_game/
├─ main.py
├─ ui.py
├─ game.py
├─ settings.py
├─ README.md
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

---

## 5. 每个文件是做什么的

### 根目录
- `main.py`
  程序入口，运行项目时最先执行这个文件。

- `ui.py`
  注册高级模式并启动游戏。

- `game.py`
  整个游戏的核心控制器。
  负责菜单、状态切换、开始设置、暂停、结算、联机逻辑接线、模式切换。

- `settings.py`
  全局配置中心。
  包含窗口大小、颜色、模式列表、食物库、难度、路径配置、端口号等。

### entities
- `entities/snake.py`
  蛇实体。
  管理蛇的身体、方向、分数、成长、状态效果。

- `entities/food.py`
  食物实体。
  管理食物位置、种类、分值、效果、生命周期。

### systems
- `systems/renderer.py`
  所有界面绘制都在这里。
  包括主菜单、设置页、游戏内 HUD、暂停页、结算页、联机页。

- `systems/ai_controller.py`
  AI 决策模块。
  使用 BFS 找路径，并带有避险和保命逻辑。

- `systems/collision.py`
  处理碰撞、传送门解析等规则。

- `systems/data_store.py`
  本地统计存档模块。
  负责读取和保存 `player_stats.json`。

- `systems/game_modes.py`
  模式骨架和难度配置。
  包含简单 / 普通 / 困难三档难度。

- `systems/localization.py`
  多语言文本管理。
  当前支持中文、英文、德文。

- `systems/network_session.py`
  局域网联机模块。
  负责主机开房、客户端加入、房间广播、房间发现、同步消息。

- `systems/rhythm_mode.py`
  节奏模式逻辑。
  负责节拍推进、连击、节拍 HUD、音乐读取和播放。

- `systems/strategy_mode.py`
  策略模式逻辑。
  负责技能点、技能卡、随机事件、AI 偏向调节。

- `systems/input_handler.py`
  输入辅助模块，用于方向键到移动方向的映射。

### utils
- `utils/helpers.py`
  通用工具函数。
  包含方向常量、边界判断、距离计算等。

---

## 6. 如何运行项目

### 6.1 环境要求
- Windows 10 / 11
- Python 3.11 或 3.12
- 已安装 `pygame`

### 6.2 安装依赖
```powershell
pip install pygame
```

### 6.3 启动项目
进入项目目录后运行：

```powershell
cd snake_game
python main.py
```

如果你使用的是虚拟环境：

```powershell
cd snake_game
..\ .venv\Scripts\python.exe main.py
```

实际命令中间不要有空格，正确写法是：

```powershell
cd snake_game
..\.venv\Scripts\python.exe main.py
```

---

## 7. 零基础复现步骤

如果你是第一次接触 Python 游戏项目，可以按下面做：

### 第一步：安装 Python
去 Python 官网安装 Python 3.11 或 3.12。  
安装时记得勾选“Add Python to PATH”。

### 第二步：下载项目
把这个仓库下载到本地，或者使用 Git：

```powershell
git clone <你的仓库地址>
```

### 第三步：进入项目目录
```powershell
cd snake-codex\snake_game
```

### 第四步：安装 pygame
```powershell
pip install pygame
```

### 第五步：启动游戏
```powershell
python main.py
```

### 第六步：开始玩
程序启动后会先进入语言选择界面。  
然后进入模式菜单，选择你想体验的模式即可。

---

## 8. 游戏操作说明

### 菜单界面
- `↑ / ↓`
  切换模式

- `← / →`
  切换语言或难度

- `Enter / Space`
  确认进入

- `Esc`
  返回上一级

### 对局中
- `方向键`
  玩家一移动

- `W A S D`
  玩家二移动

- `P`
  暂停 / 继续

- `R`
  立即重开当前模式

- `M`
  立即返回主菜单

- `Esc`
  立即返回主菜单

- `Tab`
  显示 / 隐藏 AI 路径预测

### 暂停 / 结算 / 设置页
这些快捷键已经做成全局中断设计：
- `P` 可以继续
- `R` 可以重开
- `M` 或 `Esc` 可以回菜单

---

## 9. 道具与特殊元素说明

### 食物类型
- `Apple`
  基础食物，普通加分

- `Gold Fruit`
  高分食物，分更多，成长更多

- `Phase Fruit`
  穿越效果，短时间可穿障碍

- `Freeze Fruit`
  让对手减速

- `Haste Fruit`
  自己加速

- `Bounce Fruit`
  撞墙时可反弹一次

- `Magnet Fruit`
  吸附附近食物

### 地图元素
- `障碍物`
  不能直接穿过，碰到会死亡

- `传送门`
  从一个入口瞬移到另一个出口

---

## 10. 三档难度说明

项目内置三档难度：

- `Easy`
  蛇更慢，食物刷新更慢，障碍更少

- `Normal`
  默认难度，节奏最平衡

- `Hard`
  蛇更快，特殊食物更多，障碍更多

HUD 中会显示当前难度。

---

## 11. AI 是怎么工作的

本项目的 AI 不是简单随机乱走，而是做了几步判断：

- 先找离食物的路径
- 判断这条路径是否安全
- 检查吃完以后还能不能逃出来
- 避开对手下一步可能到达的位置
- 如果吃食物不安全，就优先找更大的安全空间保命

用到的核心算法：
- `BFS（广度优先搜索）`
- `危险区域规避`
- `可达空间评估`
- `保命优先 fallback 策略`

这部分代码主要在：
- `systems/ai_controller.py`

---

## 12. 节奏模式是怎么做的

节奏模式会把游戏推进和节拍绑定起来：

- 根据 BPM 计算每拍间隔
- 每到节拍时，允许蛇移动
- 每隔若干拍刷新食物
- 吃到食物时计算节拍命中质量
- 显示 `Perfect / Good / Miss`
- HUD 显示当前拍点、连击、最佳连击

音乐文件放在：

```text
assets/music/
```

支持格式：
- `.ogg`
- `.mp3`
- `.wav`

这部分代码主要在：
- `systems/rhythm_mode.py`

---

## 13. 策略模式是怎么做的

策略模式加入了更像策略游戏的系统：

- 每条蛇有 `技能点`
- 吃食物或道具可以获得技能点
- 可以触发技能卡
- 会出现随机事件
- 事件有不同分支选择
- AI 会根据当前策略偏向改变行为

例如：
- 更激进：更喜欢抢食物
- 更保守：更重视生存空间

这部分代码主要在：
- `systems/strategy_mode.py`

---

## 14. 局域网联机是怎么做的

本项目支持局域网主机 / 加入。

实现方式：

- 主机使用 TCP 开房
- 客户端连接主机
- 主机负责发送快照
- 客户端发送输入方向
- 使用 UDP 广播做房间发现
- 自动生成房间码
- 房间列表可以显示实时状态

相关文件：
- `systems/network_session.py`

---

## 15. 数据是怎么保存的

项目会把统计数据写到：

```text
data/player_stats.json
```

保存内容包括：
- 总局数
- 总吃到食物数
- 最高分
- 各模式最佳成绩
- 玩家胜率
- AI 胜率
- 合作通关次数
- 道具使用次数

相关文件：
- `systems/data_store.py`

---

## 16. 程序主流程是怎样的

整个游戏大致按下面流程运行：

1. `main.py` 启动程序
2. `ui.py` 注册模式并创建游戏对象
3. `game.py` 初始化窗口、菜单、状态
4. `renderer.py` 负责渲染当前界面
5. 玩家输入交给 `game.py`
6. AI 使用 `ai_controller.py` 决策
7. 碰撞由 `collision.py` 处理
8. 数据由 `data_store.py` 保存
9. 如果是联机模式，使用 `network_session.py` 同步
10. 如果是节奏 / 策略模式，则额外调用对应模式模块

---

## 17. 适合初学者学习的知识点

如果你是零基础，这个项目很适合你学这些内容：

- Python 项目结构怎么拆分
- pygame 基本窗口和主循环
- 键盘事件处理
- 游戏状态机设计
- 面向对象封装
- AI 路径搜索
- JSON 数据存档
- 多语言界面
- 局域网联机基础
- 打包成 Windows 可执行程序

---

## 18. 常见问题

### 运行报错：`No module named pygame`
说明没有安装 pygame：

```powershell
pip install pygame
```

### 打开后中文乱码
项目已经优先选择支持中文的系统字体。  
如果个别机器依然异常，请检查系统是否安装了常见中文字体，例如微软雅黑。

### 局域网联机找不到房间
请检查：
- 两台电脑是否在同一局域网
- 防火墙是否阻止了端口
- 主机是否已成功开房
- 端口是否被其他程序占用

### 音乐不播放
请确认：
- `assets/music/` 中确实有音频文件
- 文件格式为 `.ogg` / `.mp3` / `.wav`
- 本机声卡和 `pygame.mixer` 正常

---

## 19. 打包为 Windows 应用

项目已经提供 PyInstaller 打包脚本：

```powershell
.\.venv\Scripts\python.exe build_windows.py
```

单文件版本：

```powershell
.\.venv\Scripts\python.exe build_windows.py --onefile
```

说明：
- 入口文件是 `snake_game/main.py`
- `assets/`、`data/` 都会一起打包
- 打包后 Windows 可直接运行
- 统计 JSON 会写到 exe 同级目录下的 `data/`

---

## 20. 未来可以继续扩展什么

你还可以继续加这些内容：

- 更多地图主题
- 音效和粒子特效
- 在线联机
- 更强的 AI
- 自定义按键
- 排行榜
- BOSS 模式
- 剧情关卡模式
- 回放系统
- 成就系统

---

## 21. 致谢

本项目基于：
- Python
- pygame

如果你喜欢这个项目，欢迎 Star、Fork，或者继续把它改造成你自己的完整游戏作品。
