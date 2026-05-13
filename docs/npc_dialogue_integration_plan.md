# NPC Dialogue Integration Plan

## 1. Purpose

Ce document prepare l'integration future des PNJ et des dialogues dans le jeu.

Il ne decrit pas une implementation immediate. Il sert a cadrer la separation entre la logique de quete deja existante, l'identite narrative des PNJ, et les textes longs qui pourraient etre affiches plus tard.

Le but est de pouvoir ajouter progressivement des PNJ, des introductions, des textes d'offre, des rappels de progression, des textes de completion et des transitions sans refondre le systeme de quetes actuel.

## 2. Current state

- Les quetes existent deja dans `data/quests.json`.
- Les quetes portent la logique gameplay : objectifs, recompenses, ordre, `next_quests`.
- Les arcs narratifs PNJ sont cadres dans `docs/forest_npc_quest_arcs.md`.
- Le plan du chapitre Foret est cadre dans `docs/forest_chapter_content_plan.md`.
- Aucun systeme PNJ/dialogue dedie n'est necessaire immediatement.

## 3. Design goals

- Garder `data/quests.json` lisible.
- Eviter de melanger logique gameplay et textes longs.
- Permettre aux PNJ de porter les quetes plus tard.
- Permettre l'affichage futur d'intros, textes d'offre, textes de progression, completions et transitions.
- Garder une architecture simple.
- Eviter une refonte globale.

## 4. What not to implement yet

- Pas de `data/npcs.json` immediat.
- Pas de `data/npc_dialogues.json` immediat.
- Pas de `systems/npcs.py`.
- Pas de `systems/dialogues.py`.
- Pas de dialogue a choix.
- Pas de reputation PNJ.
- Pas de branches narratives complexes.
- Pas de coordonnees de PNJ.
- Pas d'UI de dialogue complete.

## 5. Recommended data separation

| File | Responsibility |
|---|---|
| `data/quests.json` | quest gameplay: objectives, rewards, order, next_quests |
| future `data/npcs.json` | NPC identity, role, chapter, related quests, related zones |
| future `data/npc_dialogues.json` | long NPC texts: intro, offer, progress, completion, transition, epilogue |
| `docs/forest_npc_quest_arcs.md` | narrative writing and quest arc design |
| `docs/forest_chapter_content_plan.md` | chapter structure, zones, enemies, systems |

## 6. Future file: data/npcs.json

`data/npcs.json` pourrait rester tres simple. Il devrait identifier les PNJ, leur chapitre, leur role fonctionnel, les quetes qu'ils portent ou commentent, et les zones auxquelles ils sont narrativement lies.

Ce fichier ne devrait pas contenir de longs textes narratifs. Il ne devrait pas non plus contenir de coordonnees ou de placement physique.

Exemple de structure future :

```json
{
  "quartermaster_brindle": {
    "name": "Quartermaster Brindle",
    "chapter": "forest",
    "role": "combat_quest_giver",
    "related_quests": [
      "forest_secure_outskirts",
      "forest_pack_watches"
    ],
    "related_zones": [
      "forest_rat_outskirts",
      "forest_young_goblin_trail",
      "forest_stray_wolf_path"
    ]
  }
}
```

Cette structure reste volontairement minimale. Elle sert a relier un PNJ aux systemes existants sans imposer encore de systeme de dialogue, de carte ou d'interface.
