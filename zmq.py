import zmq
import threading

import six
from six.moves import queue
import logging

class Publisher(object):
    def __init__(self, port=8765):
        super(Publisher, self).__init__()
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind("tcp://127.0.0.1:{}".format(port))

    def send_message(self, header, message):
        self.socket.send_pyobj([header, message])

    def close(self):
        self.socket.close()
        self.context.term()


class ThreadedSubscriber(threading.Thread):
    """Threaded and non-blocking.
    """
    def __init__(self, port=8765):

        super(ThreadedSubscriber, self).__init__()
        self.is_looping = threading.Event()
        self.dataqueue = queue.Queue()
        self.Empty = queue.Empty
        self.port = port

    def run(self):

        # 0mq socket
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect("tcp://127.0.0.1:{}".format(self.port))
        self.socket.setsockopt_string(zmq.SUBSCRIBE, "")

        # 0mq poller
        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)

        self.is_looping.set()

        while self.is_looping.is_set():
            socks = dict(self.poller.poll())

            # if socks.get(self.socket) == zmq.POLLIN:
            if self.socket in socks and socks[self.socket] == zmq.POLLIN:
                data = self.socket.recv_pyobj()
                self.dataqueue.put(data)

        logging.info('tp quit')


    def stop(self):
        logging.info('call stop')
        self.is_looping.clear()
        self.join()  # wait for thread to finish
        self.socket.close()
        self.context.term()


class LPClient(object):
    """Lazy Pirate Client, will connect to a server with polling, does 
    REQUEST_RETRIES tries with REQUEST_TIMEOUT before closing. Execute in main
    thread with blocking.
    """

    def __init__(self, 
        server,
        port,
        REQUEST_TIMEOUT = 2500,
        REQUEST_RETRIES = 3,
        ):

        super(LPClient, self).__init__()

        self.REQUEST_TIMEOUT = REQUEST_TIMEOUT
        self.REQUEST_RETRIES = REQUEST_RETRIES
        self.SERVER_ENDPOINT = "tcp://"+server+":%s" % port

        logger.info(self.SERVER_ENDPOINT)

        self.context = zmq.Context(1)

        logger.info("I: Connecting to server")
        self.client = self.context.socket(zmq.REQ)
        self.client.connect(self.SERVER_ENDPOINT)

        self.poll = zmq.Poller()
        self.poll.register(self.client, zmq.POLLIN)

    def send_pyobj(self, request):
        retries_left = self.REQUEST_RETRIES

        while retries_left:

            logger.info("I: Sending (%s)" % request)
            self.client.send_pyobj(request)

            expect_reply = True
            while expect_reply:
                socks = dict(self.poll.poll(self.REQUEST_TIMEOUT))

                if socks.get(self.client) == zmq.POLLIN:
                    reply = self.client.recv_pyobj()

                    if not reply:
                        break

                    if reply: ## reply code is ok
                        logger.info("I: Server replied OK (%s)" % reply)
                        retries_left = 0#self.REQUEST_RETRIES
                        expect_reply = False
                    else:
                        logger.info("E: Malformed reply from server: %s" % reply)

                else:
                    logger.info("W: No response from server, retrying")
                    # Socket is confused. Close and remove it.
                    self.client.setsockopt(zmq.LINGER, 0)
                    self.client.close()
                    self.poll.unregister(self.client)
                    retries_left -= 1
                    if retries_left == 0:
                        logger.info("E: Server seems to be offline, abandoning")
                        raise ConnectionError(self.SERVER_ENDPOINT+' is offline', 0)
                        # break
                    logger.info("I: Reconnecting and resending (%s)" % request)

                    # Create new connection
                    self.client = self.context.socket(zmq.REQ)
                    self.client.connect(self.SERVER_ENDPOINT)
                    self.poll.register(self.client, zmq.POLLIN)
                    self.client.send_pyobj(request)

    def term(self):
        ## could be put in a enter/exit
        self.context.term()
