from multiprocessing import Process, Queue, active_children
from datetime import datetime
from math import ceil
import os
from time import sleep
from textblob import TextBlob
import langdetect
from pymongo import MongoClient
import requests
import json
import credentials
import unittest
from constants import *


def stream_in(q1, q2, q3):
    if DEBUG_STREAM == True:
        print("\nstream_in PID:", os.getpid())

    api_URL = credentials.api_URL
    headers = credentials.headers

    while True:
        try:
            with requests.get(api_URL, headers=headers, stream = True) as f:
                partial_ms = ''
                if f.status_code == 200:
                    for line in f:
                        if DEBUG_STREAM:
                            print("STREAM LIME: ", line)
                        line = line.decode("utf-8")
                        # It ensures that we split the text only if it's between our desired token(s)
                        partial_ms += line
                        splits = partial_ms.split(NEW_MESSAGE_TOKEN)
                        partial_ms = splits[0]
                        if len(splits)==2:
                            new_stream_message(partial_ms, q1, q3)
                            partial_ms = splits[1]
                        elif len(splits)>2:
                            new_stream_message(partial_ms, q1, q3)
                            for ms in splits[1:-1]:
                                new_stream_message(ms, q1, q3)
                            partial_ms = splits[-1]

        except Exception as e:
            if DEBUG_STREAM:
                print(e)

        if DEBUG_STREAM:
            print("\nStream api connection losed. Reconecting...")
            t = datetime.utcnow()
            d = {'t0': t,
                 'message': WALLY_MESSAGE}
            q2.put(d)


def new_stream_message(ms, q1, q3):
    if DEBUG_STREAM:
        print("\nNEW MS: ",ms,"\n")
    t = datetime.utcnow()
    d = {'t0': t,
         'message': ms}
    q1.put(d)
    q3.put(d)


def worker_hypervisor(queue, target):
    if DEBUG:
        print("\nworker_hypervisor target="+str(target)+" PID: ", os.getpid())
        print("\nworker_hypervisor target=" + str(target) + " queue size: ", queue.qsize())

    p_events = [Queue()] # 'i'->int, 0 the value
    p = Process(target=target, args=(queue, p_events[0]))
    p.start()
    p_running = [p]

    while True:
        sleep(PROCESS_SPAWN_DELAY)
        active_children() # calls to _cleanup()
        if DEBUG_QUEUE_SIZE:
            print("\nworker_hypervisor target=" + str(target) + " queue size: ", queue.qsize())

        q_size = queue.qsize()+1
        np_needed = ceil(q_size / LANGUAGE_SENTIMENT_WORKER_SPAWN_PROCESS_IF_QSIZE_GREATER_THAN)

        if (np_needed > len(p_running)) and (len(p_running)<=MAX_PROCESSES_PER_WORK):
            # Too many work! We need to create another process!
            if DEBUG:
                print("\n"+str(target)+" \nToo many work!!!, Creating another process!")
                print("np_needed=", np_needed,
                      "\t\t np_running=",len(p_running),
                      "\t\t q_size",q_size-1,
                      "\t\t SENTIMENT_WORKER_SPAWN_PROCESS_IF_QSIZE_GREATER_THAN=",LANGUAGE_SENTIMENT_WORKER_SPAWN_PROCESS_IF_QSIZE_GREATER_THAN)

            p_events.append(Queue())
            p = Process(target=target, args=(queue, p_events[-1]))
            p.start()
            p_running.append(p)

        elif np_needed < len(p_running):
            if DEBUG:
                print("\n"+str(target)+"\nToo many processes!!!, TERMINATING one process!")
                print("np_needed=", np_needed,
                      "\t\t np_running=",len(p_running),
                      "\t\t q_size=",q_size-1,
                      "\t\t SENTIMENT_WORKER_SPAWN_PROCESS_IF_QSIZE_GREATER_THAN=",LANGUAGE_SENTIMENT_WORKER_SPAWN_PROCESS_IF_QSIZE_GREATER_THAN)
            # We kill gracefully only one process per parent iteration
            p_events[-1].put(1)
            # We wait until we have the confirmation that the process is finally ready to die
            while p_events[-1].empty():
                pass
            # Now we can kill and delete all unuseful structures
            p_events.pop()
            p = p_running.pop()
            p.terminate()


