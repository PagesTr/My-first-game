from systems.quests import accept_quest, record_quest_event


DIALOGUE_STATES = {
    "quest_offer",
    "progress",
    "completion",
    "transition",
}

REQUIRED_QUEST_DIALOGUE_STATES = {
    "quest_offer",
    "progress",
    "completion",
}

DEFAULT_PLAYER_DIALOGUE_STATE = {
    "introduced_npcs": [],
    "completed_quests_seen": [],
}


def get_npc_dialogues(dialogues_data, npc_id):
    if not isinstance(dialogues_data, dict) or not npc_id:
        return None
    dialogue = dialogues_data.get(npc_id)
    return dialogue if isinstance(dialogue, dict) else None


def get_npc_intro(dialogues_data, npc_id):
    npc_dialogues = get_npc_dialogues(dialogues_data, npc_id)
    if not npc_dialogues:
        return ""
    intro = npc_dialogues.get("intro", "")
    return intro if isinstance(intro, str) else ""


def get_quest_dialogues(dialogues_data, npcs_data, quests_data, quest_id):
    if not isinstance(quests_data, dict):
        return {}
    quest = quests_data.get(quest_id)
    if not isinstance(quest, dict):
        return {}
    npc_id = quest.get("npc_id")
    if not isinstance(npcs_data, dict) or npc_id not in npcs_data:
        return {}
    npc_dialogues = get_npc_dialogues(dialogues_data, npc_id)
    if not npc_dialogues:
        return {}
    quests = npc_dialogues.get("quests", {})
    if not isinstance(quests, dict):
        return {}
    quest_dialogues = quests.get(quest_id, {})
    return quest_dialogues if isinstance(quest_dialogues, dict) else {}


def select_quest_dialogue(dialogues_data, npcs_data, quests_data, quest_id, state):
    quest_dialogues = get_quest_dialogues(dialogues_data, npcs_data, quests_data, quest_id)
    if not quest_dialogues:
        return ""
    if state in DIALOGUE_STATES:
        text = quest_dialogues.get(state)
        if isinstance(text, str) and text:
            return text
        return ""
    fallback = quest_dialogues.get("quest_offer", "")
    return fallback if isinstance(fallback, str) else ""


def ensure_player_dialogue_state(player):
    if not isinstance(player, dict):
        return {
            "introduced_npcs": [],
            "completed_quests_seen": [],
        }

    state = player.get("npc_dialogue_state")
    if not isinstance(state, dict):
        state = {}
        player["npc_dialogue_state"] = state

    for key, default_value in DEFAULT_PLAYER_DIALOGUE_STATE.items():
        if not isinstance(state.get(key), list):
            state[key] = list(default_value)
    return state


def build_npc_conversation(player, npcs_data, quests_data, dialogues_data, npc_id):
    npc = npcs_data.get(npc_id) if isinstance(npcs_data, dict) else None
    if not isinstance(player, dict) or not isinstance(npc, dict):
        return _empty_conversation(npc_id)

    dialogue_state = player.get("npc_dialogue_state", {})
    if not isinstance(dialogue_state, dict):
        dialogue_state = {}
    introduced_npcs = dialogue_state.get("introduced_npcs", [])
    completed_seen = dialogue_state.get("completed_quests_seen", [])
    introduced_npcs = introduced_npcs if isinstance(introduced_npcs, list) else []
    completed_seen = completed_seen if isinstance(completed_seen, list) else []

    quests_state = player.get("quests", {})
    if not isinstance(quests_state, dict):
        quests_state = {}
    related_quest_ids = _get_ordered_related_quest_ids(npc, quests_data)
    pages = []
    mark_introduced = npc_id not in introduced_npcs

    if mark_introduced:
        intro = get_npc_intro(dialogues_data, npc_id)
        _append_text_pages(pages, "intro", intro)

    completed_quest_id = _first_matching_quest_id(
        related_quest_ids,
        quests_state.get("completed", []),
        excluded_ids=completed_seen,
    )
    if completed_quest_id:
        _append_quest_dialogue_pages(
            pages,
            dialogues_data,
            npcs_data,
            quests_data,
            completed_quest_id,
            ("completion", "transition"),
        )
        return {
            "npc_id": npc_id,
            "pages": pages,
            "mark_introduced": mark_introduced,
            "completed_quest_id": completed_quest_id,
            "accept_quest_id": None,
        }

    available_quest_id = _first_matching_quest_id(
        related_quest_ids,
        quests_state.get("available", []),
    )
    if available_quest_id:
        _append_quest_dialogue_pages(
            pages,
            dialogues_data,
            npcs_data,
            quests_data,
            available_quest_id,
            ("quest_offer",),
        )
        _append_quest_summary_page(pages, available_quest_id, "available")
        return {
            "npc_id": npc_id,
            "pages": pages,
            "mark_introduced": mark_introduced,
            "completed_quest_id": None,
            "accept_quest_id": available_quest_id,
        }

    active_quest_id = _first_matching_quest_id(
        related_quest_ids,
        quests_state.get("active", []),
    )
    if active_quest_id:
        _append_quest_dialogue_pages(
            pages,
            dialogues_data,
            npcs_data,
            quests_data,
            active_quest_id,
            ("progress",),
        )
        _append_quest_summary_page(pages, active_quest_id, "active")

    if not pages:
        intro = get_npc_intro(dialogues_data, npc_id)
        _append_text_pages(pages, "intro", intro)

    return {
        "npc_id": npc_id,
        "pages": pages,
        "mark_introduced": mark_introduced,
        "completed_quest_id": None,
        "accept_quest_id": None,
    }


