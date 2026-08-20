"""
Plant Engine Module
Manages Tamagotchi-style local simulation, state decay, offline elapsed time calculation,
growth/evolution rules, multi-species support, plant graduation & garden collection,
daily fortunes, and 100-achievement tracking.
"""
import datetime
import random
from typing import Dict, Any, Tuple, Optional, List
from PySide6.QtCore import QObject, Signal

from .achievements_data import ACHIEVEMENTS_100, ACHIEVEMENT_CATEGORIES

STAGE_NAMES = {
    1: "🌱 씨앗 & 새싹 (1단계)",
    2: "🌿 어린 줄기 (2단계)",
    3: "🪴 자라나는 잎새 (3단계)",
    4: "🌷 첫 꽃망울 (4단계)",
    5: "🌸 탐스러운 개화 (5단계)",
    6: "👑 영광의 만개 & 결실 (6단계 마스터)"
}

STAGE_EXP_REQUIREMENTS = {
    1: (60, 20),     # Reach Stage 2
    2: (160, 35),    # Reach Stage 3
    3: (320, 50),    # Reach Stage 4
    4: (550, 70),    # Reach Stage 5
    5: (850, 90),    # Reach Stage 6 (Final Bloom)
    6: (999999, 100) # Max stage
}

SPECIES_INFO = {
    "classic": {
        "name": "다정한 화분",
        "emoji": "🌸",
        "desc": "은은한 핑크빛 꽃을 피우는 다정한 반려화분",
        "color": "#EC4899"
    },
    "sunflower": {
        "name": "햇살 해바라기",
        "emoji": "🌻",
        "desc": "언제나 밝고 긍정적인 에너지를 주는 황금빛 해바라기",
        "color": "#F59E0B"
    },
    "cactus": {
        "name": "동글 선인장",
        "emoji": "🌵",
        "desc": "사막에서도 꿋꿋하게 노란 꽃을 피우는 씩씩한 선인장",
        "color": "#10B981"
    },
    "clover": {
        "name": "행운의 클로버",
        "emoji": "🍀",
        "desc": "공직자님에게 매일 행운과 기적을 가져다주는 네잎클로버",
        "color": "#059669"
    },
    "cherry": {
        "name": "봄날 벚꽃나무",
        "emoji": "🌺",
        "desc": "봄바람처럼 따뜻하고 화사한 벚꽃을 피우는 화분",
        "color": "#F43F5E"
    }
}

ACHIEVEMENTS_DEF = ACHIEVEMENTS_100

DAILY_FORTUNES = [
    "🍀 오늘 기안하신 문서는 막힘없이 일사천리로 결재 완료될 운세입니다!",
    "✨ 오늘은 동료에게 따뜻한 칭찬 한마디를 건네보세요. 더 큰 기쁨이 돌아옵니다.",
    "☕ 피로가 몰려올 땐 향긋한 차 한 잔과 3분의 스트레칭이 최고의 보약입니다.",
    "🎯 오늘 집중력 최고조! 까다롭던 민원이나 업무도 명쾌하게 해결됩니다.",
    "🌟 뜻밖의 기분 좋은 칭찬이나 인정받는 순간이 찾아오는 하루입니다.",
    "💪 조금만 더 힘내세요! 공직자님의 보이지 않는 노력이 큰 가치를 만듭니다.",
    "🌈 퇴근길에 기분 좋은 행운이 기다리고 있습니다. 가벼운 발걸음으로 하루를 마무리해요.",
    "🌱 작은 씨앗이 꽃을 피우듯, 오늘 쏟은 정성이 멋진 결실로 이어질 거예요.",
    "☀️ 따사로운 햇살처럼 밝은 미소가 주변 사람들에게도 큰 힘이 됩니다.",
    "💡 복잡했던 고민에 번뜩이는 명쾌한 아이디어가 떠오를 길운입니다!"
]

