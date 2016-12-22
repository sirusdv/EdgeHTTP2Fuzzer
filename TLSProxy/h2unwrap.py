'''
Created on Aug 24, 2016

@author: sirus
'''

import os, socket,threading,time
import SocketServer
from OpenSSL import SSL
import hexdump
from _socket import SHUT_RDWR

class SSLWrapper:
    """
    This whole class exists just to filter out a parameter
    passed in to the shutdown() method in SimpleXMLRPC.doPOST()
    """
    def __init__(self, conn):
        """
        Connection is not yet a new-style class,
        so I'm making a proxy instead of subclassing.
        """
        self.__dict__["conn"] = conn

    def __getattr__(self, name):
        return getattr(self.__dict__["conn"], name)

    def __setattr__(self, name, value):
        setattr(self.__dict__["conn"], name, value)

    def shutdown(self, how=1):
        """
        SimpleXMLRpcServer.doPOST calls shutdown(1),
        and Connection.shutdown() doesn't take
        an argument. So we just discard the argument.
        """
        try:
            self.__dict__["conn"].shutdown()
        except Exception as e:
            print "Got exception on shutdown", e
            pass
        
                

    def accept(self):
        """
        
        This is the other part of the shutdown() workaround.
        Since servers create new sockets, we have to infect
        them with our magic. :)
        """
        c, a = self.__dict__["conn"].accept()
        return (SSLWrapper(c), a)


class SecureTCPServer(SocketServer.TCPServer):
    
    def __init__(self, addr, port, key, cert, request_handler_class):
        self._addr = addr
        self._port = port
        self._key = key
        self._cert = cert
        self._handler = request_handler_class
        
        SocketServer.BaseServer.__init__(self, (addr, port), request_handler_class)
        
        ctx = SSL.Context(SSL.SSLv23_METHOD)
        #ctx = SSL.Context(SSL.TLSv1_2_METHOD)
        ctx.set_options(SSL.OP_NO_SSLv2)
        
        
        ctx.use_privatekey_file(key)
        ctx.use_certificate_file(cert)
        
        
        def cb_ALPN(conn, protos):
            print "ALPN CALLBACK"
            return b'h2'
        
        ctx.set_alpn_select_callback(cb_ALPN)
        
        def cb_NPN(conn, protos):
            print "NPN CALLBACK"
            return b'h2'
        ctx.set_npn_select_callback(cb_NPN)
        
        
        #Must be .socket
        self.socket = SSLWrapper(SSL.Connection(ctx, socket.socket(self.address_family, self.socket_type)))
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.server_bind()
        self.server_activate()
        

class ForwardingSecureTCPServer(SecureTCPServer):
    
    class ConnectionForwardingHandler(SocketServer.BaseRequestHandler):
        
        
        class Forwarder(threading.Thread):
            def __init__(self, source, forward_addr, forward_port, connect_on_data = False, log_data = True):
                threading.Thread.__init__(self)
                self.source = source
                self.dest = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.forward_addr = forward_addr
                self.forward_port = forward_port
                self.connect_on_data = connect_on_data
                self.log_data = log_data
                self.terminate = False
                
                if log_data:
                    self.id = str(threading.current_thread().ident)
                    print "TID", self.id
                    self.initer = 0
                    self.outiter = 0
                    
                
                self.connected = False
                
                print "initializing forwarder for (%s,%d)" % (forward_addr, forward_port)
                
                if not connect_on_data:
                    self.dest.connect((forward_addr, forward_port))
                    self.connected = True
        
            def run(self):
                print "starting forwarder... " 
        
                try:
                    while True:
                        if not self.connected and not self.terminate:
                            time.sleep(0.01)
                            continue
                        
                        if self.terminate:
                            break

                        data = self.dest.recv(4096*10)
                        if len(data) == 0:
                            raise Exception("endpoint closed")
                        print "Received from dest: " + str(len(data))
                        hexdump.hexdump(data)
                        if self.log_data:
                            with open(self.id + "_in" + str(self.initer)+".bin", "wb") as fd:
                                fd.write(data)
                            self.initer = self.initer+1
                                
                        
                        self.source.write_to_source(data)
                except Exception as e:
                    print "EXCEPTION reading from dest", e
        
                self.source.stop_forwarding()
                print "...ending forwarder."
                
            def write_to_dest(self, data):
                print "Sending to dest: " + str(len(data))
                hexdump.hexdump(data)
                if self.log_data:
                    with open(self.id + "_out"+str(self.outiter)+".bin", "wb") as fd:
                        fd.write(data)
                    self.outiter = self.outiter+1
                    
                if not self.connected:
                    self.dest.connect((self.forward_addr, self.forward_port))
                    self.connected = True
                
                self.dest.sendall(data)
        
            def stop_forwarding(self):
                print "...closing forwarding socket"

                try:
                    self.dest.shutdown(SHUT_RDWR)
                except Exception:
                    pass

                self.dest.close()
                self.terminate = True

        
        
        def handle(self):
            print "GOT CONNECTION."
            f = ForwardingSecureTCPServer.ConnectionForwardingHandler.Forwarder(self, self.server.forward_addr, self.server.forward_port, True, False)
            f.daemon = True
            f.start()
            
            try:
                while True:
                    data = self.request.recv(4096*10)
                    if len(data) == 0:
                        raise Exception("endpoint closed")
                    print "Received from SSL: " + str(len(data))
                    f.write_to_dest(data)
            except Exception as e:
                print "Exception reading from SSL socket.", e
                    
            f.stop_forwarding()
            
            print "CONNECTION FINISHED" 
                
        
        def write_to_source(self, data):
            self.request.sendall(data)
    
        def stop_forwarding(self):
            print "...closing SSL socket"
            self.request.close()
            
            

    
    def __init__(self, listen_addr, listen_port, listen_key, listen_cert, forward_addr, forward_port):
        SecureTCPServer.__init__(self, listen_addr, listen_port, listen_key, listen_cert, ForwardingSecureTCPServer.ConnectionForwardingHandler)
        self.forward_addr = forward_addr
        self.forward_port = forward_port


if __name__ == "__main__":
    print "starting"
    ForwardingSecureTCPServer("0.0.0.0", 8182, "server.key", "server.crt", "127.0.0.1", 1234).serve_forever()






