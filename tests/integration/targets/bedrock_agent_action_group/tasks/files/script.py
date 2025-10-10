# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import datetime
import json


def lambda_handler(event, context):
    now = datetime.datetime.utcnow()

    response = {"date": now.strftime("%Y-%m-%d"), "time": now.strftime("%H:%M:%S"), "timezone": "UTC"}

    # Wrap response as expected by Bedrock agent
    response_body = {"application/json": {"body": json.dumps(response)}}

    action_response = {
        "actionGroup": event.get("actionGroup", "default"),
        "apiPath": event.get("apiPath", "/"),
        "httpMethod": event.get("httpMethod", "GET"),
        "httpStatusCode": 200,
        "responseBody": response_body,
    }

    return {
        "messageVersion": "1.0",
        "response": action_response,
        "sessionAttributes": event.get("sessionAttributes", {}),
        "promptSessionAttributes": event.get("promptSessionAttributes", {}),
    }
