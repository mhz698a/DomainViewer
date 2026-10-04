# tests/test_type_underwear_and_about.py

import json
from pathlib import Path
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

import pytest

from domain_visor.type_underwear_editor import (
    load_global_type_underwear, save_global_type_underwear, TypeUnderwearEditorDialog
)
from domain_visor.about_dialog import load_about_data, AboutDialog
from domain_visor.character_dialog import CharacterEditDialog

@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app

def test_type_underwear_file_creation(tmp_path):
    json_path = tmp_path / "type_under_list.json"

    # Must auto-create file if non-existent
    items = load_global_type_underwear(json_path)
    assert json_path.exists()
    assert "Boybrief" in items
    assert len(items) > 5

    # Check JSON structure
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "type_underwear" in data
    assert isinstance(data["type_underwear"], list)

def test_type_underwear_editor_dialog(qapp, tmp_path):
    json_path = tmp_path / "type_under_list.json"
    save_global_type_underwear(["Option A", "Option B"], json_path)

    dlg = TypeUnderwearEditorDialog(filepath=json_path)
    assert dlg.list_widget.count() == 2
    assert dlg.list_widget.item(0).text() == "Option A"

    # Test saving modified items
    dlg.list_widget.addItem("Option C")
    dlg.save_and_close()

    loaded = load_global_type_underwear(json_path)
    assert loaded == ["Option A", "Option B", "Option C"]

def test_discontinued_underwear_in_character_dialog(qapp, tmp_path):
    # Set global list to only Option A and Option B
    global_path = tmp_path / "type_under_list.json"
    save_global_type_underwear(["Option A", "Option B"], global_path)

    # Patch default path in load_global_type_underwear to use global_path
    import domain_visor.type_underwear_editor as twe
    orig_default = twe.DEFAULT_TYPE_UNDERWEAR_PATH
    twe.DEFAULT_TYPE_UNDERWEAR_PATH = global_path

    try:
        # Character has Option A and OldDiscontinuedOption
        char_data = {
            "year": 2024,
            "position": 1,
            "name": "TestChar",
            "alterego": "Alter",
            "birthday": "2000-01-01",
            "age": 24,
            "type_underwear": ["Option A", "OldDiscontinuedOption"],
            "character_path": str(tmp_path / "char_folder")
        }

        # Create dummy char folder
        char_dir = tmp_path / "char_folder"
        char_dir.mkdir(parents=True, exist_ok=True)
        (char_dir / "__TestChar__.json").write_text(json.dumps({"character_data": char_data}))

        dialog = CharacterEditDialog(char_data)
        
        # Check items in list_underwear
        items_text = [dialog.list_underwear.item(i).text() for i in range(dialog.list_underwear.count())]
        assert "Option A" in items_text
        assert "Option B" in items_text
        assert "OldDiscontinuedOption (Descontinuado)" in items_text

        # Verify Option A is checked
        item_a = [dialog.list_underwear.item(i) for i in range(dialog.list_underwear.count()) if dialog.list_underwear.item(i).data(Qt.ItemDataRole.UserRole + 1) == "Option A"][0]
        assert item_a.checkState() == Qt.CheckState.Checked

        # Verify OldDiscontinuedOption is marked as discontinued
        item_disc = [dialog.list_underwear.item(i) for i in range(dialog.list_underwear.count()) if dialog.list_underwear.item(i).data(Qt.ItemDataRole.UserRole + 1) == "OldDiscontinuedOption"][0]
        assert item_disc.data(Qt.ItemDataRole.UserRole) is True

    finally:
        twe.DEFAULT_TYPE_UNDERWEAR_PATH = orig_default

def test_about_data_file_creation(tmp_path):
    json_path = tmp_path / "about_it.json"

    # Auto-create file if non-existent
    data = load_about_data(json_path)
    assert json_path.exists()
    assert data == {"mision": "", "vision": ""}

    # Save custom data
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"mision": "Nuestra misión", "vision": "Nuestra visión"}, f)

    data = load_about_data(json_path)
    assert data["mision"] == "Nuestra misión"
    assert data["vision"] == "Nuestra visión"

def test_about_dialog(qapp, tmp_path):
    json_path = tmp_path / "about_it.json"
    
    # Test empty fallback text
    load_about_data(json_path)
    dlg = AboutDialog(filepath=json_path)
    assert dlg.windowTitle() == "Acerca de este visor"

    # Test custom mission and vision text
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"mision": "Mision Test", "vision": "Vision Test"}, f)

    dlg_custom = AboutDialog(filepath=json_path)
    assert dlg_custom.windowTitle() == "Acerca de este visor"
