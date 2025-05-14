import logging
import os
import pytz
import json
import asyncio

from datetime import datetime


TIMEZONE_INFO = pytz.timezone(os.getenv("TIMEZONE_INFO", pytz.UTC.zone))


def get_logger(name: str, level: int = logging.DEBUG) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    formatter = logging.Formatter("%(asctime)s - %(module)s.%(funcName)s - %(levelname)s: %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def get_datetime() -> datetime:
    return datetime.now(tz=TIMEZONE_INFO)

def get_datetime_formatted() -> str:
    return get_datetime().strftime("%d.%m.%Y %H:%M:%S")

def load_or_create_json(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def extended_friendly_names(friendly_dict: dict[str, str]) -> dict[str, set[str]]:
    data = load_or_create_json(os.getenv("FRIENDLY_NAMES"))
    result = {}

    for entity_id, new_name in friendly_dict.items():
        if not new_name:
            continue

        # Načíst existující jména jako množinu
        existing = set(data.get(entity_id, {}).get("friendly_names", []))
        existing.add(new_name)  # Přidat nové jméno


        data[entity_id] = {"friendly_names": list(existing)}
        result[entity_id] =  existing 

    save_json(os.getenv("FRIENDLY_NAMES"), data)
    return result

def find_entity_id_by_friendly_name(friendly_name: str) -> str | None:
    with open(os.getenv("FRIENDLY_NAMES"), "r", encoding="utf-8") as f:
        data = json.load(f)
    
    query = friendly_name.lower().strip()
    for entity_id, entry in data.items():
        for name in entry.get("friendly_names", []):
            if query == name.lower().strip():
                return entity_id
    return None

def get_friendly_name_map_string(domain: str) -> str:
    with open(os.getenv("FRIENDLY_NAMES"), "r", encoding="utf-8") as f:
        data = json.load(f)

    parts = []
    for entity_id, entry in data.items():
        if entity_id.startswith(f"{domain}."):
            for name in entry.get("friendly_names", []):
                parts.append(f"{name.lower().strip()}-{entity_id}")
    return ", ".join(parts)


def load_scenes():
    if os.path.exists(os.getenv("SCENES_PATH")):
        with open(os.getenv("SCENES_PATH"), "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_scene(name: str, actions: list[dict]):
    scenes = load_scenes()
    scenes[name] = { "actions": actions }
    with open(os.getenv("SCENES_PATH"), "w", encoding="utf-8") as f:
        json.dump(scenes, f, indent=4, ensure_ascii=False)

async def activate_scene(dm, ha_instance, scene_name: str):
        scenes = load_scenes()
        scene = scenes.get(scene_name)

        if not scene:
            await dm.send_message({
                "type": "chat-dm",
                "data": f"Scéna '{scene_name}' neexistuje."
            })
            return

        actions = scene.get("actions", [])

        for action in actions:
            dm.on_receive_message(action)

        await dm.send_message({
            "type": "chat-dm",
            "data": f"Scéna '{scene_name}' byla aktivována."
        })
        await asyncio.sleep(1) 
        await dm.send_message({"type": "state_update","data": ha_instance.get_all_entities()})
        
        if dm.ttsEnabled:
            await dm.synthesize_and_wait(f"Scéna {scene_name} byla aktivována.")