def language_sentiment_worker(q, exit_event):
    if DEBUG:
        print("\nlanguage_sentiment_worker PID: ", os.getpid())

    while exit_event.empty():
        ms = q.get()
        try:
            # Exactly what languages are using the users to talk each other?
            ms['language'] = langdetect.detect(ms['message'])
            # This texts are too long. It's more useful for more shorter texts. Like chats. Or we can
            # split the text and do analysis by segments
            ms['sentiment_polarity'], ms['sentiment_subjectivity'] = TextBlob(ms['message']).sentiment
            ms['t1'] = datetime.utcnow()
            # Now with the results we can do whatever we want
        except Exception as e:
            # If something bad happens, we can save the message in a log file
            if DEBUG==True:
                print(e)
    exit_event.get()


def wally_alert_worker(q):
    if DEBUG == True:
        print("wally_alert_worker PID: ", os.getpid())

    while True:
        ms = q.get()
        try:
            if ms['message'] == WALLY_MESSAGE:
                r = requests.post(WALLY_SEND_ALERTS_URL, data=json.dumps( {'t0': str(ms['t0']), 'ms':str(ms['message']) }))
                if DEBUG == True:
                    print("\nWally sent correctly! r.status_code=", r.status_code)

        except Exception as e:
            if DEBUG==True:
                print("\nWally_alert_worker ERROR")
                print(e)
                # Save ms in a log file


def permanent_storage_worker(q, exit_event):
    if DEBUG == True:
        print("\npermanent_storage_worker PID: ", os.getpid())

    mongodb_client = MongoClient(MONGO_CLIENT_URI)

    db = mongodb_client[MONGO_CLIENT_DATABASE]
    BSDECC_collection = db[MONGO_CLIENT_COLLECTION]

    db_TEST = mongodb_client[MONGO_CLIENT_DATABASE_TEST]
    BSDECC_collection_TEST = db_TEST[MONGO_CLIENT_COLLECTION_TEST]

    while exit_event.empty():
        ms = q.get()
        ms['t2'] = datetime.utcnow()
        if not UNIT_TESTS:
            BSDECC_collection.insert_one(ms)
        else:
            BSDECC_collection_TEST.insert_one(ms)

    exit_event.get()


class TestStreamProcessing(unittest.TestCase):
    def setUp(self):
        self.mongodb_client = MongoClient(MONGO_CLIENT_URI)
        self.db_TEST = self.mongodb_client[MONGO_CLIENT_DATABASE_TEST]

        self.BSDECC_collection_TEST = self.db_TEST[MONGO_CLIENT_COLLECTION_TEST]
        self.BSDECC_collection_TEST.delete_many({})

        self.n_lines_processed = 0
        self.stream_in_by_file(q1, q3)

    def stream_in_by_file(self, q1, q3):
        if DEBUG_STREAM == True:
            print("\nstream_in PID:", os.getpid())

        try:
            with open("server_test_payload.txt") as f:
                partial_ms = ''
                for line in f:
                    if DEBUG_STREAM:
                        print(line)
                    # It ensures that we split the text only if it's between our desired token(s)
                    if line != '<br/>\n':
                        new_stream_message(line, q1, q3)

        except Exception as e:
            if DEBUG_STREAM:
                print(e)

            self.assertRaises(TypeError)


    def test_q3(self):
        # If after 10s can't process a small number of documents, something serious is happening
        sleep(10)
        self.assertEqual(self.BSDECC_collection_TEST.count(), 500)



if __name__ == '__main__':
    if DEBUG == True:
        print("\nMAIN process PID:", os.getpid())

    # FIFO queues. This queues are process save.
    # It's like a pipe with a few locks/semaphores.
    # With that we ensure that the data at the end of the queue is processed only once and the data isn't corrupted
    # ff maxsize=0, queue size = infinite (limited to the available memory of course)
    q1 = Queue(maxsize=0)
    q2 = Queue(maxsize=0)
    q3 = Queue(maxsize=0)

    # Now let's execute our primary workers
    p2 = Process(target=worker_hypervisor, args=(q1, language_sentiment_worker))
    p3 = Process(target=wally_alert_worker, args=(q2,))
    p4 = Process(target=worker_hypervisor, args=(q3, permanent_storage_worker))

    # Now we start the processes
    p2.start()
    p3.start()
    p4.start()

    # Necessary for unit tests
    if UNIT_TESTS:
        UNIT_TESTS = False
        unittest.main()
    p1 = Process(target=stream_in, args=(q1, q2, q3))
    p1.start()

    # Not strictly necessary because our princial processes run indefinitely
    p1.join()
    p2.join()
    p3.join()
    p4.join()
