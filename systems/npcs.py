REQUIRED_NPC_FIELDS = {
    "name",
    "chapter",
    "role",
    "related_quests",
    "related_zones",
}


def get_npc(npcs_data, npc_id):
    if not isinstance(npcs_data, dict) or not npc_id:
        return None
    npc = npcs_data.get(npc_id)
    return npc if isinstance(npc, dict) else None


def get_npcs_by_chapter(npcs_data, chapter):
    if not isinstance(npcs_data, dict):
        return {}
    return {
        npc_id: npc
        for npc_id, npc in npcs_data.items()
        if isinstance(npc, dict) and npc.get("chapter") == chapter
    }


def get_npc_quest_ids(npcs_data, npc_id):
    npc = get_npc(npcs_data, npc_id)
    if not npc:
        return []
    related_quests = npc.get("related_quests", [])
    return list(related_quests) if isinstance(related_quests, list) else []


def get_npc_for_quest(npcs_data, quests_data, quest_id):
    if not isinstance(quests_data, dict):
        return None
    quest = quests_data.get(quest_id)
    if not isinstance(quest, dict):
        return None
    return get_npc(npcs_data, quest.get("npc_id"))


def validate_npc_data(npcs_data, quests_data):
    errors = []
    if not isinstance(npcs_data, dict):
        return ["NPC data must be a dictionary."]
    if not isinstance(quests_data, dict):
        return ["Quest data must be a dictionary."]

    for npc_id, npc in npcs_data.items():
        if not isinstance(npc, dict):
            errors.append(f"{npc_id}: NPC entry must be a dictionary.")
            continue

        missing_fields = sorted(REQUIRED_NPC_FIELDS - set(npc))
        if missing_fields:
            errors.append(f"{npc_id}: missing fields {', '.join(missing_fields)}.")

        related_quests = npc.get("related_quests", [])
        if not isinstance(related_quests, list):
            errors.append(f"{npc_id}: related_quests must be a list.")
            related_quests = []
        for quest_id in related_quests:
            if quest_id not in quests_data:
                errors.append(f"{npc_id}: unknown related quest {quest_id}.")

        related_zones = npc.get("related_zones", [])
        if not isinstance(related_zones, list):
            errors.append(f"{npc_id}: related_zones must be a list.")

    for quest_id, quest in quests_data.items():
        if not isinstance(quest, dict) or quest.get("chapter") != "forest":
            continue
        npc_id = quest.get("npc_id")
        if npc_id not in npcs_data:
            errors.append(f"{quest_id}: npc_id {npc_id!r} does not reference an NPC.")
            continue
        npc_quests = get_npc_quest_ids(npcs_data, npc_id)
        if quest_id not in npc_quests:
            errors.append(f"{quest_id}: NPC {npc_id} does not reference this quest.")

    return errors