def apply_npc_conversation_result(player, quests_data, conversation):
    if not isinstance(player, dict) or not isinstance(conversation, dict):
        return {"introduced": False, "accepted_quest_id": None, "completed_seen": None}

    state = ensure_player_dialogue_state(player)
    npc_id = conversation.get("npc_id")
    introduced = False
    if conversation.get("mark_introduced") and npc_id and npc_id not in state["introduced_npcs"]:
        state["introduced_npcs"].append(npc_id)
        introduced = True

    completed_quest_id = conversation.get("completed_quest_id")
    completed_seen = None
    if completed_quest_id and completed_quest_id not in state["completed_quests_seen"]:
        state["completed_quests_seen"].append(completed_quest_id)
        completed_seen = completed_quest_id

    accepted_quest_id = None
    quest_id = conversation.get("accept_quest_id")
    if quest_id:
        if accept_quest(player, quests_data, quest_id):
            accepted_quest_id = quest_id

    record_quest_event(
        player,
        quests_data,
        {
            "type": "talk_to_npc",
            "target": npc_id,
            "amount": 1,
        },
    )

    return {
        "introduced": introduced,
        "accepted_quest_id": accepted_quest_id,
        "completed_seen": completed_seen,
    }


def _empty_conversation(npc_id):
    return {
        "npc_id": npc_id,
        "pages": [],
        "mark_introduced": False,
        "completed_quest_id": None,
        "accept_quest_id": None,
    }


def _get_ordered_related_quest_ids(npc, quests_data):
    related_quests = npc.get("related_quests", []) if isinstance(npc, dict) else []
    if not isinstance(related_quests, list) or not isinstance(quests_data, dict):
        return []
    return sorted(
        (quest_id for quest_id in related_quests if quest_id in quests_data),
        key=lambda quest_id: quests_data[quest_id].get("order", 0),
    )


def _first_matching_quest_id(related_quest_ids, candidate_ids, excluded_ids=None):
    candidate_ids = candidate_ids if isinstance(candidate_ids, list) else []
    excluded_ids = excluded_ids if isinstance(excluded_ids, list) else []
    return next(
        (
            quest_id
            for quest_id in related_quest_ids
            if quest_id in candidate_ids and quest_id not in excluded_ids
        ),
        None,
    )


def _append_quest_dialogue_pages(
    pages,
    dialogues_data,
    npcs_data,
    quests_data,
    quest_id,
    states,
):
    for state in states:
        text = select_quest_dialogue(
            dialogues_data,
            npcs_data,
            quests_data,
            quest_id,
            state,
        )
        _append_text_pages(pages, state, text, quest_id=quest_id)


def _append_quest_summary_page(pages, quest_id, quest_status):
    pages.append({
        "state": "quest_summary",
        "quest_id": quest_id,
        "quest_status": quest_status,
        "text": "",
    })


def _append_text_pages(pages, state, text, quest_id=None):
    if not isinstance(text, str) or not text:
        return
    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
    for paragraph in paragraphs:
        page = {"state": state, "text": paragraph}
        if quest_id is not None:
            page["quest_id"] = quest_id
        pages.append(page)


def validate_dialogue_data(dialogues_data, npcs_data, quests_data):
    errors = []
    if not isinstance(dialogues_data, dict):
        return ["Dialogue data must be a dictionary."]
    if not isinstance(npcs_data, dict):
        return ["NPC data must be a dictionary."]
    if not isinstance(quests_data, dict):
        return ["Quest data must be a dictionary."]

    for npc_id, npc_dialogues in dialogues_data.items():
        if npc_id not in npcs_data:
            errors.append(f"{npc_id}: dialogue references an unknown NPC.")
            continue
        if not isinstance(npc_dialogues, dict):
            errors.append(f"{npc_id}: dialogue entry must be a dictionary.")
            continue

        intro = npc_dialogues.get("intro")
        if not isinstance(intro, str) or not intro:
            errors.append(f"{npc_id}: intro must be a non-empty string.")

        quest_dialogues = npc_dialogues.get("quests", {})
        if not isinstance(quest_dialogues, dict):
            errors.append(f"{npc_id}: quests must be a dictionary.")
            continue

        for quest_id, state_texts in quest_dialogues.items():
            quest = quests_data.get(quest_id)
            if not isinstance(quest, dict):
                errors.append(f"{npc_id}: unknown dialogue quest {quest_id}.")
                continue
            if quest.get("npc_id") != npc_id:
                errors.append(f"{quest_id}: dialogue is under {npc_id}, but quest uses {quest.get('npc_id')!r}.")
            if not isinstance(state_texts, dict):
                errors.append(f"{quest_id}: quest dialogue must be a dictionary.")
                continue

            missing_states = sorted(REQUIRED_QUEST_DIALOGUE_STATES - set(state_texts))
            if missing_states:
                errors.append(f"{quest_id}: missing dialogue states {', '.join(missing_states)}.")
            for state, text in state_texts.items():
                if state not in DIALOGUE_STATES:
                    errors.append(f"{quest_id}: unknown dialogue state {state}.")
                if not isinstance(text, str) or not text:
                    errors.append(f"{quest_id}: {state} must be a non-empty string.")

    for quest_id, quest in quests_data.items():
        if not isinstance(quest, dict) or quest.get("chapter") != "forest":
            continue
        npc_id = quest.get("npc_id")
        npc_dialogues = get_npc_dialogues(dialogues_data, npc_id)
        quest_dialogues = (
            npc_dialogues.get("quests", {})
            if isinstance(npc_dialogues, dict)
            else {}
        )
        if quest_id not in quest_dialogues:
            errors.append(f"{quest_id}: missing dialogue entry.")

    return errors
