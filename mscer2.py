'''
Created on Sep 7, 2016

@author: sirus
'''

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import threading
import xml.etree.ElementTree as ET

import time

class ServerThread(threading.Thread):
    def __init__(self, callback, handlerClass, port = 8881, address='0.0.0.0'):
        threading.Thread.__init__(self)
        self._stop = False
        self._port = port
        self._addr = address
        self._handlerClass = handlerClass
        self._handlerArgs = callback;
        
        def handler(*args):
            return self._handlerClass(self._handlerArgs, *args)
        
        self._httpd = HTTPServer((self._addr, self._port), handler)
        
    def shutdown(self):
        print "Shutting down httpd"
        try:
            self._httpd.shutdown()
        except:
            pass
        
    def run(self):
        print "Starting httpd"
        self._httpd.serve_forever()
        
        
        

class MSCER2Handler(BaseHTTPRequestHandler):
    
    def __init__(self, callback, *args):
        self._callback = callback
        BaseHTTPRequestHandler.__init__(self, *args)
    
    
    def do_POST(self):
        self.data_string = self.rfile.read(int(self.headers['Content-Length'])).decode('utf-16').encode('utf-8')
        print "POST", self.path, self.data_string
        
        try:
            
            root = ET.fromstring(self.data_string)
            
            appInfo = root.find("APPLICATIONINFO")
            signature = root.find("SIGNATURE")
            eventInfo = root.find("EVENTINFO")

            appName = appInfo.attrib['appname']
            appPath = appInfo.attrib['apppath']
            eventType = eventInfo.attrib['eventtype']
            
            params = {}
            for param in signature.findall('PARAMETER'):
                params[param.attrib['name']] = param.attrib['value']
                
            
            print appName, repr(params)
            
            if self._callback != None:
                self._callback(appName, appPath, eventType, params)
            
                
        except Exception as e:
            print "EX", e
        
        
        self.send_response(404)
        self.end_headers()
    

def test_callback(appName, appPath, eventType, params):
    print "CALLBACK", "appName", appName,"appPath", appPath, "eventType", eventType, "params", params
    
if __name__ == "__main__":
    server = ServerThread(test_callback, MSCER2Handler)
    server.daemon = True
    server.start()
    
    try:
        while True:
            time.sleep(1)
        
    except KeyboardInterrupt:
        server.shutdown()

