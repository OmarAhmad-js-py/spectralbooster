import random

def generate_message():
    message_templates = [
        "gg",
        "lol",
        "nice play",
        "hello from {city}",
        "back from work gl everyone",
        "o7",
        "pog",
        "that was insane",
        "clip that",
        "first time here, this is cool",
        "anyone else here from {game}?",
        "lurking for now, great stream"
    ]

    cities = ["NYC", "LA", "London", "Berlin", "Tokyo", "Toronto", "Sydney"]
    popular_games = ["Valorant", "League", "CS2", "Apex", "Minecraft", "Fortnite"]

    template = random.choice(message_templates)
    if "{city}" in template:
        message = template.format(city=random.choice(cities))
    elif "{game}" in template:
        message = template.format(game=random.choice(popular_games))
    else:
        message = template 
 
    return message