import discord
from discord.ext import commands, tasks
import os
import requests
import hashlib
from pymongo import MongoClient
from pymongo.errors import PyMongoError

assert 'BOT_TOKEN' in os.environ, 'BOT_TOKEN is not set in the environment variables.'
assert 'DB_URI' in os.environ, 'DB_URI is not set in the environment variables.'
assert 'DB_NAME' in os.environ, 'DB_NAME is not set in the environment variables.'

TOKEN = os.environ['BOT_TOKEN']
DB_URI = os.environ['DB_URI']
DB_NAME = os.environ['DB_NAME']

db_client = MongoClient(DB_URI)

db = db_client[DB_NAME]

#table with (id, url, content_hash)
db_urls = db['urls'] 

#table with (user_id, url_id)
db_follows = db['follows']

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
bot.remove_command('help')

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
    
def url_exists_in_db(url):
    return db_urls.find_one({'url': url}) is not None

def user_follows_page(user_id, url_id):
    return db_follows.find_one({'user_id': user_id, 'url_id': url_id}) is not None

async def alert_users(url, url_id):
    for row in db_follows.find({'url_id': url_id}):
        user_id = row['user_id']
        user = await bot.fetch_user(user_id)
        await user.send(f'Webpage {url} has been updated!')

@bot.command()
async def follow(ctx):
    try:
        url = ctx.message.content.split()[1]
    except:
        await ctx.send(f'{ctx.author.mention} Command !follow needs one argument!')
        return

    if not is_valid_url(url):
        await ctx.send(f'{ctx.author.mention} The url you provided is not valid!')
        return

    content = fetch_webpage_content(url)

    with db_client.start_session() as session:
        with session.start_transaction():
            try:
                if not url_exists_in_db(url):
                    url_id = db_urls.insert_one({'url' : url, 'content_hash': content}).inserted_id
                else:
                    url_id = db_urls.find_one({'url': url})['_id']

                if user_follows_page(ctx.author.id, url_id):
                    await ctx.send(f'{ctx.author.mention} You are already following that page!')
                    return
                else:
                    db_follows.insert_one({'user_id': ctx.author.id, 'url_id': url_id})

            except PyMongoError as e:
                print(f'Transaction aborted due to error: {e}')
                return

    await ctx.send(f'{ctx.author.mention} I have started following the webpage!')

@bot.command()
async def unfollow(ctx):
    try:
        url = ctx.message.content.split()[1]
    except:
        await ctx.send(f'{ctx.author.mention} Command !unfollow needs one argument!')
        return
    
    if not is_valid_url(url):
        await ctx.send(f'{ctx.author.mention} The url you provided is not valid!')
        return
    
    if not url_exists_in_db(url):
        await ctx.send(f'{ctx.author.mention} You aren\'t even following this page!')
        return
    else:
        url_id = db_urls.find_one({'url': url})['_id']
    
    with db_client.start_session() as session:
        with session.start_transaction():
            try:
                if user_follows_page(ctx.author.id, url):
                    await ctx.send(f'{ctx.author.mention} You aren\'t even following this page!')
                    return
                else:
                    db_follows.delete_one({'user_id': ctx.author.id, 'url_id': url_id}, session=session)

                if db_follows.count_documents({'url': url}) == 0:
                    db_urls.delete_one({'url': url}, session=session)

            except PyMongoError as e:
                print(f'Transaction aborted due to error: {e}')
                return
    
    await ctx.send(f'{ctx.author.mention} Webpage successfully unfollowed!')

@bot.command()
async def pages(ctx):
    message = ''
    for row in db_follows.find({'user_id': ctx.author.id}):
        message +='\n' + db_urls.find_one({'_id': row['url_id']})['url']

    if message == '':
        await ctx.send(f'{ctx.author.mention} You are not following any webpages')
    else:
        await ctx.send(f'{ctx.author.mention} You are following these webpages: {message}')

@bot.command()
async def help(ctx):
    await ctx.send(f"Hi {ctx.author.mention}, I am a bot that keeps track of when static content on a webpage changes.\n"
                   "My current functionalities are:\n"
                   "```\n"
                   "!help -> provides this message\n"
                   "!follow url -> starts following the provided webpage and lets you know when it changes\n"
                   "!unfollow url -> stops following the provided webpage\n"
                   "!pages -> gives you a list of webpages you are currently following\n"
                   "```\n")

@tasks.loop(minutes=0.1)
async def check_for_updates():
    for row in db_urls.find():
        content = fetch_webpage_content(row['url'])
        if content != row['content_hash']:
            db_urls.update_one({'url': row['url']}, {'$set': {'content_hash': content}})
            await alert_users(row['url'], row['_id'])

@bot.command()
async def hello(ctx):
    await ctx.send(f'Hello {ctx.author.mention}!')

bot.run(TOKEN)
