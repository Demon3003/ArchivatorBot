import requests,telebot
from requests import post
from telebot.types import Message
import zipfile, rarfile
import os
from datetime import datetime
from collections import defaultdict
from urllib.parse import quote


TOKEN=''
MAX_DOWNLOAD_SIZE=20971520
MAX_SEND_SIZE=52428800
API_URL=f'https://api.telegram.org/file/bot{TOKEN}/'
USER_DICT=defaultdict(list)
data_folder_path='python_bot/data/'
bot=telebot.TeleBot(TOKEN)


def send_files(message):
    for root, subfolders, files in os.walk(data_folder_path+str(message.from_user.id),topdown=False):                    
        for current_file in files:
            if current_file[0]!='.':
                files = {'document': (open(root+'/'+current_file, 'rb'))}            
                status = requests.post(f'https://api.telegram.org/bot{TOKEN}/sendDocument?chat_id=' + str(message.chat.id),files=files)
            os.remove(root+'/'+current_file)                           
        os.rmdir(root)

def download_files(file_info,user_id):     # file_ info is a tuple with 2 elements. First - file_path in the telegram and Second - file_name. 
    file = requests.get(API_URL+file_info[0]) #user_id - id of user in the telegram
    f_path = data_folder_path+user_id+'/'+file_info[1]
    with open(f_path, 'wb') as fd:
        for chunk in file.iter_content(chunk_size=128):
            fd.write(chunk)       

def zip_extract(file_info,user_id):
    my_zip=zipfile.ZipFile(data_folder_path+user_id+'/'+file_info)
    my_zip.extractall(data_folder_path+user_id)
    my_zip.close()
    if os.path.exists(data_folder_path+user_id+'/__MACOSX'):
        for root, folders, files in os.walk(data_folder_path+user_id+'/__MACOSX',topdown=False):
            for file in files:
                os.remove(root+'/'+file)
            os.rmdir(root)
    os.remove(data_folder_path+user_id+'/'+file_info)

def rar_extract(file_info,user_id):
    rf = rarfile.RarFile(data_folder_path+user_id+'/'+file_info)
    rf.extractall(data_folder_path+user_id)
    rf.close()
    os.remove(data_folder_path+user_id+'/'+file_info)



@bot.message_handler(commands=['start','cancel','extract_files','make_archive','stop'])
def command(message: Message):
    if message.text=='/start':
        bot.send_message(message.chat.id,"sss")
        
    elif message.text=='/help':
        bot.send_message(message.chat.id,'👍')
        
    elif message.text=='/make_archive' and USER_DICT[message.from_user.id]==[]:
        bot.send_message(message.chat.id,'Drop files as much as you need. When you finish send /stop to make archive or /cancel to cancel the process.')
        if USER_DICT[message.from_user.id]==[]:
            USER_DICT[message.from_user.id].append(0)
            
    elif message.text=='/extract_files' and USER_DICT[message.from_user.id]==[]:
        bot.send_message(message.chat.id,'Drop your archive.')
        if USER_DICT[message.from_user.id]==[]:
            USER_DICT[message.from_user.id].append(1)
            
    elif message.text=='/cancel' and USER_DICT[message.from_user.id]!=[]:
        USER_DICT.pop(message.from_user.id)
        
    elif message.text=='/stop' and USER_DICT[message.from_user.id]!=[]:
            if len(USER_DICT[message.from_user.id])>1:

                user_id=str(message.from_user.id)
                overflow=0
                if not os.path.exists(data_folder_path+user_id):
                        os.makedirs(data_folder_path+user_id)

                if USER_DICT[message.from_user.id][0]==0:

                    bot.send_message(message.chat.id,'Wait a minute. Your files are compressing.')
                    fantasy_zip = zipfile.ZipFile(data_folder_path+user_id+'/your_archive.zip', 'w')
                
                    for file_info in USER_DICT[message.from_user.id][1:]:
                        f_path = data_folder_path+user_id+'/'+file_info[1]

                        download_files(file_info,user_id)
                        
                        fantasy_zip.write(f_path,arcname=file_info[1], compress_type = zipfile.ZIP_DEFLATED)

                        if os.path.isfile(f_path):
                            os.remove(f_path)
                        
                        if os.path.getsize(data_folder_path+user_id+'/your_archive.zip') > MAX_SEND_SIZE:
                            bot.send_message(message.chat.id,"Bot can't send files over 50 MB")
                            overflow=1
                            break
                        
                    fantasy_zip.close()

                    if not overflow:
                        send_files(message)
                        bot.send_message(message.chat.id,'Process has finished')
  
                else:
                    file_info=USER_DICT[message.from_user.id][1]                 
                    f_path = data_folder_path+user_id+'/'+file_info[1]
                    download_files(file_info,user_id)
            
                    if zipfile.is_zipfile(f_path):
                        zip_extract(file_info[1],user_id)
                        send_files(message)
                    elif rarfile.is_rarfile(f_path):
                        rar_extract(file_info[1],user_id)
                        send_files(message)
                    else:
                        bot.send_message(message.chat.id,'Bot can extract files only from zip and rar archives.')

                    bot.send_message(message.chat.id,'Process has finished')

                USER_DICT.pop(message.from_user.id)
            else:
                bot.send_message(message.chat.id,'You did not send any file.')
                USER_DICT.pop(message.from_user.id)



@bot.message_handler(func=lambda message: True)
def answer(message:Message):
    if message.text.isupper():
        bot.reply_to(message,message.text+' lol ')
   

@bot.message_handler(content_types=['document'])
def rir(message:Message):        
    if USER_DICT[message.from_user.id]!=[]:

        if message.document.file_size <= MAX_DOWNLOAD_SIZE:
            USER_DICT[message.from_user.id].append((bot.get_file(message.document.file_id).file_path,message.document.file_name))
            print(USER_DICT)
        else:
            bot.send_message(message.chat.id,"Bot can't download files over 20 MB")
            USER_DICT.pop(message.from_user.id)


bot.polling() 
