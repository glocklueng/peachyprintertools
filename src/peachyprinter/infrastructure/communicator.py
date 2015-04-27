import libusb1
import usb1
import logging
import threading
import time
from messages import ProtoBuffableMessage

logger = logging.getLogger('peachy')


class Communicator(object):
    def send(self, message):
        raise NotImplementedError()

    def register_handler(self, message_type, handler):
        raise NotImplementedError()

class UsbPacketCommunicator(Communicator, threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self._handlers = {}
        self._usbContext = None
        self._device = None
        self._devHandle = None

    def start(self):
        self._usbContext = usb1.USBContext()
        self._device = self._usbContext.getByVendorIDAndProductID(0x16d0, 0xaf3)
        self._devHandle = self._device.open()
        self._devHandle.claimInterface(0)
        super(UsbPacketCommunicator, self).start()

    def close(self):
        self._devHandle.close()

    def run(self):
        while True:
            data = None
            try:
                data = self._devHandle.bulkRead(3, 64, timeout=100)
            except (libusb1.USBError,):
                pass
            if not data:
                continue
            logger.info("Received %d bytes from device" % (len(data),))

    def send(self, message):
        data = chr(message.TYPE_ID) + message.get_bytes()
        self._devHandle.bulkWrite(2, data, timeout=1000)

    def register_handler(self, message_type, handler):
        if not issubclass(message_type, ProtoBuffableMessage):
            logger.error("ProtoBuffableMessage required for message type")
            raise Exception("ProtoBuffableMessage required for message type")
        if message_type in self._handlers:
            self._handlers[message_type].append(handler)
        else:
            self._handlers[message_type] = [handler]

class SerialCommunicator(Communicator, threading.Thread):
    def __init__(self, port, header, footer, escape):
        threading.Thread.__init__(self)
        self._send_lock = threading.Lock()
        self._port = port
        self._running = False
        self._header = header
        self._footer = footer
        self._escape = escape
        self._to_be_escaped = [self._header, self._footer, self._escape]
        self._read_bytes = ''
        self._escape_next = False
        self._handlers = {}
        self._connection = None
        self._send_count = 0
        self._send_start = time.time()

    def send(self, message):
        if not self._running:
            logger.error("attempt to send message before start")
            raise Exception("attempt to send message before start")
        out = [self._header]
        for c in (chr(message.TYPE_ID) + message.get_bytes()):
            if c in self._to_be_escaped:
                out.append(self._escape)
                out.append('%c' % ((~ord(c) & 0xFF),))
            else:
                out.append(c)
        out.append(self._footer)
        self._send_lock.acquire()
        try:
            self._connection.flush()
            self._connection.write(''.join(out))
            self._send_count += len(out)
            if self._send_count > 200000:
                now = time.time()
                total = now - self._send_start
                self._send_start = now
                logger.info("WROTE: %s bytes in %5.f s (%f / sec)" % (self._send_count, total, self._send_count / total))
                self._send_count = 0
        finally:
            self._send_lock.release()

    def start(self):
        logging.info("Opening Serial Port %s" % self._port)
        self._connection = serial.Serial(self._port, timeout=1)
        self._connection.writeTimeout = None
        logging.info("Opened Serial Port %s Opened" % self._port)
        super(SerialCommunicator, self).start()
        while not self._running:
            time.sleep(0.01)

    def run(self):
        try:
            self._running = True
            while self._running:
                self._recieve()
        except Exception as ex:
            logger.error(ex)
            raise
        finally:
            if self._connection:
                self._connection.close()
        logger.info("Closed serial port: %s" % (self._port,))

    def _recieve(self):
        try:
            # TODO I'm 99% sure that read() can return more
            # than one byte, and this will discard the rest of them.
            byte = self._connection.read()
            if not byte:
                return
            byte = byte[0]
            if byte == self._header:
                self._read_bytes = byte
            elif byte == self._footer and self._read_bytes:
                self._process(self._read_bytes[1:])
                self._read_bytes = ''
            elif byte == self._escape and self._read_bytes:
                self._escape_next = True
            elif self._escape_next and self._read_bytes:
                self._read_bytes += chr(0xff & ~ord(byte))
                self._escape_next = False
            elif self._read_bytes:
                self._read_bytes += byte
            else:
                pass
        except serial.SerialTimeoutException:
            pass

    def _process(self, data):
        message_type_id = ord(data[0])
        for (message, handlers) in self._handlers.items():
            if message.TYPE_ID == message_type_id:
                for handler in handlers:
                    handler(message.from_bytes(data[1:]))

    def register_handler(self, message_type, handler):
        if not issubclass(message_type, ProtoBuffableMessage):
            logger.error("ProtoBuffableMessage required for message type")
            raise Exception("ProtoBuffableMessage required for message type")
        if message_type in self._handlers:
            self._handlers[message_type].append(handler)
        else:
            self._handlers[message_type] = [handler]

    def close(self):
        self._running = False
        while self.is_alive():
            time.sleep(0.01)


class NullCommunicator(Communicator):
    def send(self, message):
        pass

    def register_handler(self, message_type, handler):
        pass
