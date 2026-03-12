from dataclasses import dataclass, field


@dataclass
class SystemSettings:
    directory: str = ""
    account_number: int = 3


@dataclass
class AppearanceSettings:
    language: str = "en"
    theme: str = "dark"
    show_id_section: bool = True


@dataclass
class BehaviorSettings:
    minimize_on_apply: bool = False
    preload_next_page: bool = True


@dataclass
class DebugSettings:
    debug_mode: bool = False


@dataclass
class GeneralSettings:
    appearance: AppearanceSettings = field(default_factory=AppearanceSettings)
    behavior: BehaviorSettings = field(default_factory=BehaviorSettings)
    debug: DebugSettings = field(default_factory=DebugSettings)


@dataclass
class ApplicationSettings:
    system: SystemSettings = field(default_factory=SystemSettings)
    general: GeneralSettings = field(default_factory=GeneralSettings)