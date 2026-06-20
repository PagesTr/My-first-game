import xml.etree.ElementTree as ET
from pathlib import Path

import pygame

from ui.screens.exploration_screen import TiledMap


PROJECT_ROOT = Path(__file__).resolve().parent.parent

EXPECTED_MAP_NPCS = {
    "assets/maps/town_01.tmx": {
        "camp_quartermaster",
        "old_herbalist",
        "bone_scribe",
    },
    "assets/maps/forest_01.tmx": {
        "retired_scout",
        "dungeon_warden",
    },
}


def get_property(object_node, name):
    properties = object_node.find("properties")
    if properties is None:
        return None
    for property_node in properties.findall("property"):
        if property_node.attrib.get("name") == name:
            return property_node.attrib.get("value") or property_node.text
    return None


def test_tiled_maps_define_expected_npc_objects():
    for relative_path, expected_npc_ids in EXPECTED_MAP_NPCS.items():
        root = ET.parse(PROJECT_ROOT / relative_path).getroot()
        npc_layer = next(
            group
            for group in root.findall("objectgroup")
            if group.attrib.get("name") == "91_npcs"
        )
        objects = npc_layer.findall("object")

        assert {get_property(node, "npc_id") for node in objects} == expected_npc_ids
        for node in objects:
            assert (node.attrib.get("type") or node.attrib.get("class")) == "npc"
            assert node.attrib.get("gid")
            assert get_property(node, "display_name")
            assert get_property(node, "trigger_type") == "dialogue"
            assert get_property(node, "requires_interact") == "true"


def test_tiled_map_builds_npc_tile_object_with_bottom_anchor():
    tiled_map = TiledMap.__new__(TiledMap)
    tiled_map.tiles = {7: pygame.Surface((16, 24), pygame.SRCALPHA)}
    object_node = ET.fromstring(
        """
        <object name="npc_test" type="npc" gid="7" x="100" y="200" width="24" height="36">
          <properties>
            <property name="display_name" value="Test NPC"/>
            <property name="npc_id" value="test_npc"/>
            <property name="prompt" value="E - Talk"/>
            <property name="requires_interact" type="bool" value="true"/>
            <property name="trigger_id" value="talk_test_npc"/>
            <property name="trigger_type" value="dialogue"/>
          </properties>
        </object>
        """
    )

    npc = tiled_map._build_npc(object_node)

    assert npc["npc_id"] == "test_npc"
    assert npc["rect"] == pygame.Rect(100, 164, 24, 36)
    assert npc["collision_rect"].midbottom == npc["rect"].midbottom
    assert npc["sprite"].get_size() == (24, 36)
