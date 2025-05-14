import os

from typing import Optional, Literal
from pydantic import BaseModel, Field

from langchain_core.tools import tool

from backend.ha import HA, LIGHTS, CLIMATE, SCENES
from backend.utils import get_logger

logger = get_logger("ha_tools")


ha_instance = HA(token=os.getenv("HA_TOKEN"))


class SetLightArgs(BaseModel):
    action: bool = Field(..., description='Akce rozsvícení / zapnutí (`True`) nebo zhasnutí / vypnutí (`False`) světla. Pokud je požadavek o změně jasu nebo barvy, tak vždy uvažuj `action` jako rozsvícení tedy nastav na `True`.')
    entity_id: Literal[*list(LIGHTS.keys())] = Field( #type:ignore
        ...,
        description=f'Název světelného zařízení. Seznam světelných zařízení s jejich lidsky čitelnými názvy:\n{"\n".join(["- " + name + ": " + "; ".join(synonyms) for name, synonyms in LIGHTS.items()])}'
    )
    brightness: Optional[int] = Field(default=None, description='Úroveň jasu od 0 do 100 procent', ge=0, le=100)
    color_name: Optional[str] = Field(default=None, description='Název barvy anglicky například: "red" OR "blue" OR "white"')

@tool("set_light", args_schema=SetLightArgs, return_direct=True)
def set_light(
    action: bool,
    entity_id: str,
    brightness: Optional[int] = None,
    color_name: Optional[str] = None
) -> str:
    """
    Funkce, které slouží pro ovládání světelných zařízaní jako jsou světla, lampy, apod.
    Světelná zařízení jsou vždy označena identifikátorem `entity_id`, kde ke každému identifikátoru jsou přiřazeny očekávaná lidská označení.
    Volej tuto funkci vždy v případech, když přijde požadavek na změnu stavu světelného zařízení, např: rozsviť/zhasni, změna jasu nebo barvy.
    """
    if brightness:
        brightness = int((brightness / 100) * 255)

    command = f"[LIGHT {entity_id}] - action: {action}; brightness: {brightness}; color: {color_name}"
    logger.debug(command)
    
    result = ha_instance.control_light("on" if action else "off", entity_id, brightness, color_name)
    if not isinstance(result, str):
        result = command
    return result


class GetLightArgs(BaseModel):
    entity_id: Literal[*list(LIGHTS.keys())] = Field( #type:ignore
        ...,
        description=f'Název světelného zařízení. Seznam světelných zařízení s jejich lidsky čitelnými názvy:\n{"\n".join(["- " + name + ": " + "; ".join(synonyms) for name, synonyms in LIGHTS.items()])}'
    )
    states: Optional[list[Literal["is_active", "brightness", "color"]]] = Field(
        default=None,
        description="""Slouží k výběru specifických stavů, které výslovně zajímají uživatele. Pokud nespecifikuje nebo se zajímá o všechny stavy ponech prázdné (`None`), jinak vyber podmnožinu z:
- "is_active": Uživatel se zajímá o aktivitu světla, zda je zapnuto / vypnuto
- "brightness": Uživatel se zajímá o intenzitu jasu
- "color": Uživatel se zajíma o barvu osvětlení"""
    )

@tool("get_light", args_schema=GetLightArgs, return_direct=True)
def get_light(
    entity_id: str,
    states: Optional[list[str]] = None
) -> str:
    """
    Funkce, které slouží pro získávání informací o světelných zařízaní jako jsou světla, lampy, apod.
    Světelná zařízení jsou vždy označena identifikátorem `entity_id`, kde ke každému identifikátoru jsou přiřazeny očekávaná lidská označení.
    Volej tuto funkci vždy v případech, když přijde požadavek na zisk aktuálního stavu světelného zařízení.
    """
    logger.debug(f"[LIGHT {entity_id}] - Get state")

    current_state = ha_instance.get_state(entity_id)
    logger.debug(current_state)
    if isinstance(current_state, str):
        return f"Prvek {entity_id} není k dispozici."

    result = f"Current state [LIGHT {entity_id}] -"
    if states is None or "is_active" in states:
        result += f" state: {current_state["state"]};"
    if states is None or "brightness" in states:
        result += f" brightness: {((current_state["attributes"]["brightness"]/255)*100) if current_state["attributes"]["brightness"] else None};"
    if states is None or "color" in states:
        result += f" rgb_color: {current_state["attributes"]["rgb_color"]};"

    return result


