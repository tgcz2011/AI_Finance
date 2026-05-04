from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.core.enums import ModuleStatus
from src.core.types.result import Ok, Err, Result


@dataclass(frozen=True)
class ModuleMeta:
    module_id: str
    name: str
    description: str
    dependencies: frozenset[str]
    default_enabled: bool
    is_core: bool


class ModuleDisabledError(Exception):
    pass


class DependencyCheckResult:
    def __init__(self, satisfied: bool, missing: frozenset[str] = frozenset()) -> None:
        self.satisfied = satisfied
        self.missing = missing


class ModuleRegistry:
    def __init__(self) -> None:
        self._modules: dict[str, ModuleMeta] = {}
        self._statuses: dict[str, ModuleStatus] = {}
        self._instances: dict[str, object] = {}

    def register(self, meta: ModuleMeta) -> None:
        self._modules[meta.module_id] = meta
        if meta.module_id not in self._statuses:
            self._statuses[meta.module_id] = (
                ModuleStatus.RUNNING if meta.default_enabled else ModuleStatus.DISABLED
            )

    def check_dependencies(self, module_id: str) -> DependencyCheckResult:
        meta = self._modules.get(module_id)
        if meta is None:
            return DependencyCheckResult(False, frozenset({module_id}))
        missing = frozenset(
            dep for dep in meta.dependencies
            if not self.is_enabled(dep)
        )
        return DependencyCheckResult(satisfied=len(missing) == 0, missing=missing)

    def enable(self, module_id: str) -> Result[None]:
        meta = self._modules.get(module_id)
        if meta is None:
            return Err(f"Module {module_id} not registered")
        dep_result = self.check_dependencies(module_id)
        if not dep_result.satisfied:
            return Err(f"Dependencies not satisfied: {dep_result.missing}")
        self._statuses[module_id] = ModuleStatus.RUNNING
        return Ok(None)

    def disable(self, module_id: str, force: bool = False) -> Result[None]:
        meta = self._modules.get(module_id)
        if meta is None:
            return Err(f"Module {module_id} not registered")
        if meta.is_core and not force:
            return Err(f"Cannot disable core module {module_id}")
        dependents = [
            mid for mid, m in self._modules.items()
            if module_id in m.dependencies and self.is_enabled(mid)
        ]
        if dependents and not force:
            return Err(f"Module {module_id} is depended on by: {dependents}")
        self._statuses[module_id] = ModuleStatus.DISABLED
        return Ok(None)

    def get_status(self, module_id: str) -> ModuleStatus:
        return self._statuses.get(module_id, ModuleStatus.STOPPED)

    def get_all_status(self) -> dict[str, ModuleStatus]:
        return dict(self._statuses)

    def is_enabled(self, module_id: str) -> bool:
        return self._statuses.get(module_id) == ModuleStatus.RUNNING

    def get_meta(self, module_id: str) -> ModuleMeta | None:
        return self._modules.get(module_id)

    def get_all_modules(self) -> dict[str, ModuleMeta]:
        return dict(self._modules)


def register_all_modules(registry: ModuleRegistry) -> None:
    modules = [
        ModuleMeta("storage", "存储管理", "SQLite WAL模式数据持久化", frozenset(), True, True),
        ModuleMeta("crypto", "加密管理", "API Key AES-256加密存储", frozenset(), True, True),
        ModuleMeta("config", "配置管理", "YAML配置加载与校验", frozenset({"storage", "crypto"}), True, True),
        ModuleMeta("wal", "WAL管理", "预写日志与原子操作保障", frozenset({"storage"}), True, True),
        ModuleMeta("module_manager", "模块管理", "模块注册启停与依赖检查", frozenset({"config"}), True, True),
        ModuleMeta("account", "账户管理", "多币种账户与资产折算", frozenset({"storage", "config"}), True, True),
        ModuleMeta("trade_validator", "交易校验", "交易规则校验与拦截", frozenset({"data_fetcher", "account", "config"}), True, True),
        ModuleMeta("trade_executor", "交易执行", "原子性交易执行与费用计算", frozenset({"account", "loan", "wal", "config"}), True, True),
        ModuleMeta("risk", "风控引擎", "多规则风控检查与熔断", frozenset({"account", "config"}), True, True),
        ModuleMeta("data_fetcher", "数据接入", "多市场数据拉取与容错", frozenset({"config", "logging"}), True, False),
        ModuleMeta("ai_adapter", "AI适配", "AI决策请求与上下文压缩", frozenset({"data_fetcher", "account", "config", "logging"}), True, False),
        ModuleMeta("loan", "借贷管理", "贷款发放计息与强平", frozenset({"account", "trade_executor", "config"}), True, False),
        ModuleMeta("scheduler", "模拟调度", "实时/回测调度与多周期决策", frozenset({"data_fetcher", "ai_adapter", "trade_validator", "trade_executor", "risk", "loan", "config"}), True, False),
        ModuleMeta("contest", "竞赛管理", "多AI竞赛与多轮淘汰", frozenset({"scheduler", "account", "config"}), True, False),
        ModuleMeta("snapshot", "快照管理", "状态快照与恢复", frozenset({"storage", "config"}), True, False),
        ModuleMeta("report", "报告可视化", "绩效统计与图表导出", frozenset({"storage", "config"}), True, False),
        ModuleMeta("logging", "日志监控", "日志记录与实时监控", frozenset({"storage", "config"}), True, False),
        ModuleMeta("version_control", "版本管理", "Git/GitHub数据同步", frozenset({"config", "logging"}), False, False),
    ]
    for meta in modules:
        registry.register(meta)
