#!./.venv/bin/python
import argparse
import hashlib
import json
import re
import uuid
from pathlib import Path

class colors:
    HEADER = '\033[35m'
    OKBLUE = '\033[34m'
    OKCYAN = '\033[36m'
    OKGREEN = '\033[32m'
    OKYELLOW = '\033[33m'
    WARNING = '\033[33m'
    FAIL = '\033[31m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

MINECRAFT_FOLDER = Path("../")
PLAYER_ADVANCEMENTS_FOLDER_PREFIX = Path("world/players/advancements/")
USERCACHE = Path("usercache.json")
ADVANCEMENT_REPORTS_FOLDER_PREFIX = Path("reports/data/minecraft/advancement")

ADVANCEMENTS = [
    {"name": "Monsters Hunted", "id": "minecraft:adventure/kill_all_mobs", "filepath": "adventure/kill_all_mobs.json"},
    {"name": "Adventuring Time", "id": "minecraft:adventure/adventuring_time", "filepath": "adventure/adventuring_time.json"},
    {"name": "Hot Tourist Destinations", "id": "minecraft:nether/explore_nether", "filepath": "nether/explore_nether.json"},
    {"name": "Balanced Diet", "id": "minecraft:husbandry/balanced_diet", "filepath": "husbandry/balanced_diet.json"},
    {"name": "Two by Two", "id": "minecraft:husbandry/bred_all_animals", "filepath": "husbandry/bred_all_animals.json"},
    {"name": "A Complete Catalogue", "id": "minecraft:husbandry/complete_catalogue", "filepath": "husbandry/complete_catalogue.json"},
    {"name": "The Whole Pack", "id": "minecraft:husbandry/whole_pack", "filepath": "husbandry/whole_pack.json"},
]

def display_advancement_list(title, goals, data):
    count = 0

    print(colors.BOLD, f"\n\n--- {title} ---\n", colors.ENDC)

    for id, name in goals.items():
        completed = id in data.keys()
        if completed:
            count += 1
        print(colors.OKGREEN + "V " if completed else colors.FAIL + "  ", name, colors.ENDC)

    print(f"\n{colors.OKYELLOW if count >= len(goals) else colors.OKCYAN}Completed: {count}/{len(goals)}{colors.ENDC}")


def resolve_player_id(name):
    usercache = json.loads((MINECRAFT_FOLDER / USERCACHE).read_text())
    usermap = {e["uuid"]: e["name"] for e in usercache}
    
    # just in case the name happens to be the id
    if name in usermap.keys():
        return name
    
    userid = [u for u, n in usermap.items() if n == name]
    if len(userid) == 1:
        return userid[0]
    else:
        raise ValueError("Could not find unambiguous userid for '%s', values: %s" % (name, userid))

def offline_uuid(name: str):
    data = f"OfflinePlayer:{name}".encode("utf-8")
    digest = bytearray(hashlib.md5(data).digest())

    digest[6] = (digest[6] & 0x0f) | 0x30
    digest[8] = (digest[8] & 0x3f) | 0x80

    return uuid.UUID(bytes=bytes(digest))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('player_name', type=str, help="player name")
    parser.add_argument('-i', '--id', help="provide the player uuid instead of the name")

    args = parser.parse_args()

    player_id: str = args.player_name
    if not args.id:
        player_id = offline_uuid(player_id)

    try:
        player_data = json.loads((MINECRAFT_FOLDER / PLAYER_ADVANCEMENTS_FOLDER_PREFIX / f"{player_id}.json").read_text())
    except FileNotFoundError:
        player_data = None

    if not player_data:
        raise ValueError("Player not found: %s" % player_id)

    print(colors.BOLD, f"Select advancement details for player: {args.player_name} / {player_id}", colors.ENDC)

    for advancement in ADVANCEMENTS:
        try:
            with (MINECRAFT_FOLDER / ADVANCEMENT_REPORTS_FOLDER_PREFIX / advancement["filepath"]).open("r") as f:
                advancement_data = json.loads(f.read())
        except FileNotFoundError:
            raise RuntimeError(
                "The advancement map: `%s` not found.\n" \
                "You may need to generate the reports first with: \n" \
                "java -DbundlerMainClass=\"net.minecraft.data.Main\" -jar <SERVER_BINARY>.jar --output reports --all\n" \
                "" % advancement["id"]
            )

        goals = {
            _id: re.sub("^minecraft:", "", _id).replace("_", " ").title()
            for _id in advancement_data.get("criteria", {}).keys()
        }

        display_advancement_list(advancement["name"], goals, player_data.get(advancement["id"], {}).get("criteria", {}))

