import logging
from re import S
from typing import Dict, Text, List, Any

from rasa_sdk import Tracker
from rasa_sdk.events import EventType, SlotSet
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk import Action

from aiohttp_requests import requests

from . import convert_metadata_to_content, url, get_natural_number, SLOT_STATE, SLOT_METADATA

logger = logging.getLogger(__name__)

class OrderAction(Action):
    def name(self) -> Text:
        return "action_order"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        session_id = tracker.sender_id

        intent = tracker.latest_message.get("intent")
        intent_name = intent.get("name")

        logger.debug(intent_name)

        if intent_name == 'order_anything':
            # TODO: order with is_exact = False
            return [
                SlotSet(SLOT_STATE, 'order_failed')
            ]

        entities = tracker.latest_message.get('entities', [])

        if len(entities) == 0:
            return [
                SlotSet(SLOT_STATE, 'order_failed')
            ]

        item_entities = list(filter(lambda e: e.get('entity', '').startswith('item'), entities))
        number_entities = list(filter(lambda e: e.get('entity', '').startswith('number'), entities))

        order_items = []

        logger.debug(item_entities)
        logger.debug(number_entities)

        if len(item_entities) == len(number_entities):
            items = [e.get('value', None) for e in item_entities]
            quantities = [e.get('value', None) for e in number_entities]
            order_items = zip(items, quantities)
        # else:
            # TODO: handle the case with mismatching quantities and items, failing for now
        else:
            return [
                SlotSet(SLOT_STATE, 'order_failed')
            ]

        logger.debug(order_items)

        events = []
        ordered_items = []

        for order_item in order_items:
            quantity = get_natural_number(order_item[1])
            response = await requests.post(url(f'/sessions/{session_id}/order'), json={
                "query": order_item[0],
                "quantity": quantity if quantity > 0 else 1,
                "is_exact": True,
            })

            result = await response.json()
            logger.debug(result)

            if SLOT_STATE in result and result[SLOT_STATE] is not None:
                events.append(SlotSet(SLOT_STATE, result[SLOT_STATE]))

            if SLOT_METADATA in result and result[SLOT_METADATA] is not None:
                ordered_items.extend(result[SLOT_METADATA].get('items', []))

        final_metadata = { "items": ordered_items }
        events.append(SlotSet(SLOT_METADATA, final_metadata))
        dispatcher.utter_message(template="utter_announce_ordered", content=convert_metadata_to_content(final_metadata))
        return events
