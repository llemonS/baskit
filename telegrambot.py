import subprocess
import os
import time
import telepot
import sys
from io import StringIO

__stdout = sys.stdout
sys.stdout = StringIO()
#         PREREQUISITES
#1) first things first, place the testbot.py in the same directory of the file baskit.conf.
#2) make your bot on telegram talking with botfather
TOKEN = 'INSERTYOURBOTTOKENHERE'
#2.1)if you dont know your id, run this code only with token and type /myid to your bot, it will response your ID and username.
adminid = "YOURTELEGRAMID"
adminidusername = "YOURTELEGRAMUSERNAME"
#3)magic happens down below.
bot = telepot.Bot(TOKEN)
bot.setWebhook()
username = '@' + bot.getMe()['username']
#find server IP
ip = os.popen("curl ipinfo.io/ip").read()[:-1]+(":25565")

# sending server address to my telegram 
bot.sendMessage(adminid, "Bot Started!\n"+ ip)
# to do a list of registered players to send this server address
def handle(msg):
    text = msg['text'].strip().replace(username, '')
    chat = msg['chat']['id']
    r = ''
    if text == "/myid":
       bot.sendMessage(chat, "Your ID: "+ str(chat) +"\nYour Username: "+ str(msg['chat']['username']))
    if msg['from'].get('username') != adminidusername:
    	#commands available to users != from bot admin.
        bot.sendMessage(adminid, msg)
        if text == "/myid":
         bot.sendMessage(chat, "Your ID: "+ str(chat) +"\nYour Username: "+ str(msg['chat']['username']))
        if text == "/players":
         r = subprocess.Popen(["sudo","/usr/local/bin/baskit","players"], stdout=subprocess.PIPE)
         bot.sendMessage(chat, r.stdout.read())  
         r.stdout.flush()
         return
    
    if text == '/restart':
        bot.sendMessage(adminid, "Restarting! "+ ip)
        sleep(1)
        r = os.popen("sudo reboot")
    elif text == '/start':
        bot.sendMessage(adminid, "Starting Server! : " + ip)
        r = subprocess.Popen(["sudo","/usr/local/bin/baskit","start"],stdout=subprocess.PIPE)
        bot.sendMessage(adminid, r.stdout.read())
        r.stdout.flush()
        
    elif text == '/players':
        r = subprocess.Popen(["sudo","/usr/local/bin/baskit","players"],stdout=subprocess.PIPE)
        bot.sendMessage(adminid, stdout.read())
        r.stdout.flush()
    elif text == "/stop":
        bot.sendMessage(adminid, "desligando o Servidor!")
        r = subprocess.Popen(["sudo","/usr/local/bin/baskit","stop"], stdout=subprocess.PIPE)
        bot.sendMessage(adminid, stdout.read())
        r.stdout.flush()
    elif text == "/help":
        r = " /start - start baskit server \n /players - show online players \n /stop - stop server \n /restart - reboot pc."
        bot.sendMessage(adminid, r)
    #to do a command to talk with players on server using "baskit cmd say" and getting players live response throught telegram.
    #looks similar to "baskit players" but first i need to learn regex and how to search the right stuff in latest.log file
bot.message_loop(handle)


while 1:
    time.sleep(1000)
#thats it my dudes. As you guys can see, Im a begginer on python. 
