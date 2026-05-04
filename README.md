# AI 金融模拟竞赛系统

多市场、多 AI 并行的自动化模拟投资竞赛环境。AI 作为唯一决策者，系统负责数据供给、交易校验、费用计算、借贷管理和绩效统计。

## 特性

- **多市场交易**：A股（AKShare）、美股（yfinance）、加密货币（CoinGecko/Binance）
- **多 AI 竞赛**：同时运行多个 AI 选手，独立账户、独立决策通道
- **人民币本位**：初始资金 CNY，跨币种兑换模拟真实银行点差损耗
- **真实费用模型**：佣金、印花税、滑点、兑换费，各市场独立配置
- **贷款机制**：自动贷款、日复利计息、质押率监控、强制平仓
- **全面风控**：回撤熔断、持仓集中度限制、日亏损限额、异常频率检测、极端行情暂停
- **AI 上下文压缩**：4级优先级分层，关键指令前置，避免上下文过长丢失目标
- **WAL 容错**：预写日志保障交易原子性，异常重启自动恢复
- **模块化设计**：18个功能模块，每个可独立启用/禁用
- **GUI 界面**：PyQt6 跨平台 GUI，实时排行榜、资产曲线、配置编辑
- **Git/GitHub 集成**：数据自动提交、远程同步、Issue 跟踪
- **跨平台**：Windows / macOS / Linux 一致运行

## 快速开始

### 环境要求

- Python 3.11+
- pip

### 安装

```bash
# 克隆项目
git clone <repo-url>
cd AI_Finance

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 安装依赖
pip install -e ".[dev]"
```

### 配置

编辑 `config/system.yaml` 调整系统参数：

```yaml
initial_capital_cny: "1000000"   # 初始资金
simulation_mode: REALTIME        # REALTIME 或 BACKTEST
spread_bps: "0.004"             # 兑换点差

modules:
  version_control: false         # 需Git时启用
```

AI 选手配置在 `config/ai_players.yaml`，支持 OpenAI 兼容接口（包括本地 Ollama）。

### 启动

#### 方式一：直接运行（开发模式）

```bash
# 安装依赖后
python -m src.main
```

#### 方式二：打包为可执行文件（PyInstaller）

```bash
# 安装打包工具
pip install pyinstaller

# 打包（macOS/Linux）
pyinstaller --name AI-Finance-Simulator --noconfirm --windowed --onedir \
  --add-data "config:config" \
  --hidden-import sqlalchemy.dialects.sqlite \
  --hidden-import aiosqlite \
  src/main.py

# 打包（Windows PowerShell）
pyinstaller --name AI-Finance-Simulator --noconfirm --windowed --onedir `
  --add-data "config;config" `
  --hidden-import sqlalchemy.dialects.sqlite `
  --hidden-import aiosqlite `
  src/main.py

# 运行
./dist/AI-Finance-Simulator/AI-Finance-Simulator
```

#### 方式三：下载Release版本

前往 [GitHub Releases](https://github.com/tgcz2011/AI_Finance/releases) 下载对应平台的可执行文件。

#### 方式四：通过GitHub Actions自动构建

推送tag即可触发自动构建并发布Release：

```bash
git tag v0.1.0
git push origin v0.1.0
```

## 测试

```bash
# 全部测试
pytest tests/ -v

# 单元测试
pytest tests/unit/ -v

# 集成测试
pytest tests/integration/ -v

# 带覆盖率
pytest tests/ --cov=src --cov-report=term-missing
```

## 项目结构

```
src/
├── core/                    # 核心模块
│   ├── types/              # Result[T]、EventBus
│   ├── account/            # 多币种账户与资产管理
│   ├── trade_validator/    # 交易规则校验
│   ├── trade_executor/     # 手续费计算与滑点
│   ├── risk/               # 风控引擎（5条规则）
│   └── wal/                # WAL预写日志与恢复
├── business/               # 业务模块
│   ├── loan/               # 借贷管理（自动贷款/强平）
│   ├── data_fetcher/       # 数据接入（免费优先+容错）
│   ├── ai_adapter/         # AI接口适配（上下文压缩）
│   ├── scheduler/          # 模拟调度（实时/回测）
│   └── contest/            # 竞赛管理（多轮/淘汰/积分）
├── auxiliary/              # 辅助模块
│   ├── snapshot/           # 状态快照与恢复
│   ├── logging_/           # 日志记录与脱敏
│   ├── report/             # 绩效报告与导出
│   └── version_control/    # Git/GitHub版本管理
├── infrastructure/         # 基础设施
│   ├── storage/            # SQLite WAL存储（15张表）
│   ├── crypto_/            # AES-256加密管理
│   ├── config/             # YAML配置+pydantic校验
│   └── module_manager/     # 模块注册表与代理
├── gui/                    # GUI层
│   ├── bridge.py           # asyncio/Qt事件循环桥接
│   ├── main_window.py      # PyQt6主窗口
│   ├── views/              # 8个核心视图
│   └── widgets/            # 可复用组件
└── main.py                 # 应用入口

config/
├── system.yaml             # 系统配置
├── modules.yaml            # 模块开关
├── ai_players.yaml         # AI选手配置
└── prompts/                # 提示词模板

tests/
├── unit/                   # 单元测试（200个）
└── integration/            # 集成测试
```

## 核心原则

1. **AI 无成本感知**：AI 不知道 token 消耗，决策不受成本影响
2. **强错误拦截**：非法指令静默拦截并记录，不干扰模拟运行
3. **人民币本位**：所有资产最终按银行买入价折算回 CNY
4. **高精度计算**：所有金额使用 `decimal.Decimal`，禁止浮点数
5. **模块化优先**：高内聚低耦合，模块可独立启停
6. **跨平台兼容**：不依赖操作系统专有特性

## 技术栈

| 领域 | 选型 |
|------|------|
| 语言 | Python 3.11+ |
| GUI | PyQt6 + qasync |
| 存储 | SQLite (WAL模式) + SQLAlchemy 2.0 |
| 定点小数 | decimal.Decimal (prec=28) |
| 配置 | PyYAML + pydantic |
| 异步 | asyncio + httpx |
| 数据源 | AKShare / yfinance / CoinGecko (免费优先) |
| AI接口 | OpenAI SDK (兼容协议) |
| 加密 | cryptography (AES-256 Fernet) |
| 图表 | matplotlib + pyqtgraph |
| Git | GitPython + PyGithub |
| 测试 | pytest + pytest-asyncio + pytest-cov |
| CI/CD | GitHub Actions (跨平台矩阵) |

## 许可证

MIT License
