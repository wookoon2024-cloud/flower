"""
Achievements Definition Data (100 Achievements across 10 Categories)
Provides structured metadata, categories, icons, and descriptions for long-term companion plant progression.
"""

ACHIEVEMENT_CATEGORIES = {
    "all": "전체 도감 (110개)",
    "first_steps": "🌱 첫걸음 & 시작 (10)",
    "watering": "💧 촉촉한 물주기 (10)",
    "sunlight": "☀️ 따스한 햇빛 (10)",
    "petting": "💕 다정한 손길 (10)",
    "dialogue": "💬 AI 대화 & 고민상담 (10)",
    "mood_care": "📈 마음 날씨 케어 (10)",
    "fortune": "🥠 오늘의 포춘 쿠키 (10)",
    "growth": "🌸 6단계 성장·진화 (10)",
    "garden": "🪴 5종 품종 & 화원 (10)",
    "office_life": "⏰ 공직자 일과 & 힐링 (10)",
    "eco_events": "🐝 생태계 탐험 & 이벤트 (10)"
}

ACHIEVEMENTS_100 = [
    # 1. 🌱 첫걸음 & 시작 (10개)
    {"id": "first_meet", "cat": "first_steps", "title": "설레는 첫 만남", "icon": "🌱", "desc": "데스크톱 AI 반려화분과 첫 인사를 나누었습니다."},
    {"id": "first_name", "cat": "first_steps", "title": "나만의 반려화분", "icon": "🏷️", "desc": "화분에게 소중하고 특별한 이름을 선물했습니다."},
    {"id": "first_chat", "cat": "first_steps", "title": "첫 대화의 시작", "icon": "💬", "desc": "AI 화분과 첫 대화를 나눴습니다."},
    {"id": "first_water", "cat": "first_steps", "title": "시원한 첫 모금", "icon": "💧", "desc": "화분에게 처음으로 시원한 물을 주었습니다."},
    {"id": "first_sun", "cat": "first_steps", "title": "첫 햇살 한 줌", "icon": "☀️", "desc": "화분에게 첫 햇빛을 쬐어주었습니다."},
    {"id": "first_pet", "cat": "first_steps", "title": "다정한 첫 터치", "icon": "💕", "desc": "화분을 부드럽게 처음 쓰다듬어주었습니다."},
    {"id": "first_fortune", "cat": "first_steps", "title": "첫 번째 행운", "icon": "🥠", "desc": "오늘의 첫 포춘 쿠키를 열어보았습니다."},
    {"id": "first_mood", "cat": "first_steps", "title": "내 마음 들여다보기", "icon": "📈", "desc": "첫 대화를 통해 마음 날씨가 기록되었습니다."},
    {"id": "first_routine", "cat": "first_steps", "title": "정시의 동반자", "icon": "⏰", "desc": "정시 알림을 통해 시간대별 인사를 들었습니다."},
    {"id": "first_settings", "cat": "first_steps", "title": "맞춤형 환경 설정", "icon": "⚙️", "desc": "환경설정에서 나만의 설정을 저장했습니다."},

    # 2. 💧 촉촉한 물주기 (10개)
    {"id": "water_1", "cat": "watering", "title": "촉촉한 시작", "icon": "💧", "desc": "화분에 물을 1회 주었습니다."},
    {"id": "water_5", "cat": "watering", "title": "목마름 해소", "icon": "💧", "desc": "화분에 물을 5회 주었습니다."},
    {"id": "water_10", "cat": "watering", "title": "정성스런 물뿌리개", "icon": "💧", "desc": "화분에 물을 10회 주었습니다."},
    {"id": "water_25", "cat": "watering", "title": "촉촉한 반려 친구", "icon": "💧", "desc": "화분에 물을 25회 주었습니다."},
    {"id": "water_50", "cat": "watering", "title": "초록빛 수분 공급자", "icon": "🌊", "desc": "누적 물주기 50회를 달성했습니다."},
    {"id": "water_75", "cat": "watering", "title": "생명의 단비", "icon": "🌊", "desc": "누적 물주기 75회를 달성했습니다."},
    {"id": "water_100", "cat": "watering", "title": "백 번의 촉촉함", "icon": "🌊", "desc": "누적 물주기 100회를 달성했습니다."},
    {"id": "water_150", "cat": "watering", "title": "마르지 않는 샘물", "icon": "⛲", "desc": "누적 물주기 150회를 달성했습니다."},
    {"id": "water_200", "cat": "watering", "title": "청정 오아시스", "icon": "⛲", "desc": "누적 물주기 200회를 달성했습니다."},
    {"id": "water_300", "cat": "watering", "title": "워터 가디언 마스터", "icon": "👑", "desc": "누적 물주기 300회를 달성했습니다."},

    # 3. ☀️ 따스한 햇빛 (10개)
    {"id": "sun_1", "cat": "sunlight", "title": "따스한 햇살", "icon": "☀️", "desc": "햇빛을 1회 쬐어주었습니다."},
    {"id": "sun_5", "cat": "sunlight", "title": "활력 충전", "icon": "☀️", "desc": "햇빛을 5회 쬐어주었습니다."},
    {"id": "sun_10", "cat": "sunlight", "title": "광합성 장인", "icon": "☀️", "desc": "햇빛을 10회 쬐어주었습니다."},
    {"id": "sun_25", "cat": "sunlight", "title": "햇살 가득한 책상", "icon": "☀️", "desc": "햇빛을 25회 쬐어주었습니다."},
    {"id": "sun_50", "cat": "sunlight", "title": "태양의 친구", "icon": "🌞", "desc": "누적 햇빛 50회를 달성했습니다."},
    {"id": "sun_75", "cat": "sunlight", "title": "눈부신 초록빛", "icon": "🌞", "desc": "누적 햇빛 75회를 달성했습니다."},
    {"id": "sun_100", "cat": "sunlight", "title": "백 번의 햇살", "icon": "🌞", "desc": "누적 햇빛 100회를 달성했습니다."},
    {"id": "sun_150", "cat": "sunlight", "title": "따스한 온실 가드너", "icon": "🌻", "desc": "누적 햇빛 150회를 달성했습니다."},
    {"id": "sun_200", "cat": "sunlight", "title": "태양의 수호자", "icon": "🌻", "desc": "누적 햇빛 200회를 달성했습니다."},
    {"id": "sun_300", "cat": "sunlight", "title": "솔라 마스터 가드너", "icon": "👑", "desc": "누적 햇빛 300회를 달성했습니다."},

    # 4. 💕 다정한 손길 (10개)
    {"id": "pet_1", "cat": "petting", "title": "조심스런 손길", "icon": "💕", "desc": "화분을 1회 쓰다듬어주었습니다."},
    {"id": "pet_10", "cat": "petting", "title": "따뜻한 손길", "icon": "💕", "desc": "화분을 10회 쓰다듬어주었습니다."},
    {"id": "pet_25", "cat": "petting", "title": "다정한 가드너", "icon": "💕", "desc": "화분을 25회 쓰다듬어주었습니다."},
    {"id": "pet_50", "cat": "petting", "title": "헤헤, 행복해요!", "icon": "💖", "desc": "화분을 50회 쓰다듬어주었습니다."},
    {"id": "pet_100", "cat": "petting", "title": "백 번의 쓰다듬기", "icon": "💖", "desc": "화분을 100회 쓰다듬어주었습니다."},
    {"id": "pet_200", "cat": "petting", "title": "언제나 함께하는 온기", "icon": "💖", "desc": "화분을 200회 쓰다듬어주었습니다."},
    {"id": "pet_300", "cat": "petting", "title": "최고의 짝꿍", "icon": "💗", "desc": "화분을 300회 쓰다듬어주었습니다."},
    {"id": "pet_500", "cat": "petting", "title": "영혼의 단짝 가드너", "icon": "👑", "desc": "화분을 500회 쓰다듬어주었습니다."},
    {"id": "aff_50", "cat": "petting", "title": "깊어지는 유대감", "icon": "🥰", "desc": "화분의 애정도 50을 달성했습니다."},
    {"id": "aff_100", "cat": "petting", "title": "애정 만점 가드너", "icon": "💯", "desc": "화분의 애정도 100(만점)을 달성했습니다."},

    # 5. 💬 AI 대화 & 우정 (10개)
    {"id": "chat_1", "cat": "dialogue", "title": "반가워 초록아", "icon": "💬", "desc": "AI 화분과 첫 대화를 나눴습니다."},
    {"id": "chat_5", "cat": "dialogue", "title": "어느덧 친해진 사이", "icon": "💬", "desc": "AI 화분과 5회 대화를 나눴습니다."},
    {"id": "chat_10", "cat": "dialogue", "title": "마음이 통하는 친구", "icon": "💬", "desc": "AI 화분과 10회 대화를 나눴습니다."},
    {"id": "chat_25", "cat": "dialogue", "title": "속마음 터놓기", "icon": "🗣️", "desc": "AI 화분과 25회 대화를 나눴습니다."},
    {"id": "chat_50", "cat": "dialogue", "title": "데스크의 비밀 친구", "icon": "🗣️", "desc": "AI 화분과 50회 대화를 나눴습니다."},
    {"id": "chat_100", "cat": "dialogue", "title": "백 번의 정다운 교감", "icon": "🗣️", "desc": "AI 화분과 100회 대화를 나눴습니다."},
    {"id": "chat_150", "cat": "dialogue", "title": "공감의 달인", "icon": "🤝", "desc": "AI 화분과 150회 대화를 나눴습니다."},
    {"id": "chat_200", "cat": "dialogue", "title": "마음의 안식처", "icon": "🤝", "desc": "AI 화분과 200회 대화를 나눴습니다."},
    {"id": "chat_300", "cat": "dialogue", "title": "평생의 힐링 메이트", "icon": "✨", "desc": "AI 화분과 300회 대화를 나눴습니다."},
    {"id": "chat_500", "cat": "dialogue", "title": "대화의 대가 (500회)", "icon": "👑", "desc": "AI 화분과 500회 대화를 달성했습니다."},

    # 6. 📈 마음 날씨 케어 (10개)
    {"id": "mood_happy", "cat": "mood_care", "title": "기쁨의 순간 😊", "icon": "😊", "desc": "기쁨과 행복이 가득한 마음 날씨가 기록되었습니다."},
    {"id": "mood_passion", "cat": "mood_care", "title": "열정 가득한 하루 🔥", "icon": "🔥", "desc": "의욕과 열정 넘치는 마음 날씨가 기록되었습니다."},
    {"id": "mood_calm", "cat": "mood_care", "title": "평온한 일상 🌿", "icon": "🌿", "desc": "차분하고 편안한 마음 날씨가 기록되었습니다."},
    {"id": "mood_tired_care", "cat": "mood_care", "title": "피로 회복 케어 😴", "icon": "😴", "desc": "피로한 날 화분과 대화하며 위로를 받았습니다."},
    {"id": "mood_stress_care", "cat": "mood_care", "title": "스트레스 훌훌 🌧️", "icon": "🌧️", "desc": "힘든 날 화분과 대화하며 마음을 털어냈습니다."},
    {"id": "mood_log_5", "cat": "mood_care", "title": "마음 일기 5장", "icon": "📝", "desc": "마음 날씨를 5회 기록했습니다."},
    {"id": "mood_log_10", "cat": "mood_care", "title": "감정 추이 관찰자", "icon": "📊", "desc": "마음 날씨를 10회 기록했습니다."},
    {"id": "mood_log_25", "cat": "mood_care", "title": "마음 날씨 연구가", "icon": "📊", "desc": "마음 날씨를 25회 기록했습니다."},
    {"id": "mood_log_50", "cat": "mood_care", "title": "마음 힐링 마스터", "icon": "🏆", "desc": "마음 날씨를 50회 기록했습니다."},
    {"id": "mood_high_avg", "cat": "mood_care", "title": "맑음 가득한 마음", "icon": "🌈", "desc": "최근 마음 날씨 평균 4.0점 이상을 달성했습니다."},

    # 7. 🥠 오늘의 포춘 쿠키 (10개)
    {"id": "fortune_1", "cat": "fortune", "title": "행운의 포춘 오픈", "icon": "🥠", "desc": "첫 포춘 쿠키를 열어보았습니다."},
    {"id": "fortune_3", "cat": "fortune", "title": "소소한 행운가", "icon": "🥠", "desc": "포춘 쿠키를 3회 열어보았습니다."},
    {"id": "fortune_5", "cat": "fortune", "title": "기분 좋은 메시지", "icon": "🥠", "desc": "포춘 쿠키를 5회 열어보았습니다."},
    {"id": "fortune_7", "cat": "fortune", "title": "일주일의 행운", "icon": "🌟", "desc": "포춘 쿠키를 7회 열어보았습니다."},
    {"id": "fortune_14", "cat": "fortune", "title": "2주의 긍정 에너지", "icon": "🌟", "desc": "포춘 쿠키를 14회 열어보았습니다."},
    {"id": "fortune_21", "cat": "fortune", "title": "3주의 습관", "icon": "🌟", "desc": "포춘 쿠키를 21회 열어보았습니다."},
    {"id": "fortune_30", "cat": "fortune", "title": "한 달의 행운 수집가", "icon": "💫", "desc": "포춘 쿠키를 30회 열어보았습니다."},
    {"id": "fortune_50", "cat": "fortune", "title": "행운의 단골손님", "icon": "💫", "desc": "포춘 쿠키를 50회 열어보았습니다."},
    {"id": "fortune_75", "cat": "fortune", "title": "황금빛 포춘 마스터", "icon": "✨", "desc": "포춘 쿠키를 75회 열어보았습니다."},
    {"id": "fortune_100", "cat": "fortune", "title": "백 개의 기적", "icon": "👑", "desc": "포춘 쿠키를 100회 열어보았습니다."},

    # 8. 🌸 6단계 성장·진화 (10개)
    {"id": "stage_2", "cat": "growth", "title": "어린 줄기의 탄생", "icon": "🌿", "desc": "화분을 2단계(어린 줄기)로 진화시켰습니다."},
    {"id": "stage_3", "cat": "growth", "title": "무럭무럭 자라는 잎", "icon": "🪴", "desc": "화분을 3단계(자라나는 잎새)로 진화시켰습니다."},
    {"id": "stage_4", "cat": "growth", "title": "설레는 첫 꽃망울", "icon": "🌷", "desc": "화분을 4단계(첫 꽃망울)로 진화시켰습니다."},
    {"id": "stage_5", "cat": "growth", "title": "화사한 개화", "icon": "🌸", "desc": "화분을 5단계(탐스러운 개화)로 진화시켰습니다."},
    {"id": "stage_6", "cat": "growth", "title": "영광의 6단계 만개", "icon": "👑", "desc": "화분을 최종 6단계(영광의 만개&결실)로 키워냈습니다."},
    {"id": "exp_300", "cat": "growth", "title": "성장의 기쁨 (300 EXP)", "icon": "⭐", "desc": "누적 경험치 300 EXP를 달성했습니다."},
    {"id": "exp_600", "cat": "growth", "title": "정성의 결실 (600 EXP)", "icon": "⭐", "desc": "누적 경험치 600 EXP를 달성했습니다."},
    {"id": "exp_1000", "cat": "growth", "title": "천 점의 가드너 (1,000 EXP)", "icon": "🌟", "desc": "누적 경험치 1,000 EXP를 달성했습니다."},
    {"id": "exp_2000", "cat": "growth", "title": "베테랑 원예사 (2,000 EXP)", "icon": "🌟", "desc": "누적 경험치 2,000 EXP를 달성했습니다."},
    {"id": "exp_5000", "cat": "growth", "title": "전설의 가드너 (5,000 EXP)", "icon": "👑", "desc": "누적 경험치 5,000 EXP를 달성했습니다."},

    # 9. 🪴 5종 품종 & 화원 (10개)
    {"id": "grad_1", "cat": "garden", "title": "첫 번째 명예 졸업생", "icon": "🎓", "desc": "6단계 만개 화분을 화원에 처음으로 졸업 등록했습니다."},
    {"id": "grad_2", "cat": "garden", "title": "두 번째 졸업식", "icon": "🎓", "desc": "화분을 2회 졸업시켰습니다."},
    {"id": "grad_3", "cat": "garden", "title": "화원의 번영", "icon": "🪴", "desc": "화분을 3회 졸업시켰습니다."},
    {"id": "grad_5", "cat": "garden", "title": "원예 명예의 전당", "icon": "🪴", "desc": "화분을 5회 졸업시켰습니다."},
    {"id": "grad_10", "cat": "garden", "title": "식물원 원장님", "icon": "🏛️", "desc": "화분을 10회 졸업시켰습니다."},
    {"id": "spec_classic", "cat": "garden", "title": "다정한 화분의 꽃", "icon": "🌸", "desc": "기본 '다정한 화분'을 6단계 만개까지 키웠습니다."},
    {"id": "spec_sunflower", "cat": "garden", "title": "햇살 해바라기의 결실", "icon": "🌻", "desc": "'햇살 해바라기' 품종을 6단계 만개까지 키웠습니다."},
    {"id": "spec_cactus", "cat": "garden", "title": "선인장의 황금꽃", "icon": "🌵", "desc": "'동글 선인장' 품종을 6단계 만개까지 키웠습니다."},
    {"id": "spec_clover", "cat": "garden", "title": "네잎클로버의 기적", "icon": "🍀", "desc": "'행운의 클로버' 품종을 6단계 만개까지 키웠습니다."},
    {"id": "spec_cherry", "cat": "garden", "title": "봄날 벚꽃의 만개", "icon": "🌺", "desc": "'봄날 벚꽃나무' 품종을 6단계 만개까지 키웠습니다."},

    # 10. ⏰ 공직자 일과 & 힐링 (10개)
    {"id": "routine_morning", "cat": "office_life", "title": "상쾌한 모닝커피 ☕", "icon": "☕", "desc": "아침 출근 시간(07~09시)에 화분과 인사를 나누었습니다."},
    {"id": "routine_focus", "cat": "office_life", "title": "오전 집중 업무 🎯", "icon": "🎯", "desc": "오전 집중 업무 시간(10~12시)에 응원을 받았습니다."},
    {"id": "routine_lunch", "cat": "office_life", "title": "맛있는 점심시간 🍱", "icon": "🍱", "desc": "점심시간(12~13시)에 기분 좋은 인사를 나눴습니다."},
    {"id": "routine_stretch", "cat": "office_life", "title": "오후 3시 리프레시 💧", "icon": "💧", "desc": "나른한 오후 3시 스트레칭 알림을 확인했습니다."},
    {"id": "routine_ontime_leave", "cat": "office_life", "title": "칼퇴의 기쁨 🏃‍♂️", "icon": "🏃‍♂️", "desc": "퇴근 시간(17:30~19시)에 정시 퇴근 인사를 받았습니다."},
    {"id": "routine_overtime", "cat": "office_life", "title": "야근 속 따뜻한 위로 🌙", "icon": "🌙", "desc": "저녁 야근 시간(19시 이후)에 화분의 따뜻한 위로를 받았습니다."},
    {"id": "routine_midnight", "cat": "office_life", "title": "심야의 데스크 지킴이 🌌", "icon": "🌌", "desc": "늦은 밤(23시 이후) 조용한 연구/업무 중 인사를 나눴습니다."},
    {"id": "routine_idle_rest", "cat": "office_life", "title": "달콤한 3분 휴식 🧘", "icon": "🧘", "desc": "PC 3분 유휴 감지 힐링 메시지로 심호흡을 했습니다."},
    {"id": "routine_desk_guardian", "cat": "office_life", "title": "데스크의 든든한 수호자 🛡️", "icon": "🛡️", "desc": "공직자님의 책상 위를 굳건히 지키며 하루를 함께했습니다."},
    {"id": "routine_master", "cat": "office_life", "title": "공직 가드너 마스터 👑", "icon": "👑", "desc": "모든 시간대별 일과 루틴을 화분과 함께 완주했습니다."},

    # 11. 🐝 생태계 탐험 & 이벤트 (10개)
    {"id": "eco_first_meet", "cat": "eco_events", "title": "자연의 작은 손님", "icon": "🐝", "desc": "화분을 찾아온 생태계 방문객(벌, 나비, 새, 고양이 등)을 처음 맞이했습니다."},
    {"id": "bug_clear_1", "cat": "eco_events", "title": "벌레야 훠이~ 🐛", "icon": "🐛", "desc": "나뭇잎을 갉아먹는 애벌레를 클릭하여 1회 퇴치했습니다."},
    {"id": "bug_clear_5", "cat": "eco_events", "title": "명예 해충 방제사 🛡️", "icon": "🛡️", "desc": "화분에 나타난 벌레를 5회 퇴치하여 화분을 지켰습니다."},
    {"id": "bee_water", "cat": "eco_events", "title": "꿀벌의 달콤한 꿀 🍯", "icon": "🍯", "desc": "꿀벌이 놀러왔을 때 시원한 물을 주어 꿀 보너스를 받았습니다."},
    {"id": "ladybug_visit", "cat": "eco_events", "title": "행운의 무당벌레 🐞", "icon": "🐞", "desc": "화분을 기어오르는 귀여운 칠성무당벌레와 교감했습니다."},
    {"id": "bluebird_feather", "cat": "eco_events", "title": "파랑새의 황금 깃털 🐦", "icon": "🐦", "desc": "날아온 아기 파랑새를 맞이하고 행운의 황금 깃털을 얻었습니다."},
    {"id": "cat_highfive", "cat": "eco_events", "title": "냥젤리 하이파이브 🐾", "icon": "🐾", "desc": "화분에 장난치러 온 길고양이의 핑크 젤리 발과 하이파이브를 나눴습니다."},
    {"id": "rain_rainbow", "cat": "eco_events", "title": "단비와 오색 무지개 🌈", "icon": "🌈", "desc": "화분 위로 지나가는 촉촉한 단비 구름과 무지개를 목격했습니다."},
    {"id": "firefly_night", "cat": "eco_events", "title": "한여름 밤의 반딧불이 ✨", "icon": "✨", "desc": "어둠 속에서 반짝이며 화분을 밝히는 반딧불이 무리를 만났습니다."},
    {"id": "eco_master", "cat": "eco_events", "title": "생태계 가디언 마스터 👑", "icon": "👑", "desc": "모든 생태계 방문객 및 환경 이벤트와 교감을 달성했습니다."}
]
