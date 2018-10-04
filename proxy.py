import sys
import traceback
import collections
import logging
import threading

import zmq

import six
from six.moves import queue


class ProxyServer(threading.Thread):
    """Proxy manager to one object."""
    def __init__(self, port=8123):
        super(ProxyServer, self).__init__()

        self.obj = []
        self.port = port

        self.is_looping = threading.Event()
        self.start()

    def run(self):

        self.is_looping.set()

        self.context = zmq.Context()

        self.rep = self.context.socket(zmq.REP)
        self.rep.bind("tcp://*:%s" % self.port)

        # sub = context.socket(zmq.SUB)
        # sub.connect("tcp://127.0.0.1:{}".format(ZMQ_PORT_PUBSUB))
        # sub.setsockopt_string(zmq.SUBSCRIBE, "")

        self.poll = zmq.Poller()
        self.poll.register(self.rep, zmq.POLLIN)
        # poll.register(sub, zmq.POLLIN)

        while self.is_looping.is_set():

            # poll
            socks = dict(self.poll.poll(500))  # 500 ms for timeout

            if socks.get(self.rep) == zmq.POLLIN:
                obj_class, cmd, args, kwargs = self.rep.recv_pyobj()

                print(obj_class, cmd, args, kwargs)

                try:

                    # find obj: need more thoughts
                    # obj = [o for o in self.obj if isinstance(self.obj, obj_class)][0]
                    obj = self.obj[0]

                    fn = getattr(obj,cmd)
                    if isinstance(fn, collections.Callable):
                        retval = fn(*args, **kwargs)
                    else:
                        retval = fn

                    self.rep.send_pyobj((True, retval), protocol=-1)

                except:
                    # exception, return the full exception info
                    info = sys.exc_info()
                    tb = "\n".join(traceback.format_exception(*info, limit=20))
                    self.rep.send_pyobj((False, (info[1], tb)), protocol=-1)


    def close(self):
        self.is_looping.clear()
        self.join()  # wait for thread to finish
        self.rep.close()
        self.context.term()


    def add(self, obj):
        self.obj.append(obj)


class ProxyClient(object):
    """Proxy for an ExperimentLog object.
    Redirects calls and property accesses to the real, remote logging object
    """
    def __init__(self, obj, port=8123):

        # possibly init obj
        # super(type(obj), self).__init__()

        self.obj = obj
        self.port = port

        # connect to the server
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect("tcp://localhost:%s" % self.port)


    def __getattr__(self, attr):


        # redirect properties
        if not isinstance(getattr(self.obj, attr) , collections.Callable):
        # attr in ['data', 'session_path', 'session_id', 't', 'in_run', 'random_seed']:
            self.socket.send_pyobj(('(self.obj)', attr,(),()))
            success, value = self.socket.recv_pyobj()
            if success:
                return value
            else:
                # deal with exceptions in the remote process
                logging.error(value[1])
                raise value[0]

        # redirect calls to the remote object
        else:
            def proxy(*args, **kwargs):
                self.socket.send_pyobj(('(self.obj)', attr, args, kwargs), protocol=-1)
                success, value = self.socket.recv_pyobj()
                if success:
                    return value
                else:
                    # deal with exceptions in the remote process
                    logger.error(value[1])
                    raise value[0]

            return proxy

    def add(self, obj):
        print(obj)
