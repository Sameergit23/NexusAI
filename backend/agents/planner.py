import asyncio
from geopy.geocoders import Nominatim
from sklearn.cluster import KMeans
from backend.db import log

# For testing
# async def log(*args):
#     pass


geolocator = Nominatim(user_agent="nexusai")


async def run(goal, deliveries, num_vehicles, run_id):
    valid_deliveries = []
    skipped = []

    for delivery in deliveries:
        try:
            if (
                delivery.get("lat") is None
                or delivery.get("lng") is None
            ):
                # Run sync geopy call in a thread so we don't block the event loop.
                location = await asyncio.to_thread(geolocator.geocode, delivery["address"])

                await asyncio.sleep(1)  # Nominatim rate limit (1 req/sec)

                if location:
                    delivery["lat"] = location.latitude
                    delivery["lng"] = location.longitude
                else:
                    skipped.append(delivery["id"])
                    continue

            valid_deliveries.append(delivery)

        except Exception as e:
            await log(
                run_id,
                "planner",
                f"Failed to process delivery {delivery['id']}: {str(e)}",
                "error"
            )
            skipped.append(delivery["id"])

    if len(valid_deliveries) == 0:
        return {
            "zones": [],
            "total_deliveries": 0,
            "num_vehicles": num_vehicles,
            "skipped": skipped
        }

    num_clusters = min(num_vehicles, len(valid_deliveries))

    coords = [
        [d["lat"], d["lng"]]
        for d in valid_deliveries
    ]

    kmeans = KMeans(
        n_clusters=num_clusters,
        random_state=42,
        n_init=10
    )

    labels = kmeans.fit_predict(coords)

    zones = [
        {
            "zone_id": f"zone_{i+1}",
            "vehicle_id": f"vehicle_{i+1}",
            "deliveries": []
        }
        for i in range(num_clusters)
    ]

    for delivery, label in zip(valid_deliveries, labels):
        zones[label]["deliveries"].append(
            {
                "id": delivery["id"],
                "address": delivery["address"],
                "lat": delivery["lat"],
                "lng": delivery["lng"]
            }
        )

    await log(
        run_id,
        "planner",
        "Deliveries clustered successfully",
        "info"
    )

    return {
        "zones": zones,
        "total_deliveries": len(valid_deliveries),
        "num_vehicles": num_vehicles,
        "skipped": skipped
    }

