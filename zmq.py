import zmq
import threading
import queue
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
