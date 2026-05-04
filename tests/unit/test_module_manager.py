import pytest
from unittest.mock import MagicMock, AsyncMock

from src.core.enums import ModuleStatus
from src.infrastructure.module_manager.registry import (
    ModuleMeta, ModuleRegistry, ModuleDisabledError,
    DependencyCheckResult, register_all_modules,
)
from src.infrastructure.module_manager.proxy import ModuleProxy


class TestModuleMeta:
    def test_frozen_dataclass(self):
        meta = ModuleMeta(
            module_id="test",
            name="Test Module",
            description="A test module",
            dependencies=frozenset({"dep1"}),
            default_enabled=True,
            is_core=False,
        )
        with pytest.raises(AttributeError):
            meta.module_id = "changed"

    def test_dependencies_is_frozenset(self):
        meta = ModuleMeta(
            module_id="test", name="Test", description="",
            dependencies=frozenset({"a", "b"}),
            default_enabled=True, is_core=False,
        )
        assert isinstance(meta.dependencies, frozenset)


class TestModuleRegistry:
    def _make_registry(self):
        registry = ModuleRegistry()
        registry.register(ModuleMeta("a", "A", "", frozenset(), True, True))
        registry.register(ModuleMeta("b", "B", "", frozenset({"a"}), True, False))
        registry.register(ModuleMeta("c", "C", "", frozenset({"a", "b"}), True, False))
        registry.register(ModuleMeta("d", "D", "", frozenset(), False, False))
        return registry

    def test_register_and_get_status(self):
        registry = self._make_registry()
        assert registry.is_enabled("a") is True
        assert registry.is_enabled("d") is False

    def test_enable_module(self):
        registry = self._make_registry()
        assert registry.is_enabled("d") is False
        result = registry.enable("d")
        assert result.is_ok
        assert registry.is_enabled("d") is True

    def test_disable_non_core_module(self):
        registry = self._make_registry()
        result = registry.disable("c")
        assert result.is_ok
        assert registry.is_enabled("c") is False

    def test_disable_core_module_rejected(self):
        registry = self._make_registry()
        result = registry.disable("a")
        assert result.is_err

    def test_disable_core_module_forced(self):
        registry = self._make_registry()
        result = registry.disable("a", force=True)
        assert result.is_ok

    def test_disable_depended_module_rejected(self):
        registry = self._make_registry()
        result = registry.disable("a")
        assert result.is_err
        result2 = registry.disable("b")
        assert result2.is_err

    def test_check_dependencies_satisfied(self):
        registry = self._make_registry()
        result = registry.check_dependencies("b")
        assert result.satisfied

    def test_check_dependencies_not_satisfied(self):
        registry = self._make_registry()
        registry.disable("a", force=True)
        result = registry.check_dependencies("b")
        assert not result.satisfied
        assert "a" in result.missing

    def test_get_all_status(self):
        registry = self._make_registry()
        status = registry.get_all_status()
        assert len(status) == 4

    def test_register_all_modules(self):
        registry = ModuleRegistry()
        register_all_modules(registry)
        status = registry.get_all_status()
        assert len(status) == 18
        assert registry.is_enabled("account") is True
        assert registry.is_enabled("version_control") is False


class TestModuleProxy:
    def test_enabled_module_forwards_calls(self):
        registry = ModuleRegistry()
        registry.register(ModuleMeta("test", "Test", "", frozenset(), True, False))
        mock_module = MagicMock()
        mock_module.do_something.return_value = 42
        proxy = ModuleProxy(registry, "test", mock_module)
        assert proxy.do_something() == 42

    def test_disabled_module_raises_error(self):
        registry = ModuleRegistry()
        registry.register(ModuleMeta("test", "Test", "", frozenset(), True, False))
        mock_module = MagicMock()
        proxy = ModuleProxy(registry, "test", mock_module)
        registry.disable("test")
        with pytest.raises(ModuleDisabledError):
            proxy.do_something()

    def test_proxy_is_enabled_property(self):
        registry = ModuleRegistry()
        registry.register(ModuleMeta("test", "Test", "", frozenset(), True, False))
        proxy = ModuleProxy(registry, "test")
        assert proxy.is_enabled is True
        registry.disable("test")
        assert proxy.is_enabled is False
