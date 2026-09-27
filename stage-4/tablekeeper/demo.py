"""Self-contained synthetic restaurant for local demonstrations."""


def fixture():
    return {
        "users": [{"id": "demo_guest", "email": "guest@tablekeeper.test",
                   "password": "a lovely evening", "display_name": "Alex"},
                  {"id": "demo_manager", "email": "manager@tablekeeper.test",
                   "password": "a thoughtful service", "display_name": "Sam"}],
        "restaurants": [{
            "id": "the_orangery", "name": "The Orangery", "timezone": "Europe/London",
            "manager_user_ids": ["demo_manager"],
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
        "reservations": [
            {"id": "demo_evening", "reference": "EVENING1", "user_id": "demo_guest",
             "restaurant_id": "the_orangery", "table_id": "window",
             "starts_at_local": "2035-06-14T19:00", "party_size": 2},
            {"id": "demo_friends", "reference": "FRIENDS1", "user_id": "demo_guest",
             "restaurant_id": "the_orangery", "table_id": "round",
             "starts_at_local": "2035-06-14T19:00", "party_size": 4},
            {"id": "demo_later", "reference": "LATER001", "user_id": "demo_guest",
             "restaurant_id": "the_orangery", "table_id": "garden",
             "starts_at_local": "2035-06-14T20:30", "party_size": 2}
        ]
    }
