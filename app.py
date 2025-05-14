from dotenv import load_dotenv
load_dotenv()

import os
import asyncio

from uuid import uuid4

from langgraph.checkpoint.memory import MemorySaver

from langchain_core.messages import HumanMessage

from backend.dialog import SpeechCloudWS, Dialog
from backend.agent import Agent
from backend.app_schemas import ChainInput
from backend.graph import plot_graph
from backend.utils import get_logger, load_scenes, save_scene, activate_scene, save_json, load_or_create_json
from backend.tools import ha_instance


logger = get_logger("hds")


class HDSDialog(Dialog):
    agent = None

    async def main(self):
        if self.agent is None:
            logger.info("HDS Dialog init")
            self.ttsEnabled=False
            self.stt= False
            self.agent = Agent()
            self.memory = MemorySaver()
            self.chain = self.agent.build_graph(checkpointer=self.memory)

            # _ = plot_graph(graph=self.chain, save_path="./graph.png")
        else:
            logger.info("HDS Dialog was runnig")
        
        self.thread_id = str(uuid4())

        await self.run_dialog()


    async def run_dialog(self):
        # Začínáme syntézou. Metody *_and_wait jsou blokující, náš skript tedy 
        # bude pokračovat až po skončení syntetizované promluvy.
        # V tuto chvíli ještě není spuštěno rozpoznávání řeči.
        # await self.synthesize_and_wait(text="Já jsem dialogový manažer pro semestrální práci z předmětu hlasové dialogové systémy. Co si přejete")
        if ha_instance.is_alive():
            await self.send_message({"type": "init", "data": ha_instance.get_all_entities()})
        else:
            await self.send_message({"type": "HA-error", "data":"HA-error"})

        message = "Co si přejete"
        await self.send_message({"type": "chat-dm", "data": message}) 
        if self.ttsEnabled:
            await self.synthesize_and_wait(message)
        while True:
            await asyncio.sleep(1)
            while self.stt:
                await self.send_message({"type": "mic_on", "data": None}) 
                result = await self.recognize_and_wait_for_asr_result(timeout=5.)
                await self.send_message({"type": "mic_off", "data": None})

                if result is None:
                    user_words = None
                else:
                    user_words = result["word_1best"]

                if user_words is None:
                    message = "Nic jste neřekli"
                    await self.send_message({"type": "chat-dm", "data": message}) 
                    if self.ttsEnabled:
                        await self.synthesize_and_wait(message)
                elif "konec" in user_words:
                    message = "----"
                    await self.send_message({"type": "chat-dm", "data": message}) 
                    if self.ttsEnabled:
                        await self.synthesize_and_wait(message)
                    self.thread_id = str(uuid4())
                else:
                    logger.debug(f"user_words: {user_words}")
                    await self.handle_input(user_words)

    async def handle_input(self,user_words):
        await self.send_message({"type": "thinking", "data": "thinking"}) 
        output = await self.chain.ainvoke(
            input=ChainInput(
                messages=[HumanMessage(content=user_words)]
            ),
            config={
                "configurable": {
                    "thread_id": self.thread_id
                }
            }
        )
        response = output["messages"][-1].content
        await self.send_message({"type": "state_update","data": ha_instance.get_all_entities()})
        await self.send_message({"type": "chat-dm", "data": response}) 
        if self.ttsEnabled:
            await self.synthesize_and_wait(response)
        
    def on_receive_message(self, data):
        logger.debug("Received message:\n%s", str(data))

        if not isinstance(data, dict) or "type" not in data:
            return

        msg_type = data["type"]

        handlers = {
            "toggle_light": lambda: (ha_instance.toggle_light(data["entity_id"])),
            "set_light_color": lambda: (ha_instance.set_light_color(data["entity_id"],data["color"])),
            "set_brightness": lambda:(ha_instance.control_light("on", data["entity_id"],data["brightness"])),
            "set_temperature": lambda: ha_instance.set_temperature(data["entity_id"], data["temperature"]),
            "control_light": (lambda: ha_instance.control_light(data.get("action", "on"), data["entity_id"], data.get("brightness"), data.get("color"))),
            "get_temperature": lambda: asyncio.create_task(
                self.send_message({"type": "temperature_update",
                    "data": {"elementId": data["elementId"],"current_temperature": ha_instance.get_temperature(data["entity_id"])}})),
            "chat_input": lambda: asyncio.create_task( self.handle_input(data["data"])),
            "toggleTTS": lambda: setattr(self, "ttsEnabled", not self.ttsEnabled),
            "toggleRec": lambda: setattr(self, "stt", not self.stt),
             "settings": lambda: asyncio.create_task(
                self.send_message({"type": "settings", "data": load_or_create_json(os.getenv("FRIENDLY_NAMES"))})),
            "set_friendly_names": lambda: (
                save_json(os.getenv("FRIENDLY_NAMES"), data["data"]),
                asyncio.create_task(self.send_message({"type": "chat-dm",  "data": f"Friendly names byla uložena."}))),
            "get_scenes": lambda: asyncio.create_task(
                self.send_message({"type": "scene_list", "data": list(load_scenes().keys())})),
            "save_scene": lambda: (
                save_scene(data["name"], data["actions"]),
                asyncio.create_task(self.send_message({"type": "chat-dm","data": f"Scéna '{data['name']}' byla uložena."})),
                asyncio.create_task(self.send_message({"type": "scene_list", "data": list(load_scenes().keys())}))),
            "activate_scene": lambda: asyncio.create_task(activate_scene(self,ha_instance,data["scene"])),
            "get_light_states": lambda: asyncio.create_task( self.send_message({"type": "state_update","data": ha_instance.get_all_entities()})),
        }

        handler = handlers.get(msg_type)
        if handler:
            handler()
        else:
            self.logger.warning("Unknown message type received: %s", msg_type)


if __name__ == "__main__":
    print("http://127.0.0.1:8888/static/index.html")
    SpeechCloudWS.run(HDSDialog, address="0.0.0.0", port=8888, static_path="./static")