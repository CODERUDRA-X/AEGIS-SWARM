from caspian_sdk import CommClient
client = CommClient()

@client.on_message
def handle(message):
    print("MEDIA VALUE:", message.media)
    print("MEDIA TYPE:", type(message.media))
    message.reply("test received")

client.connect_telegram(bot_token="8890255710:AAEXaCDetxym_A5-Vflm5mgUVDRsJhJV1ks")
client.listen()