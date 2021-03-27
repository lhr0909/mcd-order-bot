import logging
from typing import Dict, Text, List

from rasa_sdk import Tracker
from rasa_sdk.events import EventType, SlotSet
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk import Action

from aiohttp_requests import requests

from . import convert_metadata_to_content, url, SLOT_STATE, SLOT_METADATA

logger = logging.getLogger(__name__)


class CheckCartAction(Action):
    def name(self) -> Text:
        return "action_check_cart"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        session_id = tracker.sender_id

        events = []
        response = await requests.get(url(f'/sessions/{session_id}/cart'))

        result = await response.json()
        logger.debug(result)

        if SLOT_STATE in result and result[SLOT_STATE] is not None:
            events.append(SlotSet(SLOT_STATE, result[SLOT_STATE]))

        if SLOT_METADATA in result and result[SLOT_METADATA] is not None:
            events.append(SlotSet(SLOT_METADATA, result[SLOT_METADATA]))

        if result[SLOT_STATE] == 'cart_empty':
            dispatcher.utter_message(template="utter_cart_empty")
        else:
            dispatcher.utter_message(
                template="utter_cart_status", content=convert_metadata_to_content(result[SLOT_METADATA]))
            dispatcher.utter_message(text="，".join(
                result[SLOT_METADATA].get('cart_price_texts', [])))
            dispatcher.utter_message(
                template="utter_address_and_eta",
                eta="".join(result[SLOT_METADATA].get('deliver_time_texts', [])).replace("送达", ""),
                # FIXME: this is not robust enough for other cities
                address="".join(result[SLOT_METADATA].get('address_texts', []))[:6],
            )
        return events
