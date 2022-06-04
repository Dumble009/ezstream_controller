import os
import signal
from venv import create
import websockets
import datetime
import asyncio
import subprocess
import atexit
import time

basePath = '/ezstream-1.0.2'


def createPlayLists(playlist):
    with open('/music/playlist.txt', 'w') as f:
        ids = playlist.split('\n')
        for id in ids:
            p = f'/mp3/{id}.mp3'
            log(f'requested id : {id}')
            if not os.path.exists(p):
                return False
            f.write(p)
    return True


def change():
    log('change')
    killStream()
    time.sleep(0.5)
    newStream()


def killStream():
    log('kill ezstream')
    if isEzstreamExist():
        with open('/ezstream-1.0.2/pid.txt', 'r') as f:
            pid = int(f.read())
            log("read pid")
            os.kill(pid, signal.SIGTERM)


def newStream(xmlFileName='ezstream.xml', pidFileName='pid.txt'):
    proc = subprocess.Popen(['ezstream', '-c', os.path.join(basePath, xmlFileName),
                            '-p', os.path.join(basePath, pidFileName)], stdout=subprocess.PIPE)
    # 少し待ってログインに失敗している(プロセスが死んでいる)場合は再度プロセスを起動する
    time.sleep(0.5)
    if not isEzstreamExist(pidFileName):
        log('reopen new stream')
        newStream(xmlFileName, pidFileName)
    


def isEzstreamExist(pidFileName='pid.txt'):
    return os.path.exists(os.path.join(basePath, pidFileName))

dt_now = datetime.datetime.now()
log_filename = f"/mp3/ezstream_controller-{dt_now.year}{dt_now.month}{dt_now.day}-{dt_now.hour}{dt_now.minute}{dt_now.second}.txt"
def log(msg):
    print(msg)
    with open(log_filename, 'w') as f:
        f.write(msg + "\n")


# finishedレスポンスを返し続けないようにするためのフラグ
isOnceFinishSent = True
FINISHED = 'finished'

async def accept(websocket):
    global isOnceFinishSent
    global FINISHED
    async for message in websocket:
        #print(message)
        log(message)
        sp = message.split(':')
        command = sp[0]
        playlist = sp[1]
        if command == 'play':
            isOnceFinishSent = False
            isExist = createPlayLists(playlist)
            if not isExist:
                await websocket.send(FINISHED)
            else:
                if isEzstreamExist():
                    change()
                else:
                    newStream()
        elif command == 'kill':
            isOnceFinishSent = True
            killStream()
        else:
            ret = 'alive'
            if (not isEzstreamExist()) and (not isOnceFinishSent):
                ret = FINISHED
                isOnceFinishSent = True
            #print(ret)
            log(ret)
            await websocket.send(ret)


async def main():
    atexit.register(killStream)
    async with websockets.serve(accept, "0.0.0.0", 1112):
        await asyncio.Future()

#print('server started')
log('server started')
newStream('noize.xml', 'noize_pid.txt')  # フォールバック用のノイズストリームを立てておく
asyncio.run(main())
