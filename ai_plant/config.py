"""
Configuration Manager for AI Companion Plant Widget
Handles loading, saving, and defaults from config.json.
"""
import os
import json
import sys

DEFAULT_CONFIG = {
    "api_endpoint": "https://dev.ai.go.kr/api/v1/chat/completions",
    "api_key": "",
    "model": "gov-gpt-4o",
    "ssl_verify": False,  # Useful for closed/internal networks (행정망/업무망 사설 인증서 대응)
    "timeout_sec": 5,
    "decay_interval_minutes": 30,
    "water_decay_per_interval": 3,
    "sunlight_decay_per_interval": 3,
    "affection_decay_per_interval": 1,
    "always_on_top": True,
    "sound_enabled": True,
    "user_nickname": "공직자님",
    "plant_name": "초록이",
    "bubble_duration_sec": 4,
    "window_pos_x": -1,
    "window_pos_y": -1,
    "compact_hover_mode": True,  # 화분만 보이다 마우스 오버 시 메뉴 등장
    "ghost_mode": False,          # 평소 반투명(고스트) 모드
    "hourly_peek": True,         # 매 정시 5초간 스트레칭/리프레시 알림
    "idle_peek": True,           # PC 3분 유휴 감지 시 힐링 인사 알림
    "plant_scale": 100,          # 화분 크기 비율 (70% ~ 150%)
    "initial_setup_done": False  # 최초 실행 시 이름/품종 설정 완료 여부
}

def get_base_dir() -> str:
    """Get the base directory whether running from source or frozen PyInstaller executable."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller bundle."""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # PyInstaller bundled assets
        bundle_path = os.path.join(sys._MEIPASS, relative_path)
        if os.path.exists(bundle_path):
            return bundle_path
    
    # Check next to executable / project root
    base_dir = get_base_dir()
    direct_path = os.path.join(base_dir, relative_path)
    if os.path.exists(direct_path):
        return direct_path
        
    return os.path.abspath(relative_path)

class ConfigManager:
    def __init__(self, config_file: str = "config.json"):
        self.config_path = os.path.join(get_base_dir(), config_file)
        self.config = dict(DEFAULT_CONFIG)
        self.load()

    def load(self):
        """Load configuration from JSON file or create with defaults."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    user_cfg = json.load(f)
                    self.config.update(user_cfg)
            except Exception as e:
                print(f"[ConfigManager] Error reading config: {e}. Using defaults.")
        else:
            self.save()

    def save(self):
        """Save current configuration to JSON file."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[ConfigManager] Error writing config: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value, auto_save=True):
        self.config[key] = value
        if auto_save:
            self.save()
