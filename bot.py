import discord
import os
import requests
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont
font = TTFont('pacifico\Pacifico.ttf')



client = discord.Client(intents=discord.Intents.all())


@client.event
async def on_ready():
    print("I'am ready")


def get_game_price(app_id):
    url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if str(app_id) in data and "price_overview" in data[str(app_id)]:
            price_data = data[str(app_id)]["price_overview"]
            price = price_data.get("final_formatted", "Price not available")
            return price
    return "Price not available"


def get_games_on_sale():
    url = "https://store.steampowered.com/api/featuredcategories"
    params = {"cc": "US", "l": "english", "v": "1", "format": "json", "specials": "1"}
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        if "specials" in data:
            games = data["specials"]["items"]
            return games

    return []


def insert_period(org_string):
    # default position middle of org_string
    # if pos is None:
    pos = 2
    return org_string[:pos] + "." + org_string[pos:]
def convert_string_to_font(string, font_path):
    font = TTFont(font_path)
    glyph_names = font.getGlyphNames()

    converted_string = ""
    for char in string:
        if char in glyph_names:
            converted_string += char
        else:
            converted_string += " "  # If the character is not present in the font, replace it with a space

    return converted_string


def get_app_id(game_name):
    url = f"https://store.steampowered.com/api/storesearch/"
    params = {"cc": "US", "l": "english", "term": game_name, "format": "json"}
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        if "items" in data:
            if len(data["items"]) > 0:
                app_id = data["items"][0]["id"]
                return app_id

    return None


@client.event
async def on_message(message):
    # print(message.content)
    if message.author == client.user:
        return

    if message.content.startswith("!price"):
        games_on_sale = get_games_on_sale()
        if games_on_sale:
            for game in games_on_sale:
                on_sale_game = f"Game: {game['name']}\n"
                on_sale_game += f"Discount: {game['discount_percent']}%\n"
                on_sale_game += f"Price: ${game['final_price'] / 100:.2f}\n"
                on_sale_game += (
                    f"https://store.steampowered.com/app/{get_app_id(game['name'])}"
                )
                await message.channel.send(on_sale_game + "\n")
        else:
            await message.channel.send("No games on sale at the moment.")


client.run("MTExOTcyMzEwNTkyMTgxMDUyNQ.Glpkpk.JTzaQRq6bXNhXF0E93WNwuPbSNImv-_iDZQS8s")