class SetTemperatureArgs(BaseModel):
    entity_id: Literal[*list(CLIMATE.keys())] = Field( # type:ignore
        ...,
        description=f'Název topného zařízení. Seznam topných zařízení s jejich lidsky čitelnými názvy:\n{"\n".join(["- " + name + ": " + "; ".join(synonyms) for name, synonyms in CLIMATE.items()])}'
    )
    temperature: float = Field(..., description='Požadovaná teplota ve stupních Celsia. Očekávaný rozsah je od 5 do 30 stupňů s krokem 0.5')

@tool("set_temperature", args_schema=SetTemperatureArgs, return_direct=True)
def set_temperature(
    entity_id: str,
    temperature: float
) -> str:
    """
    Funkce, které slouží pro ovládání topných zařízaní jako jsou radiátory nebo topení.
    Topná zařízení jsou vždy označena identifikátorem `entity_id`, kde ke každému identifikátoru jsou přiřazeny očekávaná lidská označení.
    Volej tuto funkci vždy v případech, když přijde požadavek na změnu stavu topného zařízení, např: změna teploty, zatopení.
    """
    command = f"[CLIMATE {entity_id}] - temperature: {temperature}"
    logger.debug(command)

    result = ha_instance.set_temperature(entity_id, temperature)
    if not isinstance(result, str):
        result = command
    return result


class GetTemperatureArgs(BaseModel):
    entity_id: Literal[*list(CLIMATE.keys())] = Field( # type:ignore
        ...,
        description=f'Název topného zařízení. Seznam topných zařízení s jejich lidsky čitelnými názvy:\n{"\n".join(["- " + name + ": " + "; ".join(synonyms) for name, synonyms in CLIMATE.items()])}'
    )
    states: Optional[list[Literal["is_active", "temperature", "current_temperature"]]] = Field(
        default=None,
        description="""Slouží k výběru specifických stavů, které výslovně zajímají uživatele. Pokud nespecifikuje nebo se zajímá o všechny stavy ponech prázdné (`None`), jinak vyber podmnožinu z:
- "is_active": Uživatel se zajímá o aktivitu topení, zda je zapnuto / vypnuto
- "temperature": Uživatel se zajímá o nastavenou teplotu
- "current_temperature": Uživatel se zajíma o aktuální teplotu okolí"""
    )

@tool("get_temperature", args_schema=GetTemperatureArgs, return_direct=True)
def get_temperature(
    entity_id: str,
    states: Optional[list[str]] = None
) -> str:
    """
    Funkce, které slouží pro získávání informací o topných zařízaní jako jsou radiátory nebo topení.
    Topná zařízení jsou vždy označena identifikátorem `entity_id`, kde ke každému identifikátoru jsou přiřazeny očekávaná lidská označení.
    Volej tuto funkci vždy v případech, když přijde požadavek na zisk aktuálního stavu topného zařízení.
    """
    logger.debug(f"[CLIMATE {entity_id}] - Get state")

    current_state = ha_instance.get_state(entity_id)
    logger.debug(current_state)
    if isinstance(current_state, str):
        return f"Prvek {entity_id} není k dispozici."

    result = f"Current state [CLIMATE {entity_id}] -"
    if states is None or "is_active" in states:
        result += f" state: {current_state["attributes"]["current_temperature"] - current_state["attributes"]["temperature"] <= 0};"
    if states is None or "temperature" in states:
        result += f" target_temperature: {current_state["attributes"]["temperature"]};"
    if states is None or "current_temperature" in states:
        result += f" current_temperature: {current_state["attributes"]["current_temperature"]};"

    return result


class ActivateSceneArgs(BaseModel):
    scene_name: Literal[*list(SCENES.keys())] = Field( # type:ignore
        ...,
        description=f'Vyber název scény dle požadavku uživatele. Seznam názvů dostupných scén:{"\n- ".join(SCENES.keys())}'
    )

@tool("activate_scene", args_schema=ActivateSceneArgs, return_direct=True)
def activate_scene(
    scene_name: str
) -> str:
    """
    Funkce, které slouží pro aktivaci předdefinovaných scén. Každá scéna má své unikátní jméno dle `scene_name`.
    Volej tuto funkci vždy v případech, když přijde požadavek na změnu scény, např: aktivuj/nastav scénu/přepni ...
    """
    command = f"[SCANE {scene_name}]"
    logger.debug(command)
    scene = SCENES.get(scene_name)

    if not scene:
        return "Scéna neexistuje"

    actions = scene.get("actions", [])
    for action in actions:
        if action["entity_id"].startswith("light."):
            ha_instance.control_light(action.get("action"), action.get("entity_id"), action.get("brightness"), action.get("color"))
        elif action["entity_id"].startswith("climate."):
            ha_instance.set_temperature(action.get("entity_id"), action.get("temperature"))
    return f"Akce které byli vykonány: {actions}"