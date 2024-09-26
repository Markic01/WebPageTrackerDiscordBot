import discord
from discord.ext import commands, tasks
import os
import requests
import hashlib

assert 'BOT_TOKEN' in os.environ, 'BOT_TOKEN is not set in the environment variables.'
TOKEN = os.environ['BOT_TOKEN']
user_pages = []
web_pages = []

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot connected as {bot.user}')
    check_for_updates.start()

def is_valid_url(url):
    try:
        requests.get(url)
        return True
    except:
        return False
    
def fetch_webpage_content(url):
    try:
        response = requests.get(url)
        hash_object = hashlib.sha256(response.text.encode('utf-8'))
        return hash_object.hexdigest()
    except:
        return None

def insert_user_pages(user_id, url):
    for i in range(len(user_pages)):
        if user_pages[i]['user_id'] == user_id:
            if url in user_pages[i]['urls']:
                return False
            else:
                user_pages[i]['urls'].append(url)
                return True
    
    user_pages.append({'user_id': user_id, 'urls': [url]})
    return True

def insert_web_pages(url):
    for page in web_pages:
        if page['url'] == url:
            return
    
    content = fetch_webpage_content(url)
    web_pages.append({'url': url, 'content': content})

async def alert_users(url):
    for user_page in user_pages:
        if url in user_page['urls']:
            user = await bot.fetch_user(user_page['user_id'])
            await user.send('webpage ' + url + ' has been updated!')

@bot.command()
async def follow(ctx):
    user_id = ctx.author.id
    try:
        url = ctx.message.content.split()[1]
    except:
        await ctx.send('Command !follow needs one argument!')
        return

    if not is_valid_url(url):
        await ctx.send('The url you provided is not valid!')
        return

    if not insert_user_pages(user_id, url):
        await ctx.send('You already follow this page!')
        return
    
    insert_web_pages(url)

    await ctx.send(f'{ctx.author.mention} I have started following the webpage!')

@bot.command()
async def unfollow(ctx):
    user_id = ctx.author.id
    try:
        url = ctx.message.content.split()[1]
    except:
        await ctx.send('Command !unfollow needs one argument!')
        return
    
    other_follows_url = False
    for i in range(len(user_pages)):
        if user_pages[i]['user_id'] == user_id:
            if url not in user_pages[i]['urls']:
                await ctx.send(f'{ctx.author.mention} you don\'t even follow that page in the first place!')
                return
            else:
                user_pages[i]['urls'].remove(url)
        else:
            if url in user_pages[i]['urls']:
                other_follows_url = True
    
    if not other_follows_url:
        for i, web_page in enumerate(web_pages):
            if web_page['url'] == url:
                web_pages.remove(web_page)
                break
    
    await ctx.send(f'{ctx.author.mention} webpage successfully unfollowed!')

@tasks.loop(minutes=0.1)
async def check_for_updates():
    for i, web_page in enumerate(web_pages):
        try:
            new_content = fetch_webpage_content(web_page['url'])
            if new_content != web_page['content']:
                web_pages[i]['content'] = new_content
                await alert_users(web_page['url'])
        except:
            continue

@bot.command()
async def hello(ctx):
    await ctx.send(f'Hello {ctx.author.mention}!')

bot.run(TOKEN)
