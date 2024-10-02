import socket

class videosocket:
    '''A special type of socket to handle the sending and receiving of fixed
       size frame strings over usual sockets.
       Size of a packet or whatever is assumed to be less than 100MB.
    '''

    def __init__(self, sock=None):
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock

    def connect(self, host, port):
        self.sock.connect((host, port))

    def vsend(self, framestring):
        totalsent = 0
        metasent = 0
        length = len(framestring)
        lengthstr = str(length).zfill(8)

        while metasent < 8:
            sent = self.sock.send(lengthstr[metasent:].encode('utf-8'))  # Encoding string to bytes for Python 3
            if sent == 0:
                raise RuntimeError("Socket connection broken")
            metasent += sent

        while totalsent < length:
            sent = self.sock.send(framestring[totalsent:])
            if sent == 0:
                raise RuntimeError("Socket connection broken")
            totalsent += sent

    def vreceive(self):
        totrec = 0
        metarec = 0
        msgArray = []
        metaArray = []
        while metarec < 8:
            chunk = self.sock.recv(8 - metarec).decode('utf-8')  # Decoding bytes to string for Python 3
            if chunk == '':
                raise RuntimeError("Socket connection broken")
            metaArray.append(chunk)
            metarec += len(chunk)
        lengthstr = ''.join(metaArray)
        length = int(lengthstr)

        while totrec < length:
            chunk = self.sock.recv(length - totrec)
            if chunk == b'':
                raise RuntimeError("Socket connection broken")
            msgArray.append(chunk)
            totrec += len(chunk)
        return b''.join(msgArray)
