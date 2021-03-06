import json
import requests
import os
import datetime
import urllib

from sys import exit
from colorama import Fore
from colorama import Style
from tqdm import tqdm

try:
    from win32_setctime import setctime             # for linux
except:
    pass
    
def downloadMemories(path):
    clear()

    with open(path, 'r') as f:
        content = json.load(f)
        media = content['Saved Media']

    success(f'Found {len(media)} files')
    media.reverse() # start from the oldest ones

    if not os.path.exists('memories'):
        try:
            os.mkdir('memories')
            success('Directory created\n')
        except Exception as e:
            error('Could not create directory', e)
            exit()

    already_downloaded = len(os.listdir('memories'))
    dw_counter = 0

    for data in tqdm(media, desc=f"{Fore.GREEN}[OK]{Style.RESET_ALL} Downloading: ", unit="file", ncols=70, bar_format="{desc}{n_fmt}/{total_fmt} {bar} {percentage:3.0f}%"):
        if((dw_counter := dw_counter+1) < already_downloaded) :   # skip already downloaded without last one in case it was corrupted
            continue
        
        date = data['Date']
        url = data['Download Link']
        filetype = data['Media Type']

        day = date.split(" ")[0]
        time = date.split(" ")[1].replace(':', '-')
        filename = f'memories/{day}_{time}'
        extension = '.mp4' if filetype == 'VIDEO' else '.jpg'

        req = requests.post(url, allow_redirects=True)
        response = req.text

        if response == '':
            print('\n\n')
            error('Could not download', filename[9:])
            warning('If this error persists request new data\n')
            continue

        downloaded = False
        if os.path.exists(filename+extension):
            dw_size = urllib.request.urlopen(response).info()['Content-Length']
            
            counter = 1
            filename_copy = filename

            while os.path.exists(filename+extension):
                local_size = str(os.path.getsize(filename+extension))
                if local_size == dw_size:
                    downloaded = True
                    break
                
                if counter == 1:
                    filename += '_01'
                    counter += 1
                    continue

                filename = filename_copy + f'_{counter:02}'
                counter += 1

        if not downloaded:
            file = requests.get(response)
            
            filename += extension
            with open(filename, 'wb') as f:
                f.write(file.content)
                
            timestamp = datetime.datetime.timestamp(datetime.datetime.strptime(day + '-' + time, "%Y-%m-%d-%H-%M-%S"))
            os.utime(filename, (timestamp, timestamp))
            if os.name=='nt':   ## only for windows overrite creation time
                setctime(filename, timestamp)

    print('\n\n----------------\n')
    success('Finished')
    return media

clear = lambda: os.system('cls' if os.name=='nt' else 'clear')

def success(str, as_input=False):
    output = f'{Fore.GREEN}[OK]{Style.RESET_ALL} {str}'
    if as_input:
        input(output)
    else:
        print(output)

def warning(str, as_input=False):
    output = f'{Fore.YELLOW}[!]{Style.RESET_ALL} {str}'
    if as_input:
        input(output)
    else:
        print(output)

def error(str, e='', as_input=False):
    output = f'{Fore.RED}[ERROR]{Style.RESET_ALL} {str}: {e}'
    if as_input:
        input(output)
    else:
        print(output)
        
def save_duplicates(media):
    # get all dates from json
    list_of_dates = []
    for obj in media:
        list_of_dates.append(obj['Date'])

    # find all duplicates
    seen = set()
    seen_add = seen.add
    duplicates = list(set(x for x in list_of_dates if x in seen or seen_add(x)))
    
    return duplicates

try:        
    path = 'memories_history.json' if not os.path.exists('json') else 'json/memories_history.json'
    media = downloadMemories(path)
    duplicates = save_duplicates(media)
    dup_len = len(duplicates)
    
    if dup_len > 0:
        warning(f'{dup_len} duplicates detected, saving to file ...')
        with open('duplicates.txt', 'w+') as f:
            for d in duplicates:
                f.write(d + '\n')

    input()
    exit()
except Exception as e:
    error('Exception occured', e, True)