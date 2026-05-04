from __future__ import annotations

from typing import Any

from src.infrastructure.module_manager.registry import ModuleDisabledError, ModuleRegistry


class ModuleProxy:
    def __init__(self, registry: ModuleRegistry, module_id: str, real_module: Any = None) -> None:
        self._registry = registry
        self._module_id = module_id
        self._real_module = real_module

    def __getattr__(self, name: str) -> Any:
        if not self._registry.is_enabled(self._module_id):
            raise ModuleDisabledError(f"模块 {self._module_id} 已禁用, 无法调用 {name}")
        if self._real_module is None:
            raise AttributeError(f"Module {self._module_id} has no real implementation")
        return getattr(self._real_module, name)

    def set_real_module(self, module: Any) -> None:
        object.__setattr__(self, "_real_module", module)

    @property
    def module_id(self) -> str:
        return self._module_id

    @property
    def is_enabled(self) -> bool:
        return self._registry.is_enabled(self._module_id)
