"""Self-contained synthetic restaurant for local demonstrations."""


def fixture():
    return {
        "users": [{"id": "demo_guest", "email": "guest@tablekeeper.test",
                   "password": "a lovely evening", "display_name": "Alex"}],
        "restaurants": [{
            "id": "the_orangery", "name": "The Orangery", "timezone": "Europe/London",
            "slot_minutes": 30, "reservation_duration_minutes": 90,
            "cancellation_cutoff_minutes": 60,
            "opening_hours": [{"weekday": day, "opens": "17:00", "closes": "23:00"}
                              for day in ("mon", "tue", "wed", "thu", "fri", "sat", "sun")],
            "tables": [{"id": "window", "label": "Window nook", "capacity": 2},
                       {"id": "garden", "label": "Garden table", "capacity": 2},
                       {"id": "round", "label": "The round table", "capacity": 4},
                       {"id": "alcove", "label": "Quiet alcove", "capacity": 6}],
            "combinable": [["window", "garden"], ["round", "alcove"]]
        }],
        "reservations": []
    }
