import json
import logging
import random

import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    id = req.route_params.get("id")
    logging.info(f"Requesting crowdedness for restaurant: {id}")

    total_capacity = random.randint(10, 20)
    crowdedness = random.random()
    current_visitors = int(total_capacity * crowdedness)
    days_visitors = random.randint(4 * current_visitors, 12 * current_visitors)

    return func.HttpResponse(
        body=json.dumps(
            {
                "crowdedness": crowdedness,
                "last_hour": current_visitors,
                "last_day": days_visitors,
            }
        )
    )
