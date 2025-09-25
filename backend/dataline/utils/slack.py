import logging
import json
import requests

from dataline.config import config

logger = logging.getLogger(__name__)

async def slack_push(message: str):
    if not config.slack_url:
        return
    push_message = {"text": message}
    try:
        response = requests.post(
        config.slack_url,
        data=json.dumps(push_message),
        headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()
        logger.info(f"Message posted successfully, status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error posting message to Slack: {e}")