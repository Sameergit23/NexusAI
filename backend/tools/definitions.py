ALL_TOOLS = [
    {
        "name": "plan_tasks",
        "description": (
            "Analyse a delivery goal and produce a structured delivery plan. "
            "Groups delivery addresses into geographic zones, assigns a vehicle to each zone, "
            "and returns an ordered list of tasks for the Route Optimizer agent."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "goal": {
                    "type": "string",
                    "description": "The plain-English delivery goal provided by the user.",
                },
                "deliveries": {
                    "type": "array",
                    "description": "List of delivery addresses to be planned.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string", "description": "Unique delivery ID."},
                            "address": {"type": "string", "description": "Full delivery address."},
                            "lat": {"type": "number", "description": "Latitude of delivery point."},
                            "lng": {"type": "number", "description": "Longitude of delivery point."},
                        },
                        "required": ["id", "address"],
                    },
                },
                "num_vehicles": {
                    "type": "integer",
                    "description": "Number of vehicles available for this run.",
                },
            },
            "required": ["goal", "deliveries", "num_vehicles"],
        },
    },
    {
        "name": "optimise_routes",
        "description": (
            "Take a delivery plan produced by the Planner and compute the optimal route for each vehicle. "
            "Returns per-vehicle ordered waypoint lists and estimated total distance in kilometres."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "run_id": {
                    "type": "string",
                    "description": "Unique identifier for the current delivery run.",
                },
                "zones": {
                    "type": "array",
                    "description": "List of zones, each containing a vehicle ID and its assigned deliveries.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "zone_id": {"type": "string"},
                            "vehicle_id": {"type": "string"},
                            "deliveries": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "string"},
                                        "address": {"type": "string"},
                                        "lat": {"type": "number"},
                                        "lng": {"type": "number"},
                                    },
                                    "required": ["id", "address"],
                                },
                            },
                        },
                        "required": ["zone_id", "vehicle_id", "deliveries"],
                    },
                },
            },
            "required": ["run_id", "zones"],
        },
    },
    {
        "name": "send_notifications",
        "description": (
            "Send email notifications to customers or fleet managers about delivery status. "
            "Uses the Resend API. Returns a list of message IDs for each email dispatched."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "run_id": {
                    "type": "string",
                    "description": "Unique identifier for the current delivery run.",
                },
                "notifications": {
                    "type": "array",
                    "description": "List of notifications to send.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "to": {"type": "string", "description": "Recipient email address."},
                            "subject": {"type": "string", "description": "Email subject line."},
                            "body": {"type": "string", "description": "Plain-text email body."},
                            "delivery_id": {
                                "type": "string",
                                "description": "Delivery ID this notification is about (optional).",
                            },
                        },
                        "required": ["to", "subject", "body"],
                    },
                },
            },
            "required": ["run_id", "notifications"],
        },
    },
    {
        "name": "generate_report",
        "description": (
            "Compute analytics for a completed delivery run and persist them to Supabase. "
            "Calculates distance saved vs naive routing, CO₂ avoided, cost saved in INR, "
            "time saved, on-time delivery rate, and trees-equivalent metric."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "run_id": {
                    "type": "string",
                    "description": "Unique identifier for the completed delivery run.",
                },
                "naive_km": {
                    "type": "number",
                    "description": "Total kilometres if each delivery had been routed naively (point-to-point).",
                },
                "optimised_km": {
                    "type": "number",
                    "description": "Actual total kilometres after route optimisation.",
                },
                "deliveries_total": {
                    "type": "integer",
                    "description": "Total number of deliveries attempted.",
                },
                "deliveries_on_time": {
                    "type": "integer",
                    "description": "Number of deliveries completed within the promised time window.",
                },
            },
            "required": [
                "run_id",
                "naive_km",
                "optimised_km",
                "deliveries_total",
                "deliveries_on_time",
            ],
        },
    },
]
