import discord
import os
import requests
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont
import pymongo
import json
import pyshorteners
import config


import sys


client = discord.Client(intents=discord.Intents.all())
clientdb = pymongo.MongoClient("mongodb://localhost:27017/")
db = clientdb["steam"]
collection = db["collection"]


@client.event
async def on_ready():
    print("I'am ready")


def get_game_price(app_id):
    url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&cc=US"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        # print(
        #     data[str(app_id)]["data"]["price_overview"]["final_formatted"]
        #     + "in get_game_price"
        # )
        price_data = data[str(app_id)]["data"]["price_overview"]["final"]
        price = price_data / 100
        print(str(price))
        return price


def shorten_url(long_url):
    api_url = "https://api.tinyurl.com/dev/api-create"

    # Send a POST request to the API endpoint with the long URL
    response = requests.post(api_url, data={"url": long_url})

    if response.status_code == 200:
        # Extract the shortened URL from the response
        shortened_url = response.text
        return shortened_url
    else:
        # Handle error if the request was not successful
        print("Error occurred while shortening the URL.")
        print("Response Status Code:", response.status_code)
        print("Response Content:", response.text)
        return None


# to get the name then input that
def get_game_name(app_id):
    url = f"https://store.steampowered.com/api/appdetails?appids={(app_id)}&cc=US"
    params = {"cc": "US", "l": "english", "v": "1", "format": "json"}
    response = requests.get(url, params)

    if response.status_code == 200:
        data = response.json()
        game_name = data[str(app_id)]["data"]["name"]
        return game_name

    return None


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


def find_game_by_name(game_name):
    url = f"https://store.steampowered.com/api/storesearch/"
    params = {"cc": "US", "l": "english", "v": "1", "format": "json", "term": game_name}
    response = requests.get(url, params)

    if response.status_code == 200:
        data = response.json()
        if data["success"] and data["total"] > 0:
            game = data["items"][0]
            return game
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
                on_sale_game += f"https://store.steampowered.com/app/{get_app_id(game['name'])}&cc=US"
                await message.channel.send(on_sale_game + "\n")
        else:
            await message.channel.send("No games on sale at the moment.")

    if message.content.startswith("!name"):
        # Extract the user input by removing the "!name" prefix
        user_input = message.content[len("!name") :].strip()

        # Call the get_game_name function with the user input
        messageToUser = get_game_name(user_input)

        if messageToUser:
            await message.channel.send(messageToUser)
        else:
            print("The message content is empty.")

    if message.content.startswith("!track"):
        # Extract the user input by removing the "!track" prefix
        game_name = message.content[len("!track") :].strip()

        # Construct the API request URL
        base_url = "https://store.steampowered.com/api/storesearch"
        params = {"term": game_name, "cc": "us", "l": "en", "v": "1", "format": "json"}
        response = requests.get(base_url, params=params)

        if response.status_code == 200:
            data = response.json()

            if data:
                game_data = data["items"][0]
                game = {
                    "game_name": game_data["name"],
                    "game_app_id": game_data["id"],
                }

                if not game_data["price"]:
                    await message.channel.send("Bruh, this game is already free")
                else:
                    dividing_by_100_price = game_data["price"]["final"] / 100
                    game["game_price"] = "$" + str(dividing_by_100_price)

                existing_game = db.collection.find_one({"game_app_id": game_data["id"]})
                if existing_game is None:
                    db.collection.insert_one(game)
                    await message.channel.send("Game Added!")
                else:
                    await message.channel.send("Game is already added!")
            else:
                await message.channel.send("Invalid game ID or game not found.")
        else:
            await message.channel.send(
                "Failed to retrieve game information from Steam API."
            )

    if message.content.startswith("!search"):
        game_name = message.content[len("!search") :].strip()

        # Construct the API request URL
        base_url = "https://store.steampowered.com/api/storesearch"
        params = {"term": game_name, "cc": "us", "l": "en", "v": "1", "format": "json"}
        response = requests.get(base_url, params=params)

        if response.status_code == 200:
            data = response.json()

            if data:
                game_data = data["items"][0]
                game_name = game_data["name"]
                game_id = game_data["id"]
                game_price = game_data["price"]["final"]
                type_tiny = pyshorteners.Shortener()
                game_url = f"https://store.steampowered.com/app/{game_id}"
                short_url = type_tiny.tinyurl.short(game_url)
                formatted_price = "${:,.2f}".format(game_price / 100)
                embed = discord.Embed(
                    title="Steam Game Information",
                    description=f"Game Name: {game_name}\nGame Price: {formatted_price}\n Game Link: {(short_url)}",
                    color=discord.Color.green(),
                )
                embed.set_image(url=game_data["tiny_image"])
                await message.channel.send(embed=embed)
            else:
                await message.channel.send("Game not found.")
        else:
            await message.channel.send("Failed to retrieve game information.")

    if message.content.startswith("!pupdate"):
        message_to_user = ""
        print(get_game_price(294100))
        for doc in collection.find():
            api_game_price = get_game_price(doc["game_app_id"])
            print(f"{api_game_price}: API game price")
            print(f"{doc['game_price']}: Doc game price")
            float_game_price_db = doc["game_price"]
            price_without_symbol = float_game_price_db.replace("$", "")

            if float(api_game_price) < float(price_without_symbol):
                game_name = doc["game_name"]
                message_to_user += f"Found a lower price for {game_name}. It is now ${api_game_price}. It used to be {float_game_price_db}\n"
                formatted_price = "${:.2f}".format(api_game_price)
                collection.update_one(
                    {"_id": doc["_id"]}, {"$set": {"game_price": formatted_price}}
                )

        if message_to_user:
            embed = discord.Embed(
                title="Price updates",
                description=message_to_user,
                color=discord.Color.green(),
            )
            await message.channel.send(embed=embed)
        else:
            await message.channel.send("Sorry, just checked and no cheaper prices for your tracked games!")


client.run(config.API_KEY)

