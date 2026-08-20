"""
Headless Unit & Integration Tests for v2.0.0 Shop & Pet Companions System.
"""
import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication

# Ensure offscreen Qt
os.environ["QT_QPA_PLATFORM"] = "offscreen"

app = QApplication.instance() or QApplication(sys.argv)

from ai_plant.database import DatabaseManager
from ai_plant.config import ConfigManager
from ai_plant.plant_engine import PlantEngine
from ai_plant.shop_data import SAUCER_CATALOG, PET_CATALOG
from ai_plant.ui.character_widget import PlantCharacterWidget
from ai_plant.ui.garden_dialog import GardenDialog


def test_coin_economy_and_inventory():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_plant.db")
        db = DatabaseManager(db_path)
        cfg = ConfigManager()
        engine = PlantEngine(db, cfg)

        # 1. Check initial retroactive coins (100 base + 0 ach = 100)
        initial_coins = engine.get_coins()
        assert initial_coins >= 100, f"Expected at least 100 coins, got {initial_coins}"

        # 2. Add coins
        engine.add_coins(500)
        assert engine.get_coins() == initial_coins + 500

        # 3. Spend coins on saucer 'wood' (cost 100)
        wood_cost = SAUCER_CATALOG["wood"]["cost"]
        assert engine.purchase_item("saucer", "wood", wood_cost) is True
        assert db.is_item_purchased("saucer", "wood") is True

        # 4. Equip saucer
        assert engine.equip_item("saucer", "wood") is True
        assert engine.get_equipped_saucer() == "wood"

        # 5. Purchase and equip pet 'cat_calico' (cost 250)
        cat_cost = PET_CATALOG["cat_calico"]["cost"]
        assert engine.purchase_item("pet", "cat_calico", cat_cost) is True
        assert db.is_item_purchased("pet", "cat_calico") is True
        assert engine.equip_item("pet", "cat_calico") is True
        assert engine.get_equipped_pet() == "cat_calico"

        # 6. Test CharacterWidget rendering with equipped saucer and pet
        widget = PlantCharacterWidget(scale_pct=100)
        widget.set_equipped_saucer("wood")
        widget.set_equipped_pet("cat_calico")
        widget.resize(150, 150)
        widget.show()
        app.processEvents()

        # Step pet animations
        for _ in range(50):
            widget._on_master_anim_tick()
        app.processEvents()
        widget.close()

        # 7. Test GardenDialog with 6 tabs & shop
        dlg = GardenDialog(engine, db, cfg)
        assert dlg.tabs.count() == 6, f"Expected 6 tabs, got {dlg.tabs.count()}"
        assert dlg.tabs.tabText(0) == "🪴 화원"
        assert dlg.tabs.tabText(1) == "🌸 품종"
        assert dlg.tabs.tabText(2) == "🏪 상점"
        assert dlg.tabs.tabText(3) == "🏆 업적"
        assert dlg.tabs.tabText(4) == "📊 마음날씨"
        assert dlg.tabs.tabText(5) == "🥠 포춘"
        dlg.show()
        app.processEvents()
        dlg.close()

        print("=== All v2.0.0 tests passed successfully! ===")

if __name__ == "__main__":
    test_coin_economy_and_inventory()
