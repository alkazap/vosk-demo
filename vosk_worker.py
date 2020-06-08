#!/usr/bin/env python3

import argparse
import asyncio
import concurrent.futures
import json
import logging
import os
import pathlib
import sys
import time

import websockets
import websockets.exceptions
from vosk import KaldiRecognizer, Model

# Uncomment for better memory usage
#
# import gc
# gc.set_threshold(0)

# Enable loging if needed
#
logger = logging.getLogger('websockets')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

parser = argparse.ArgumentParser(
    description='WebSocket for Vosk api')
parser.add_argument('-u', '--url', dest='url', type=str,
                    default='ws://localhost:20005/decoder',
                    help='URL to which the WebSocket server will respond')
parser.add_argument('-m', '--model', dest='model', type=str,
                    default='/home/alena/data/models/vosk_model', help='Vosk model path')
parser.add_argument('-r', '--rate', dest='rate', type=float,
                    default=16000.0, help='Vosk sample rate')
args = parser.parse_args()

# Gpu part, uncomment if vosk-api has gpu support
#
# from vosk import GpuInit, GpuInstantiate
# GpuInit()
# def thread_init():
#     GpuInstantiate()
# pool = concurrent.futures.ThreadPoolExecutor(initializer=thread_init)

model = Model(args.model)
pool = concurrent.futures.ThreadPoolExecutor()
loop = asyncio.get_event_loop()


def process_chunk(rec, message):
    print('Message size = %d' % len(message))

    # if message == '{"eof" : 1}':
    if message == 'EOS':
        print('Message == %s' % message)
        recFinalResult = rec.FinalResult()
        print('rec.FinalResult = %s' % recFinalResult)
        return rec.FinalResult(), True
    else:
        recAcceptWaveform = rec.AcceptWaveform(message)
        if recAcceptWaveform:
            print('rec.AcceptWaveform(message) == %s' % recAcceptWaveform)
            recResult = rec.Result()
            print('rec.Result = %s' % recResult)
            return recResult, False
        else:
            recPartialResult = rec.PartialResult()
            print('rec.PartialResult = %s' % recPartialResult)
            return recPartialResult, False


async def recognize():
    recognizer = None
    word_list = None
    sample_rate = 16000.0
    while True:
        try:
            async with websockets.connect(args.url) as websocket:
                while True:
                    message = await websocket.recv()
                    # Load configuration if provided
                    if isinstance(message, str) and 'config' in message:
                        jobj = json.loads(message)['config']
                        if 'word_list' in jobj:
                            word_list = jobj['word_list']
                        if 'sample_rate' in jobj:
                            sample_rate = float(jobj['sample_rate'])
                        continue

                    # Create the recognizer, word list is temporary disabled since not every model supports it
                    if not recognizer:
                        if False and word_list:
                            recognizer = KaldiRecognizer(model, sample_rate, word_list)
                        else:
                            recognizer = KaldiRecognizer(model, sample_rate)

                    response, stop = await loop.run_in_executor(pool, process_chunk, recognizer, message)
                    await websocket.send(response)
                    if stop:
                        break
        except Exception as e:
            print(e, file=sys.stderr)
            pass
        time.sleep(1)

# start_server = websockets.serve(recognize, vosk_interface, vosk_port)
# loop.run_until_complete(start_server)

loop.run_until_complete(recognize())

try:
    loop.run_forever()
except KeyboardInterrupt:
    print("KeyboardInterrupt", file=sys.stderr)
    pass
finally:
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()