class PlantEngine(QObject):
    # Signals for UI reaction
    state_changed = Signal(dict)
    evolved = Signal(int, str)  # (new_stage, message)
    warning_triggered = Signal(str) # (warning_message)
    interaction_occurred = Signal(str, str) # (action_name, bubble_text)
    achievement_unlocked = Signal(dict) # (achievement_info)

    def __init__(self, db_manager, config_manager):
        super().__init__()
        self.db = db_manager
        self.config = config_manager
        self.state = self.db.load_plant_state()
        
        # Interaction counters in session
        self.water_count = 0
        self.sun_count = 0
        self.pet_count = 0
        self.fortune_count = 0

        # Calculate offline decay upon initialization
        self.apply_offline_decay()
        self.check_achievements()

    def get_state(self) -> Dict[str, Any]:
        return self.state

    def get_species(self) -> str:
        return self.state.get("species", "classic")

    def apply_offline_decay(self):
        """Calculates state decay for the time elapsed while the app was closed."""
        last_updated_str = self.state.get("last_updated")
        if not last_updated_str:
            return

        try:
            last_updated = datetime.datetime.fromisoformat(last_updated_str)
        except Exception:
            last_updated = datetime.datetime.now()

        now = datetime.datetime.now()
        elapsed_seconds = (now - last_updated).total_seconds()

        if elapsed_seconds <= 60:
            return

        interval_sec = self.config.get("decay_interval_minutes", 30) * 60
        intervals_passed = int(elapsed_seconds // interval_sec)

        if intervals_passed > 0:
            # Cap intervals to avoid zeroing out completely after long breaks (max 48 intervals = 24 hours)
            capped_intervals = min(48, intervals_passed)
            
            water_decay = capped_intervals * self.config.get("water_decay_per_interval", 3)
            sun_decay = capped_intervals * self.config.get("sunlight_decay_per_interval", 3)
            aff_decay = capped_intervals * self.config.get("affection_decay_per_interval", 1)

            self.state["water"] = max(0, self.state["water"] - water_decay)
            self.state["sunlight"] = max(0, self.state["sunlight"] - sun_decay)
            self.state["affection"] = max(0, self.state["affection"] - aff_decay)
            self.state["last_updated"] = now.isoformat()
            
            self.save()
            print(f"[PlantEngine] Offline decay applied ({int(elapsed_seconds)}s elapsed): Water -{water_decay}, Sunlight -{sun_decay}, Affection -{aff_decay}")

    def tick_decay(self):
        """Regular tick decay triggered by timer during runtime."""
        self.state["water"] = max(0, self.state["water"] - self.config.get("water_decay_per_interval", 3))
        self.state["sunlight"] = max(0, self.state["sunlight"] - self.config.get("sunlight_decay_per_interval", 3))
        self.state["affection"] = max(0, self.state["affection"] - self.config.get("affection_decay_per_interval", 1))
        
        self.state["last_updated"] = datetime.datetime.now().isoformat()
        self.save()
        self.state_changed.emit(self.state)

        # Warnings for critical status
        if self.state["water"] <= 15:
            self.warning_triggered.emit("목이 말라요... 시원한 물 한 모금 주세요! 💧")
        elif self.state["sunlight"] <= 15:
            self.warning_triggered.emit("햇살이 그립네요... 창가 햇빛을 쬐어주세요! ☀️")

    # --- User Actions ---
    def give_water(self) -> Tuple[bool, str]:
        """User gives water to the plant."""
        if self.state["water"] >= 100:
            msg = "화분에 수분이 이미 가득 차 있어요! 💧✨"
            self.interaction_occurred.emit("water_full", msg)
            return False, msg

        self.water_count += 1
        self.db.increment_stat("total_water")
        self.state["water"] = min(100, self.state["water"] + 25)
        self.state["affection"] = min(100, self.state["affection"] + 5)
        self.state["exp"] += 15
        self.state["total_interactions"] += 1

        self.check_evolution()
        self.check_achievements()
        self.save()
        self.state_changed.emit(self.state)
        msg = "시원한 물을 마시고 생기를 되찾았어요! 💧🌱"
        self.interaction_occurred.emit("water", msg)
        return True, msg

    def give_sunlight(self) -> Tuple[bool, str]:
        """User gives sunlight to the plant."""
        if self.state["sunlight"] >= 100:
            msg = "따뜻한 햇빛을 이미 충분히 받았어요! ☀️✨"
            self.interaction_occurred.emit("sun_full", msg)
            return False, msg

        self.sun_count += 1
        self.db.increment_stat("total_sunlight")
        self.state["sunlight"] = min(100, self.state["sunlight"] + 25)
        self.state["affection"] = min(100, self.state["affection"] + 5)
        self.state["exp"] += 15
        self.state["total_interactions"] += 1

        self.check_evolution()
        self.check_achievements()
        self.save()
        self.state_changed.emit(self.state)
        msg = "따뜻한 햇빛을 받아 광합성 완료! ☀️🌿"
        self.interaction_occurred.emit("sunlight", msg)
        return True, msg

    def pet(self) -> Tuple[bool, str]:
        """User pets/touches the plant."""
        self.pet_count += 1
        self.db.increment_stat("total_pet")
        self.state["affection"] = min(100, self.state["affection"] + 15)
        self.state["exp"] += 10
        self.state["total_interactions"] += 1

        self.check_evolution()
        self.check_achievements()
        self.save()
        self.state_changed.emit(self.state)
        
        greetings = [
            "부드럽게 쓰다듬어 주셔서 행복해요! 💕",
            "헤헤, 공직자님의 손길이 따뜻해요~ 🥰",
            "관심 가져주셔서 힘이 불끈 나요! 🌱✨",
            "오늘도 업무 힘내세요! 제가 응원할게요! 🌸"
        ]
        msg = random.choice(greetings)
        self.interaction_occurred.emit("pet", msg)
        return True, msg

    def on_chat_completed(self):
        """Reward on conversational interaction."""
        self.db.increment_stat("total_chat")
        self.state["affection"] = min(100, self.state["affection"] + 20)
        self.state["exp"] += 20
        self.state["total_interactions"] += 1
        self.check_evolution()
        self.check_achievements()
        self.save()
        self.state_changed.emit(self.state)

    def on_bug_cleared(self) -> Tuple[bool, str]:
        """User catches and shoos away an annoying caterpillar/bug from the plant."""
        self.db.increment_stat("total_bugs_cleared")
        self.state["affection"] = min(100, self.state["affection"] + 10)
        self.state["exp"] += 20
        self.state["total_interactions"] += 1
        self.check_evolution()
        self.check_achievements()
        self.save()
        self.state_changed.emit(self.state)
        msg = "✨ 나이스! 개구쟁이 벌레를 성공적으로 쫓아냈어요! (+20 EXP, 애정도 +10) 🌿"
        self.interaction_occurred.emit("bug_cleared", msg)
        return True, msg

    def on_eco_visitor_interacted(self, v_type: str) -> Tuple[bool, str]:
        """User interacts with an eco visitor or environmental creature."""
        self.db.increment_stat(f"total_{v_type}_visits")
        self.state["affection"] = min(100, self.state["affection"] + 8)
        self.state["exp"] += 15
        self.state["total_interactions"] += 1

        if v_type == "bee":
            msg = "🐝 꿀벌 친구와 반갑게 인사했어요! (+15 EXP, 애정도 +8) 🍯✨"
        elif v_type == "butterfly":
            msg = "🦋 나비와 눈을 맞추며 힐링 타임을 가졌어요! (+15 EXP, 애정도 +8) 🌸"
        elif v_type == "ladybug":
            msg = "🐞 칠성무당벌레가 행운을 전해주고 날아갔어요! (+15 EXP, 애정도 +8) 🍀"
        elif v_type == "bird":
            self.state["exp"] += 10
            self.state["affection"] = min(100, self.state["affection"] + 4)
            msg = "🐦 아기 파랑새가 지저귀며 행운의 깃털을 선물했어요! (+25 EXP, 애정도 +12) ✨"
        elif v_type == "cat_paw":
            self.state["exp"] += 5
            msg = "🐾 냥! 호기심 많은 길고양이와 젤리 하이파이브 성공! (+20 EXP, 애정도 +8) 🐱"
        elif v_type == "rain_cloud":
            self.state["water"] = min(100, self.state["water"] + 25)
            self.state["exp"] += 5
            msg = "🌈 시원한 단비 구름이 지나가며 무지개가 떠올랐어요! (수분 +25, +20 EXP) 🌧️"
        elif v_type == "firefly":
            msg = "✨ 반짝이는 반딧불이 무리가 화분을 은은하게 밝혔어요! (+15 EXP, 애정도 +8) 🌌"
        else:
            msg = f"🌿 자연의 친구 {v_type}와 교감했어요! (+15 EXP) ✨"

        self.check_evolution()
        self.check_achievements()
        self.save()
        self.state_changed.emit(self.state)
        self.interaction_occurred.emit(f"{v_type}_greeted", msg)
        return True, msg

    def check_evolution(self):
        """Check if evolution conditions are met (up to stage 6)."""
        current_stage = self.state.get("stage", 1)
        if current_stage >= 6:
            return

        req_exp, req_aff = STAGE_EXP_REQUIREMENTS.get(current_stage, (999999, 100))
        if self.state["exp"] >= req_exp and self.state["affection"] >= req_aff:
            new_stage = current_stage + 1
            self.state["stage"] = new_stage
            stage_name = STAGE_NAMES.get(new_stage, f"{new_stage}단계")
            
            if new_stage == 6:
                msg = f"축하합니다! 화분이 최종 마스터 단계인 [6단계 만개&결실] 상태로 찬란하게 피어났어요! 👑🌸 언제든 화원에 졸업 등록하고 새 씨앗을 키울 수 있어요!"
            else:
                msg = f"축하합니다! 화분이 [{stage_name}](으)로 성장·진화했어요! 🎉✨"
                
            self.evolved.emit(new_stage, msg)

    def draw_daily_fortune(self) -> Tuple[str, bool]:
        """
        Draw today's fortune cookie.
        Returns (message, is_first_time_today)
        """
        today_str = datetime.date.today().isoformat()
        existing = self.db.get_daily_fortune(today_str)
        if existing:
            return existing, False

        msg = random.choice(DAILY_FORTUNES)
        self.db.save_daily_fortune(today_str, msg)
        self.fortune_count += 1
        self.db.increment_stat("total_fortunes")

        # Reward on first daily draw
        self.state["exp"] += 25
        self.state["affection"] = min(100, self.state["affection"] + 15)
        self.check_evolution()
        self.check_achievements()
        self.save()
        self.state_changed.emit(self.state)
        return msg, True

    def graduate_current_plant(self, new_species: str = "sunflower", new_name: Optional[str] = None):
        """
        Graduate current Stage 6 plant to Garden and plant a new seed!
        """
        current_name = self.config.get("plant_name", "초록이")
        current_species = self.get_species()
        total_inter = self.state.get("total_interactions", 0)

        # 1. Save to garden collection
        self.db.graduate_plant(current_name, current_species, total_inter)
        self.db.increment_stat("total_graduated")

        # 2. Update config name if provided
        if new_name:
            self.config.set("plant_name", new_name)

        # 3. Reset plant state with new species
        now_str = datetime.datetime.now().isoformat()
        self.state = {
            "id": 1,
            "water": 80,
            "sunlight": 80,
            "affection": 20,
            "stage": 1,
            "exp": 0,
            "total_interactions": 0,
            "species": new_species,
            "created_at": now_str,
            "last_updated": now_str
        }
        self.save()
        self.check_achievements()
        self.state_changed.emit(self.state)

    def check_achievements(self):
        """Evaluate 100 achievement criteria across 10 categories."""
        stats = self.db.get_all_stats()
        w_cnt = max(self.water_count, stats.get("total_water", 0))
        s_cnt = max(self.sun_count, stats.get("total_sunlight", 0))
        p_cnt = max(self.pet_count, stats.get("total_pet", 0))
        c_cnt = stats.get("total_chat", 0)
        f_cnt = max(self.fortune_count, stats.get("total_fortunes", 0))
        
        # 1. First steps
        self._try_unlock("first_meet")
        if self.config.get("plant_name", "초록이") != "초록이":
            self._try_unlock("first_name")
        if c_cnt >= 1:
            self._try_unlock("first_chat")
        if w_cnt >= 1:
            self._try_unlock("first_water")
        if s_cnt >= 1:
            self._try_unlock("first_sun")
        if p_cnt >= 1:
            self._try_unlock("first_pet")
        if f_cnt >= 1:
            self._try_unlock("first_fortune")
        
        mood_history = self.db.get_recent_mood_history(limit=50)
        if mood_history:
            self._try_unlock("first_mood")
        if self.state.get("total_interactions", 0) >= 1:
            self._try_unlock("first_routine")
        self._try_unlock("first_settings")

        # 2. Watering
        w_targets = [(1,"water_1"), (5,"water_5"), (10,"water_10"), (25,"water_25"), (50,"water_50"),
                     (75,"water_75"), (100,"water_100"), (150,"water_150"), (200,"water_200"), (300,"water_300")]
        for req, ach_id in w_targets:
            if w_cnt >= req:
                self._try_unlock(ach_id)

        # 3. Sunlight
        s_targets = [(1,"sun_1"), (5,"sun_5"), (10,"sun_10"), (25,"sun_25"), (50,"sun_50"),
                     (75,"sun_75"), (100,"sun_100"), (150,"sun_150"), (200,"sun_200"), (300,"sun_300")]
        for req, ach_id in s_targets:
            if s_cnt >= req:
                self._try_unlock(ach_id)

        # 4. Petting & Affection
        p_targets = [(1,"pet_1"), (10,"pet_10"), (25,"pet_25"), (50,"pet_50"), (100,"pet_100"),
                     (200,"pet_200"), (300,"pet_300"), (500,"pet_500")]
        for req, ach_id in p_targets:
            if p_cnt >= req:
                self._try_unlock(ach_id)
        aff = self.state.get("affection", 0)
        if aff >= 50:
            self._try_unlock("aff_50")
        if aff >= 100:
            self._try_unlock("aff_100")

        # 5. Dialogue
        c_targets = [(1,"chat_1"), (5,"chat_5"), (10,"chat_10"), (25,"chat_25"), (50,"chat_50"),
                     (100,"chat_100"), (150,"chat_150"), (200,"chat_200"), (300,"chat_300"), (500,"chat_500")]
        for req, ach_id in c_targets:
            if c_cnt >= req:
                self._try_unlock(ach_id)

        # 6. Mood care
        for rec in mood_history:
            mt = rec.get("mood_type")
            if mt == "happy":
                self._try_unlock("mood_happy")
            elif mt == "passionate":
                self._try_unlock("mood_passion")
            elif mt == "calm":
                self._try_unlock("mood_calm")
            elif mt == "tired":
                self._try_unlock("mood_tired_care")
            elif mt == "stressed":
                self._try_unlock("mood_stress_care")
        
        m_cnt = len(mood_history)
        if m_cnt >= 5:
            self._try_unlock("mood_log_5")
        if m_cnt >= 10:
            self._try_unlock("mood_log_10")
        if m_cnt >= 25:
            self._try_unlock("mood_log_25")
        if m_cnt >= 50:
            self._try_unlock("mood_log_50")
        if mood_history:
            avg_score = sum(r.get("score", 3) for r in mood_history) / len(mood_history)
            if avg_score >= 4.0:
                self._try_unlock("mood_high_avg")

        # 7. Fortune
        f_targets = [(1,"fortune_1"), (3,"fortune_3"), (5,"fortune_5"), (7,"fortune_7"), (14,"fortune_14"),
                     (21,"fortune_21"), (30,"fortune_30"), (50,"fortune_50"), (75,"fortune_75"), (100,"fortune_100")]
        for req, ach_id in f_targets:
            if f_cnt >= req:
                self._try_unlock(ach_id)

        # 8. Growth
        stg = self.state.get("stage", 1)
        if stg >= 2:
            self._try_unlock("stage_2")
        if stg >= 3:
            self._try_unlock("stage_3")
        if stg >= 4:
            self._try_unlock("stage_4")
        if stg >= 5:
            self._try_unlock("stage_5")
        if stg >= 6:
            self._try_unlock("stage_6")
        
        exp = self.state.get("exp", 0)
        exp_targets = [(300,"exp_300"), (600,"exp_600"), (1000,"exp_1000"), (2000,"exp_2000"), (5000,"exp_5000")]
        for req, ach_id in exp_targets:
            if exp >= req:
                self._try_unlock(ach_id)

        # 9. Garden & Species
        graduated = self.db.get_graduated_plants()
        g_cnt = len(graduated)
        g_targets = [(1,"grad_1"), (2,"grad_2"), (3,"grad_3"), (5,"grad_5"), (10,"grad_10")]
        for req, ach_id in g_targets:
            if g_cnt >= req:
                self._try_unlock(ach_id)
        
        all_species = set(p["species"] for p in graduated)
        if stg >= 6:
            all_species.add(self.get_species())
        for sp in all_species:
            if sp in ["classic", "sunflower", "cactus", "clover", "cherry"]:
                self._try_unlock(f"spec_{sp}")

        # 10. Office Life & Routines
        hour = datetime.datetime.now().hour
        if 7 <= hour <= 9:
            self._try_unlock("routine_morning")
        elif 10 <= hour <= 11:
            self._try_unlock("routine_focus")
        elif 12 <= hour <= 13:
            self._try_unlock("routine_lunch")
        elif 14 <= hour <= 16:
            self._try_unlock("routine_stretch")
        elif 17 <= hour <= 19:
            self._try_unlock("routine_ontime_leave")
        elif 19 < hour <= 23:
            self._try_unlock("routine_overtime")
        elif hour >= 23 or hour < 6:
            self._try_unlock("routine_midnight")
        
        if self.state.get("total_interactions", 0) >= 20:
            self._try_unlock("routine_desk_guardian")
        if self.state.get("total_interactions", 0) >= 50:
            self._try_unlock("routine_idle_rest")
        if self.state.get("total_interactions", 0) >= 100:
            self._try_unlock("routine_master")

        # 11. Eco Events & Environmental Visitors
        bugs_cleared = self.db.get_stat("total_bugs_cleared") or 0
        if bugs_cleared >= 1:
            self._try_unlock("bug_clear_1")
        if bugs_cleared >= 5:
            self._try_unlock("bug_clear_5")

        bee_visits = self.db.get_stat("total_bee_visits") or 0
        if bee_visits >= 1:
            self._try_unlock("bee_water")

        ladybug_visits = self.db.get_stat("total_ladybug_visits") or 0
        if ladybug_visits >= 1:
            self._try_unlock("ladybug_visit")

        bird_visits = self.db.get_stat("total_bird_visits") or 0
        if bird_visits >= 1:
            self._try_unlock("bluebird_feather")

        cat_visits = self.db.get_stat("total_cat_paw_visits") or (self.db.get_stat("total_cat_visits") or 0)
        if cat_visits >= 1:
            self._try_unlock("cat_highfive")

        rain_visits = self.db.get_stat("total_rain_cloud_visits") or (self.db.get_stat("total_rain_visits") or 0)
        if rain_visits >= 1:
            self._try_unlock("rain_rainbow")

        firefly_visits = self.db.get_stat("total_firefly_visits") or 0
        if firefly_visits >= 1:
            self._try_unlock("firefly_night")

        total_eco = bugs_cleared + bee_visits + ladybug_visits + bird_visits + cat_visits + rain_visits + firefly_visits
        if total_eco >= 1:
            self._try_unlock("eco_first_meet")
        if total_eco >= 10:
            self._try_unlock("eco_master")

    def _try_unlock(self, ach_id: str):
        if self.db.unlock_achievement(ach_id):
            ach_info = next((a for a in ACHIEVEMENTS_DEF if a["id"] == ach_id), None)
            if ach_info:
                self.achievement_unlocked.emit(ach_info)

    def reset_state(self):
        """Reset plant to initial sprout."""
        now_str = datetime.datetime.now().isoformat()
        self.state = {
            "id": 1,
            "water": 80,
            "sunlight": 80,
            "affection": 20,
            "stage": 1,
            "exp": 0,
            "total_interactions": 0,
            "species": self.get_species(),
            "created_at": now_str,
            "last_updated": now_str
        }
        self.save()
        self.state_changed.emit(self.state)

    def get_time_of_day_greeting(self) -> str:
        """Returns context-aware greeting according to current office hours and daily routine."""
        now = datetime.datetime.now()
        hour = now.hour
        user_name = self.config.get("user_nickname", "공직자님")

        if 7 <= hour < 10:
            return f"좋은 아침이에요, {user_name}! ☀️ 모닝커피 한 잔과 함께 상쾌한 하루 시작해요! ☕"
        elif 10 <= hour < 12:
            return f"오전 집중 업무 시간! 힘내세요 {user_name}, 곁에서 응원하고 있어요 🎯"
        elif 12 <= hour < 14:
            return f"맛있는 점심 드셨나요? 든든하게 드시고 식곤증 이겨내요 🍱"
        elif 14 <= hour < 17:
            return f"피로가 몰려올 시간이에요! 3분 스트레칭과 시원한 물 한잔 어떠세요? 💧"
        elif 17 <= hour < 19:
            return f"오늘 하루도 정말 고생 많으셨어요, {user_name}! 정시 퇴근하고 푹 쉬세요 🏃‍♂️✨"
        elif 19 <= hour < 23:
            return f"야근 중이신가요? 🌙 무리하지 마시고 건강 먼저 챙기세요!"
        else:
            return f"깊은 밤이에요 🌌 꿈나라에서 푹 쉬시고 내일 또 만나요 💤"

    def get_hourly_time_announcement(self) -> str:
        """Returns hourly exact time announcement with friendly cheer."""
        now = datetime.datetime.now()
        hour_12 = now.hour % 12
        if hour_12 == 0:
            hour_12 = 12
        ampm = "오후" if now.hour >= 12 else "오전"
        time_str = f"{ampm} {hour_12}시 정각"
        
        routine = self.get_time_of_day_greeting()
        return f"⏰ <b>현재 시각 {time_str}이에요!</b><br>{routine}"

    def save(self):
        """Save current state to database."""
        self.db.save_plant_state(self.state)
