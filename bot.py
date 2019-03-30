import asyncio
import discord
import random
import bs4
import requests
from discord.ext.commands import Bot
from discord import Game
import json
import re

client = Bot(command_prefix='!')


TOKEN = 'Bot Token'

async def data_request(context, casual_rank, username_local):
    r = requests.get('https://r6.tracker.network/profile/pc/{}'.format(username_local.lower()))
    scrape = bs4.BeautifulSoup(r.text, 'html.parser')
    if r.status_code == 200:
        await webscrape(context, casual_rank, scrape)
    elif r.status_code == 404:
        print('>실패! 유저를 찾을수 없음!')
        await error_message_404(context, username_local)
    else:
        print('>실패! 유저를 찾을수 없음!')
        await error_message(context, username_local)

async def error_message(context, author):
    msg = '전적 검색 사이트에 연결하는데 오류가 발생하였습니다.'
    await client.send_message(context.message.channel, msg)

async def error_message_404(context, author):
    msg = (f'유저 {author.title()} 을 찾을 수 없습니다')
    await client.send_message(context.message.channel, msg)

async def webscrape(context, casual_rank, scrape):
    label, count, data, total = [[] for i in range(4)]
    cas_rank_gen = ['Empty', 'Overview', 'Overview2', 'Current Operation','전체', '캐쥬얼', '랭크']
    for element in scrape.select('.trn-scont__content'):
            for gen in element.select('.trn-card__content'):
                for stats_list in gen.select('.trn-defstats'):
                    for stat_label in stats_list.select('.trn-defstat__name'):
                        label.append(stat_label.get_text(strip=True))
                    for stat_count in stats_list.select('.trn-defstat__value'):
                        count.append(stat_count.get_text(strip=True))
                data.append(dict(zip(label, count)))

    total.append(dict(zip(cas_rank_gen, data)))

    for profile in scrape.select('.trn-profile-header__avatar'):
        for link in profile.find_all('img', src=True):
            profile_url = link['src']

    current_rank = '랭크가 없음'
    for rating in scrape.find_all(style='width: 50px; margin-right: 14px;'):
        for rank in rating.select('img'):
            current_rank = rank['title']

    for username in scrape.select('.trn-profile-header__name'):
        username_web = str(username.get_text())

    for mostplayed in scrape.select('.trn-defstat__value'):
        for source in mostplayed.find_all('img', src=True, limit=1):
            waifu = source['title'].title()

    requested_cas_rank = total[0][f'{casual_rank.title()}']
    if len(requested_cas_rank['Time Played']) == 0:
        requested_cas_rank['Time Played'] = 0

    if current_rank == "Not ranked yet.":
        current_rank = '랭크가 없음'

    await embed_creator(context, casual_rank, username_web, profile_url,requested_cas_rank['Time Played'], requested_cas_rank['Kills'],requested_cas_rank['Deaths'], requested_cas_rank['KD'], requested_cas_rank['Win %'], waifu, current_rank)

async def embed_creator(context, casual_rank, username, profile_url, time_played, kills, deaths, kd, wl, waifu, current_rank):
    embed=discord.Embed(title=f"R6S 전적 | {casual_rank.title()}", color=0x00ff00)
    embed.set_thumbnail(url=profile_url)
    embed.add_field(name="닉네임", value=username, inline=True)
    embed.add_field(name="플레이 시간", value=time_played, inline=True)
    embed.add_field(name="킬", value=kills, inline=True)
    embed.add_field(name="데스", value=deaths, inline=True)
    embed.add_field(name="K/D 비율", value=kd, inline=True)
    embed.add_field(name="승패 비율", value=wl, inline=True)
    embed.add_field(name="자주하는 오퍼", value=waifu, inline=True)
    embed.add_field(name="랭크", value=current_rank, inline=True)
    await client.send_message(context.message.channel, embed=embed)

async def r6sstatus(context):
    message = await client.send_message(context.message.channel, "🔎 정보를 가져오는중...")
    pcstatus = get_status('e3d5ea9e-50bd-43b7-88bf-39794f4e3d40')
    ps4status = get_status('fb4cc4c9-2063-461d-a1e8-84a7d36525fc')
    xboxonestatus = get_status('4008612d-3baf-49e4-957a-33066726a7bc')
    await client.delete_message(message)
    await r6sstatus_msg(context, pcstatus, ps4status, xboxonestatus)

async def r6sstatus_msg(context, pcstatus, ps4status, xboxonestatus):
    embed=discord.Embed(title=f"R6S Server 상태", color=0x00ff00)
    embed.set_thumbnail(url='https://r6sbot.zsxdc1379.com/assets/logo.png')
    embed.add_field(name="PC", value=pcstatus, inline=True)
    embed.add_field(name="PS4", value=ps4status, inline=True)
    embed.add_field(name="XBOXONE", value=xboxonestatus, inline=True)
    await client.send_message(context.message.channel, embed=embed)

def get_status(appid):
    api = 'https://game-status-api.ubisoft.com/v1/instances?appIds='
    data = ""
    url = api + appid
    resp = requests.get(url)
    if resp.status_code == 200:
        data = resp.text
        data = data.replace("[", "")
        data = data.replace("]", "")
        data = json.loads(data)
        data = data["Status"]
        return data

async def status_task():
    while True:
        await client.change_presence(game=Game(name="!r6sh : 정보&도움말"))
        await asyncio.sleep(10)
        await client.change_presence(game=Game(name="!r6sv : 레식서버상태확인"))
        await asyncio.sleep(10)

@client.command(pass_context=True)
async def r6s(context, nickname='', search_cas_rank='전체'):
    if nickname == '':
        nickname = str(context.message.author.nick)
        username_local = str(context.message.author.nick)
    else:
        username_local = nickname.lower()
    if search_cas_rank.lower() in {'캐쥬얼', '랭크', '전체'}:
        casual_rank = search_cas_rank.lower()
        message = await client.send_message(context.message.channel, "🔎 정보를 가져오는중...")
        await data_request(context, casual_rank, username_local)
        await client.delete_message(message)
    else:
        msg = '!r6s <닉네임> <`전체`, `캐쥬얼`, `랭크`>만 가능합니다.'
        await client.say(msg)

@client.command(pass_context=True)
async def r6sh():
    embed = discord.Embed(title="R6S 전적 봇 도움말", description="!r6sh : 봇 정보&도움말 보기 \n!r6s : 자신의 디코 서버닉네임의 전체 전적보기 \n!r6s <닉네임> : 전체 전적보기 \n!r6s <닉네임> 전체 : 전체 전적보기 \n!r6s <닉네임> 캐쥬얼 : 캐쥬얼 전적보기 \n!r6s <닉네임> 랭크 : 랭크 전적보기\n!r6sv : 레인보우 식스 시즈 서버 상태 확인 \n\nBot Site : https://r6sbot.zsxdc1379.com\n Invite : https://discordbots.org/bot/537957046964846602 \n\n\n제작자 : HardBlock \nWeb : https://zsxdc1379.com", color=0x00ff00)
    embed.set_footer(text="R6S Stats 봇을 사용중인 서버 : {}개 / 이용자수 : {}명".format(len(client.servers), len(set(client.get_all_members()))))
    await client.say(embed=embed)

@client.command(pass_context=True)
async def r6sv(context):
    await r6sstatus(context)

@client.event
async def on_ready():
    print('Logged in as:')
    print(client.user.name)
    print(client.user.id)
    print('------')
    client.loop.create_task(status_task())

client.remove_command("help")
client.run(TOKEN)
