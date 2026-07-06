from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class StartupPatchContext:
    app_class: object
    ctk_class: object
    lazy_tab_specs: dict
    default_startup_tab: str
    debug: object
    get_internal_attr: object
    ensure_lazy_tab_initialized: object
    show_inline_help: object
    show_inline_donate: object
    set_help_button_selected: object
    set_donate_button_selected: object
    set_help_action_state: object
    refresh_output_strategy_hint: object
    refresh_parallel_mode_hint: object
    refresh_visible_tab_layout: object
    guess_lazy_tab_for_attr: object
    record_performance: object
    defer_default_tab: bool = True


def _call(callback, *args, **kwargs):
    if callable(callback):
        return callback(*args, **kwargs)
    return None


def install_startup_performance_patch(context):
    """Install hidden-startup and lazy-tab patches for the loader shell."""
    debug = context.debug
    app_class = context.app_class
    ctk_class = context.ctk_class

    try:
        original_setup_main_area = app_class.setup_main_area
        original_switch_tab = app_class.switch_tab
        original_ctk_init = ctk_class.__init__
    except Exception as exc:
        _call(debug, f"patch_startup_performance:missing:{exc}")
        return False

    original_getattr = getattr(app_class, "__getattr__", None)

    if getattr(original_setup_main_area, "__fx_lazy_startup_patch__", False):
        return False

    def patched_show_readme(self):
        return _call(context.show_inline_help, self)

    def patched_show_donate_window(self):
        return _call(context.show_inline_donate, self)

    def patched_ctk_init(self, *args, **kwargs):
        original_ctk_init(self, *args, **kwargs)
        if _call(context.get_internal_attr, self, "_fx_start_hidden", False):
            return
        try:
            self.withdraw()
            self._fx_start_hidden = True
            _call(debug, "startup:window_hidden")
        except Exception as exc:
            _call(debug, f"startup:window_hidden_error:{exc}")

    def patched_setup_main_area(self):
        self._fx_lazy_tabs_state = {name: False for name in context.lazy_tab_specs}
        self._fx_lazy_tab_initializers = {}
        self._fx_lazy_tabs_initializing = set()
        self._fx_lazy_startup_in_progress = True
        self._fx_startup_visible_pending = True
        try:
            for task_name, spec in context.lazy_tab_specs.items():
                init_name = spec["init"]
                initializer = getattr(self, init_name, None)
                if callable(initializer):
                    self._fx_lazy_tab_initializers[task_name] = initializer
                if task_name == context.default_startup_tab and not context.defer_default_tab:
                    continue

                def deferred_init(_task_name=task_name):
                    _call(debug, f"lazy_tab:deferred:{_task_name}")
                    return None

                setattr(self, init_name, deferred_init)

            result = original_setup_main_area(self)
            default_already_ready = bool(self._fx_lazy_tabs_state.get(context.default_startup_tab))
            self._fx_lazy_tabs_state[context.default_startup_tab] = (
                default_already_ready or not context.defer_default_tab
            )
            self._fx_lazy_startup_ready = True
            return result
        finally:
            self._fx_lazy_startup_in_progress = False
            for task_name, initializer in self._fx_lazy_tab_initializers.items():
                try:
                    setattr(self, context.lazy_tab_specs[task_name]["init"], initializer)
                except Exception:
                    pass

    def patched_switch_tab(self, task_name, btn_obj):
        started_at = time.perf_counter()
        status = "success"
        try:
            if not (
                _call(context.get_internal_attr, self, "_fx_lazy_startup_in_progress", False)
                and task_name == context.default_startup_tab
            ):
                _call(context.ensure_lazy_tab_initialized, self, task_name)
        except Exception as exc:
            status = "lazy_init_error"
            _call(debug, f"lazy_tab:switch_error:{task_name}:{exc}")
        try:
            result = original_switch_tab(self, task_name, btn_obj)
            try:
                _call(context.set_help_button_selected, self, False)
                _call(context.set_donate_button_selected, self, False)
                _call(context.set_help_action_state, self, False)
                _call(context.refresh_output_strategy_hint, self)
                _call(context.refresh_parallel_mode_hint, self)
                _call(context.refresh_visible_tab_layout, self, task_name)
                self.update_idletasks()
            except Exception as exc:
                status = "layout_refresh_error"
                _call(debug, f"lazy_tab:visible_layout_refresh_error:{task_name}:{exc}")
            return result
        except Exception:
            status = "error"
            raise
        finally:
            _call(
                context.record_performance,
                "switch_tab",
                started_at=started_at,
                task_name=task_name,
                details={"status": status},
            )

    def patched_getattr(self, name):
        task_name = _call(context.guess_lazy_tab_for_attr, name)
        if task_name is not None:
            lazy_initializing = _call(context.get_internal_attr, self, "_fx_lazy_tabs_initializing", None) or set()
            if task_name in lazy_initializing:
                raise AttributeError(f"{type(self).__name__!s} object has no attribute {name!r}")
            try:
                _call(context.ensure_lazy_tab_initialized, self, task_name)
                return object.__getattribute__(self, name)
            except AttributeError:
                pass
            except Exception as exc:
                _call(debug, f"lazy_tab:getattr_error:{name}:{exc}")
        if callable(original_getattr):
            return original_getattr(self, name)
        raise AttributeError(f"{type(self).__name__!s} object has no attribute {name!r}")

    patched_ctk_init.__fx_hidden_startup_patch__ = True
    patched_setup_main_area.__fx_lazy_startup_patch__ = True
    patched_switch_tab.__fx_lazy_startup_patch__ = True
    patched_getattr.__fx_lazy_startup_patch__ = True
    patched_show_readme.__fx_inline_help_patch__ = True
    patched_show_donate_window.__fx_inline_donate_patch__ = True
    ctk_class.__init__ = patched_ctk_init
    app_class.setup_main_area = patched_setup_main_area
    app_class.switch_tab = patched_switch_tab
    app_class.__getattr__ = patched_getattr
    app_class.show_readme = patched_show_readme
    app_class.show_donate_window = patched_show_donate_window
    _call(debug, "patch_startup_performance:installed")
    return True
