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
            f.write(f'/mp3/{id}.mp3')


def change():
    print('change')
    killStream()
    time.sleep(0.5)
    newStream()


def killStream():
    print('kill ezstream')
    if isEzstreamExist():
        with open('/ezstream-1.0.2/pid.txt', 'r') as f:
            pid = int(f.read())
            print("read pid")
            os.kill(pid, signal.SIGTERM)


def newStream(xmlFileName='ezstream.xml', pidFileName='pid.txt'):
    proc = subprocess.Popen(['ezstream', '-c', os.path.join(basePath, xmlFileName),
                            '-p', os.path.join(basePath, pidFileName)], stdout=subprocess.PIPE)

    # 少し待ってログインに失敗している(プロセスが死んでいる)場合は再度プロセスを起動する
    time.sleep(0.1)
    if not isEzstreamExist(pidFileName):
        newStream(xmlFileName, pidFileName)


def isEzstreamExist(pidFileName='pid.txt'):
    return os.path.exists(os.path.join(basePath, pidFileName))


# finishedレスポンスを返し続けないようにするためのフラグ
isOnceFinishSent = True


async def accept(websocket):
    global isOnceFinishSent
    async for message in websocket:
        print(message)
        sp = message.split(':')
        command = sp[0]
        playlist = sp[1]
        if command == 'play':
            isOnceFinishSent = False
            createPlayLists(playlist)
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
                ret = 'finished'
                isOnceFinishSent = True
            print(ret)
            await websocket.send(ret)


async def main():
    atexit.register(killStream)
    async with websockets.serve(accept, "0.0.0.0", 1112):
        await asyncio.Future()

print('server started')
newStream('noize.xml', 'noize_pid.txt')  # フォールバック用のノイズストリームを立てておく
asyncio.run(main())
