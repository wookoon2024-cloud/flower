"""
Configuration Manager for AI Companion Plant Widget
Handles loading, saving, and defaults from config.json.
Configured for CLOVA Studio GOV API (HCX-GOV-THINK-V1-32B), SSE streaming, and proactive speech.
API keys and secrets are securely encrypted and persisted inside SQLite (plant_data.db).
"""
import os
import json
import sys

DEFAULT_CONFIG = {
    "api_endpoint": "https://api.clovastudio.go.kr/api/v1/chat/completions",
    "api_key": "",
    "model": "HCX-GOV-THINK-V1-32B",
    "stream_enabled": True,       # Real-time SSE token streaming to speech bubble & chat dialog
    "ssl_verify": False,          # 행정망/업무망 사설 인증서 대응
    "timeout_sec": 10,
    "max_retries": 3,             # 429/5xx 지수 백오프 재시도 횟수
    "proactive_speech": True,     # 상태이상/랜덤넛지/점심/퇴근 자발적 말걸기 활성화
    "proactive_idle_minutes": 90, # 1.5시간(90분) 미조작 시 따뜻한 응원/스트레칭 권유 넛지
    "decay_interval_minutes": 30,
    "water_decay_per_interval": 3,
    "sunlight_decay_per_interval": 3,
    "affection_decay_per_interval": 1,
    "always_on_top": True,
    "sound_enabled": True,
    "user_nickname": "공직자님",
    "plant_name": "초록이",
    "bubble_duration_sec": 5,
    "window_pos_x": -1,
    "window_pos_y": -1,
    "compact_hover_mode": True,
    "ghost_mode": False,
    "hourly_peek": True,
    "idle_peek": True,
    "plant_scale": 100,
    "auto_start": True,
    "initial_setup_done": False
}

SENSITIVE_KEYS = {"api_key", "clova_api_key", "api_gateway_key", "clova_apigw_key", "secret_key"}

def get_base_dir() -> str:
    """Get the base directory whether running from source or frozen PyInstaller executable."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller bundle."""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        bundle_path = os.path.join(sys._MEIPASS, relative_path)
        if os.path.exists(bundle_path):
            return bundle_path
    
    base_dir = get_base_dir()
    direct_path = os.path.join(base_dir, relative_path)
    if os.path.exists(direct_path):
        return direct_path
        
    return os.path.abspath(relative_path)

class ConfigManager:
    def __init__(self, config_file: str = "config.json", db_manager=None):
        self.config_path = os.path.join(get_base_dir(), config_file)
        self.config = dict(DEFAULT_CONFIG)
        self.db = db_manager
        self.load()

    def set_db(self, db_manager):
        """Bind database manager for secure vault storage."""
        self.db = db_manager
        if self.db:
            # Sync sensitive keys from SQLite secure vault into memory
            for k in SENSITIVE_KEYS:
                val = self.db.get_secure_key(k, "")
                if val:
                    self.config[k] = val

    def load(self):
        """Load configuration from JSON file. Sensitive keys are loaded from SQLite secure vault."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    user_cfg = json.load(f)
                    
                    # If legacy config.json had an api_key, migrate it and clear from json
                    for k in SENSITIVE_KEYS:
                        if k in user_cfg and user_cfg[k]:
                            raw_val = user_cfg.pop(k)
                            if self.db:
                                self.db.set_secure_key(k, raw_val)
                            self.config[k] = raw_val
                    
                    self.config.update(user_cfg)
            except Exception as e:
                print(f"[ConfigManager] Error reading config: {e}. Using defaults.")
        else:
            self.save()

        # Load secrets from SQLite vault if DB is connected
        if self.db:
            for k in SENSITIVE_KEYS:
                val = self.db.get_secure_key(k, "")
                if val:
                    self.config[k] = val

    def save(self):
        """
        Save current non-sensitive configuration to JSON file.
        All API keys and secrets are saved inside SQLite secure_vault and omitted from config.json.
        """
        try:
            dump_data = dict(self.config)
            # Remove secrets from JSON output so config.json is 100% clean and public-safe
            for k in SENSITIVE_KEYS:
                if k in dump_data:
                    val = dump_data.pop(k)
                    if self.db and val:
                        self.db.set_secure_key(k, val)

            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(dump_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[ConfigManager] Error writing config: {e}")

    def get(self, key, default=None):
        if key in SENSITIVE_KEYS:
            if not self.config.get(key) and self.db:
                val = self.db.get_secure_key(key, "")
                if val:
                    self.config[key] = val
        return self.config.get(key, default)

    def set(self, key, value, auto_save=True):
        self.config[key] = value
        if key in SENSITIVE_KEYS and self.db:
            self.db.set_secure_key(key, value)
        if auto_save:
            self.save()


def set_autostart_registry(enable: bool):
    """Register or unregister app in Windows CurrentVersion/Run startup registry."""
    if sys.platform != "win32":
        return
    try:
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "MindKeeper_Flower"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
        if enable:
            if getattr(sys, 'frozen', False):
                exe_path = f'"{sys.executable}"'
            else:
                base_dir = get_base_dir()
                main_py = os.path.join(base_dir, "main.py")
                python_exe = sys.executable
                pythonw_exe = os.path.join(os.path.dirname(python_exe), "pythonw.exe")
                runner = pythonw_exe if os.path.exists(pythonw_exe) else python_exe
                exe_path = f'"{runner}" "{main_py}"'
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, exe_path)
        else:
            try:
                winreg.DeleteValue(key, app_name)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except Exception as e:
        print(f"[Autostart] Registry update error: {e}")


def is_autostart_registry_enabled() -> bool:
    """Check if app is registered in Windows CurrentVersion/Run registry."""
    if sys.platform != "win32":
        return False
    try:
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "MindKeeper_Flower"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
        val, _ = winreg.QueryValueEx(key, app_name)
        winreg.CloseKey(key)
        return bool(val)
    except Exception:
        return False
