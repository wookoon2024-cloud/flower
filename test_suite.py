"""
Test Suite for AI Companion Plant Widget
Tests Database, Config, Plant Engine, and Fallback logic.
"""
import os
import sys
import unittest
import datetime

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from ai_plant.config import ConfigManager
from ai_plant.database import DatabaseManager
from ai_plant.plant_engine import PlantEngine, STAGE_NAMES
from ai_plant.ai_client import select_fallback_response

class TestAIPlantWidget(unittest.TestCase):
    def setUp(self):
        self.test_db = "test_plant.db"
        self.test_cfg = "test_config.json"
        
        # Clean up any leftover test files
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        if os.path.exists(self.test_cfg):
            os.remove(self.test_cfg)

        self.db = DatabaseManager(self.test_db)
        self.config = ConfigManager(self.test_cfg)

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        if os.path.exists(self.test_cfg):
            os.remove(self.test_cfg)

    def test_config_manager(self):
        self.assertEqual(self.config.get("plant_name"), "초록이")
        self.config.set("plant_name", "새싹이")
        self.assertEqual(self.config.get("plant_name"), "새싹이")
        
        # Reload and check persistence
        reloaded_cfg = ConfigManager(self.test_cfg)
        self.assertEqual(reloaded_cfg.get("plant_name"), "새싹이")

    def test_database_and_sliding_window(self):
        state = self.db.load_plant_state()
        self.assertEqual(state["water"], 80)
        self.assertEqual(state["stage"], 1)

        # Update state
        state["water"] = 95
        state["stage"] = 2
        self.db.save_plant_state(state)
        
        loaded = self.db.load_plant_state()
        self.assertEqual(loaded["water"], 95)
        self.assertEqual(loaded["stage"], 2)

        # Add 10 chat messages
        for i in range(10):
            role = "user" if i % 2 == 0 else "assistant"
            self.db.add_chat_message(role, f"Message {i}")

        # Sliding window test (limit 6)
        recent = self.db.get_recent_chat_history(limit=6)
        self.assertEqual(len(recent), 6)
        self.assertEqual(recent[0]["content"], "Message 4")
        self.assertEqual(recent[-1]["content"], "Message 9")

    def test_plant_engine_interactions(self):
        engine = PlantEngine(self.db, self.config)
        
        # Reset state to clean baseline
        engine.reset_state()
        init_state = engine.get_state()
        self.assertEqual(init_state["water"], 80)

        # Water interaction
        success, msg = engine.give_water()
        self.assertTrue(success)
        self.assertEqual(engine.get_state()["water"], 100)
        self.assertGreater(engine.get_state()["exp"], 0)

        # Pet interaction
        init_aff = engine.get_state()["affection"]
        success, msg = engine.pet()
        self.assertTrue(success)
        self.assertEqual(engine.get_state()["affection"], init_aff + 15)

    def test_plant_engine_evolution(self):
        engine = PlantEngine(self.db, self.config)
        engine.reset_state()

        # Simulate reaching Stage 2 requirements (exp >= 100, aff >= 30)
        for _ in range(10):
            engine.give_sunlight()
            engine.pet()
            
        st = engine.get_state()
        self.assertGreaterEqual(st["stage"], 2)

    def test_offline_decay_calculation(self):
        engine = PlantEngine(self.db, self.config)
        engine.reset_state()

        # Set last_updated to 2 hours ago
        past_time = datetime.datetime.now() - datetime.timedelta(hours=2)
        engine.state["last_updated"] = past_time.isoformat()
        engine.state["water"] = 90
        engine.state["sunlight"] = 90
        engine.save()

        # Reinitialize engine to trigger offline decay
        engine2 = PlantEngine(self.db, self.config)
        st = engine2.get_state()
        self.assertLess(st["water"], 90)
        self.assertLess(st["sunlight"], 90)
        print(f"After 2h offline decay: Water={st['water']}, Sun={st['sunlight']}")

    def test_fallback_response_generation(self):
        state = {"water": 80, "sunlight": 80, "affection": 50, "stage": 1}
        
        resp_greeting = select_fallback_response("안녕하세요 초록아!", "김주무관", "초록이", state)
        self.assertIn("김주무관", resp_greeting)

        resp_tired = select_fallback_response("오늘 일이 너무 많아서 피곤해요", "김주무관", "초록이", state)
        self.assertIn("김주무관", resp_tired)

        resp_cheer = select_fallback_response("초록아 응원해줘!", "김주무관", "초록이", state)
        self.assertIn("김주무관", resp_cheer)

    def test_garden_graduation_and_achievements(self):
        engine = PlantEngine(self.db, self.config)
        engine.reset_state()

        # Test daily fortune
        msg, is_first = engine.draw_daily_fortune()
        self.assertTrue(is_first)
        self.assertTrue(len(msg) > 5)

        # Re-drawing on same day
        msg2, is_first2 = engine.draw_daily_fortune()
        self.assertFalse(is_first2)
        self.assertEqual(msg, msg2)

        # Simulate graduation
        engine.state["stage"] = 6
        engine.state["exp"] = 1000
        engine.graduate_current_plant(new_species="sunflower", new_name="해바라기1호")

        # Check garden records
        graduated = self.db.get_graduated_plants()
        self.assertEqual(len(graduated), 1)
        self.assertEqual(graduated[0]["name"], "초록이")

        # Check new plant state
        new_st = engine.get_state()
        self.assertEqual(new_st["stage"], 1)
        self.assertEqual(new_st["species"], "sunflower")

        # Check achievements
        unlocked = self.db.get_unlocked_achievements()
        self.assertIn("grad_1", unlocked)

    def test_mood_analysis_and_time_routines(self):
        from ai_plant.ai_client import analyze_user_sentiment
        
        # Test sentiment analyzer
        m1, s1 = analyze_user_sentiment("오늘 너무 행복하고 기뻐요!")
        self.assertEqual(m1, "happy")
        self.assertEqual(s1, 5)

        m2, s2 = analyze_user_sentiment("오늘 너무 피곤하고 지쳐요...")
        self.assertEqual(m2, "tired")
        self.assertEqual(s2, 2)

        m3, s3 = analyze_user_sentiment("업무 때문에 스트레스 받고 답답해요")
        self.assertEqual(m3, "stressed")
        self.assertEqual(s3, 1)

        # Test mood persistence
        self.db.add_mood_entry("happy", 5, "오늘 기분 최고!")
        self.db.add_mood_entry("calm", 3, "평온한 하루")
        recent_moods = self.db.get_recent_mood_history(limit=5)
        self.assertEqual(len(recent_moods), 2)
        self.assertEqual(recent_moods[-1]["score"], 3)

    def test_100_achievements_structure(self):
        from ai_plant.achievements_data import ACHIEVEMENTS_100, ACHIEVEMENT_CATEGORIES
        self.assertEqual(len(ACHIEVEMENTS_100), 112)
        self.assertEqual(len(ACHIEVEMENT_CATEGORIES), 12)  # all + 11 categories
        
        # Verify all achievements have unique IDs and required fields
        seen_ids = set()
        for ach in ACHIEVEMENTS_100:
            self.assertIn("id", ach)
            self.assertIn("cat", ach)
            self.assertIn("title", ach)
            self.assertIn("icon", ach)
            self.assertIn("desc", ach)
            self.assertNotIn(ach["id"], seen_ids, f"Duplicate achievement ID: {ach['id']}")
            seen_ids.add(ach["id"])

        # Test engine evaluation
        engine = PlantEngine(self.db, self.config)
        engine.give_water()
        engine.give_sunlight()
        engine.pet()
        engine.draw_daily_fortune()
        
        unlocked = self.db.get_unlocked_achievements()
        self.assertGreaterEqual(len(unlocked), 4)

    def test_clova_studio_gov_and_proactive_speech(self):
        from ai_plant.ai_client import (
            AIChatWorker, select_fallback_response, format_clean_user_name,
            parse_action_tags, SPECIES_PERSONAS
        )

        # 1. Test Clean User Name formatting
        self.assertEqual(format_clean_user_name("홍길동"), "홍길동님")
        self.assertEqual(format_clean_user_name("공직자님"), "공직자님")

        # 2. Test Proactive fallback responses
        resp_thirsty = select_fallback_response("thirsty", "김주무관", "초록이", {"water": 10})
        self.assertTrue(any(w in resp_thirsty for w in ["물", "수분", "목", "촉촉"]))

        resp_lunch = select_fallback_response("lunch", "김주무관", "초록이", {})
        self.assertTrue(any(w in resp_lunch for w in ["점심", "식사", "맛점"]))

        resp_leave = select_fallback_response("leave_work", "김주무관", "초록이", {})
        self.assertTrue(any(w in resp_leave for w in ["퇴근", "칼퇴", "고생", "완주", "쉬세요"]))

        # 3. Test Action Tag parsing
        cleaned, actions = parse_action_tags("물을 주셔서 감사해요! [ACTION:WATER]")
        self.assertEqual(cleaned, "물을 주셔서 감사해요!")
        self.assertIn("water", actions)

        # 4. Test AIChatWorker creation with CLOVA Studio GOV configuration
        worker = AIChatWorker(
            config={
                "api_endpoint": "https://api.clovastudio.go.kr/api/v1/chat/completions",
                "api_key": "",
                "model": "HCX-GOV-THINK-V1-32B",
                "stream_enabled": True
            },
            plant_state={"species": "classic", "stage": 3, "water": 70, "sunlight": 70, "affection": 40},
            chat_history=[{"role": "user", "content": "안녕"}, {"role": "assistant", "content": "반가워요"}],
            user_message="",
            proactive_mode="idle_nudge"
        )
        self.assertEqual(worker.proactive_mode, "idle_nudge")
        self.assertEqual(worker.config["model"], "HCX-GOV-THINK-V1-32B")

    def test_garden_dialog_initialization(self):
        from PySide6.QtWidgets import QApplication
        from ai_plant.ui.garden_dialog import GardenDialog
        # Ensure QApplication exists for UI tests
        app = QApplication.instance() or QApplication([])
        engine = PlantEngine(self.db, self.config)
        self.db.add_mood_entry("happy", 5, "오늘 기분 좋아")
        self.db.add_mood_entry("calm", 3, "평온한 하루")
        
        # Test daily mood summary calculation
        daily_summary = self.db.get_daily_mood_summary(num_days=7)
        self.assertEqual(len(daily_summary), 7)
        today_data = next((d for d in daily_summary if d["is_today"]), None)
        self.assertIsNotNone(today_data)
        self.assertTrue(today_data["has_data"])
        self.assertEqual(today_data["avg_score"], 4.0) # (5+3)/2 = 4.0
        self.assertEqual(today_data["count"], 2)

        # Test future slots pre-population
        future_slots = [d for d in daily_summary if d["is_future"]]
        self.assertEqual(len(future_slots), 6)
        self.assertFalse(future_slots[0]["has_data"])

    def test_eco_visitor_interactions(self):
        engine = PlantEngine(self.db, self.config)
        init_exp = engine.get_state()["exp"]
        init_aff = engine.get_state()["affection"]

        # 1. Test bug cleared & achievement
        ok, msg = engine.on_bug_cleared()
        self.assertTrue(ok)
        self.assertIn("벌레", msg)
        self.assertEqual(engine.get_state()["exp"], init_exp + 25)
        self.assertEqual(engine.get_state()["affection"], init_aff + 10)

        # 2. Test bee, ladybug, bird, cat_paw, rain_cloud, firefly
        for v in ["bee", "ladybug", "bird", "cat_paw", "rain_cloud", "firefly"]:
            ok, msg = engine.on_eco_visitor_interacted(v)
            self.assertTrue(ok)

        # 3. Check eco achievements unlocked
        unlocked = self.db.get_unlocked_achievements()
        self.assertIn("bug_clear_1", unlocked)
        self.assertIn("bee_water", unlocked)
        self.assertIn("ladybug_visit", unlocked)
        self.assertIn("bluebird_feather", unlocked)
        self.assertIn("cat_highfive", unlocked)
        self.assertIn("rain_rainbow", unlocked)
        self.assertIn("firefly_night", unlocked)
        self.assertIn("eco_first_meet", unlocked)

        # 4. Check total achievements count is 112
        from ai_plant.achievements_data import ACHIEVEMENTS_100
        self.assertEqual(len(ACHIEVEMENTS_100), 112)

    def test_species_unlock_and_starlight_rose(self):
        engine = PlantEngine(self.db, self.config)

        # 1. Basic 5 species are always unlocked
        for sp in ["classic", "sunflower", "cactus", "clover", "cherry"]:
            self.assertTrue(engine.is_species_unlocked(sp))

        # 2. Secret species 'starlight_rose' is locked initially
        self.assertFalse(engine.is_species_unlocked("starlight_rose"))
        comp, req = engine.get_species_unlock_progress("starlight_rose")
        self.assertEqual(comp, 0)
        self.assertEqual(req, 5)

        # 3. Graduate 4 species -> still locked
        base_4 = ["classic", "sunflower", "cactus", "clover"]
        for sp in base_4:
            self.db.graduate_plant(f"Plant_{sp}", sp, 1200)

        self.assertFalse(engine.is_species_unlocked("starlight_rose"))
        comp, req = engine.get_species_unlock_progress("starlight_rose")
        self.assertEqual(comp, 4)

        # 4. Graduate the 5th species ('cherry') -> Unlocked!
        self.db.graduate_plant("Plant_cherry", "cherry", 1500)
        self.assertTrue(engine.is_species_unlocked("starlight_rose"))
        comp, req = engine.get_species_unlock_progress("starlight_rose")
        self.assertEqual(comp, 5)

        # 5. Check achievements trigger
        engine.check_achievements()
        unlocked = self.db.get_unlocked_achievements()
        self.assertIn("master_botanist", unlocked)

    def test_offline_multi_turn_counseling(self):
        from ai_plant.ai_client import counsel_reply, COUNSEL_MARK, COUNSEL_FLOW
        hist = []

        def say(text):
            reply = counsel_reply(text, hist[-6:], "홍길동 주무관님")
            hist.append({"role": "user", "content": text})
            if reply:
                hist.append({"role": "assistant", "content": reply})
            return reply

        # 0턴: 일반 고민 → 무슨 일이 있었는지 되묻기
        r0 = say("벚꽃이아, 오늘 회사에서 스트레스 받는 일이 있었는데 내 이야기 좀 들어줘...")
        self.assertTrue(r0.endswith(COUNSEL_MARK))
        self.assertIn("어떤 일이 있었어요?", r0)
        # 1턴: 민원 이야기 → 민원 주제로 이어서 마음을 묻기
        r1 = say("오늘 민원인이 전화로 계속 소리를 질러서 너무 힘들었어")
        self.assertIn("마음은 어땠어요?", r1)
        self.assertIn("응대", r1)
        # 2턴: 감정 표현 → 민원 주제 유지, 숨 고르기·특이민원 절차 안내
        r2 = say("억울하고 손이 떨렸어. 내가 뭘 잘못했나 싶고")
        self.assertIn("특이민원", r2)
        # 3턴: 마무리 + 기관 상담 안내
        r3 = say("응 숨 쉬니까 좀 나아졌어")
        self.assertIn("EAP", r3)
        # 4턴 이후에는 상담 흐름이 끝나고 일반 응답으로 돌아감
        self.assertIsNone(counsel_reply("오늘 점심 뭐 먹지", hist[-6:], "홍길동 주무관님"))
        # 마무리 직후 새 상담을 시작하면 0턴부터 다시 이어짐 (앞 상담 턴을 세지 않음)
        r5 = say("과장님 때문에 너무 속상해")
        self.assertEqual(r5, COUNSEL_FLOW["boss"][0].format(user="홍길동 주무관님") + COUNSEL_MARK)
        r6 = say("회의 때 다른 직원들 앞에서 제 보고서를 크게 지적하셨어")
        self.assertIn("듣고 싶었던 말", r6)
        # 화분 돌보기 말은 상담 중이어도 상담 흐름에서 빠짐
        self.assertIsNone(counsel_reply("벚꽃이 목마르지? 물 줄게", hist[-2:], "홍길동 주무관님"))
        # 상담과 무관한 말은 상담 흐름을 시작하지 않음
        self.assertIsNone(counsel_reply("안녕 반가워", [], "홍길동 주무관님"))
        # 모든 주제 흐름은 4턴이고, 마지막 턴 전까지는 되묻는 질문이 들어 있음
        for topic, flow in COUNSEL_FLOW.items():
            self.assertEqual(len(flow), 4, topic)
            for line in flow[:3]:
                self.assertIn("?", line, (topic, line))

if __name__ == "__main__":
    unittest.main()



