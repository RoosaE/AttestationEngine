#Copyright 2021 Nokia
#Licensed under the BSD 3-Clause Clear License.
#SPDX-License-Identifier: BSD-3-Clear

import subprocess
import datetime
import yaml
import binascii
import tempfile

from urllib.parse import urlparse

import a10.asvr.protocols.A10ProtocolBase

import a10.structures.constants
import a10.structures.returncode


class A10tpm2send(a10.asvr.protocols.A10ProtocolBase.A10ProtocolBase):
    NAME = "A10TPMSENDSSL"

    def __init__(self, endpoint, policyintent, policyparameters, callparameters):
        super().__init__(endpoint, policyintent, policyparameters, callparameters)

    def exec(self):
        transientdata = {}

        #print(
        #    "Calling protocol A10TPMSENDSSL ",
        #    "endpoint ",self.endpoint,"\n",
        #    "intent ",self.policyintent,"\n",
        #    "polparams ",self.policyparameters,"\n",
        #    "cpsparams ",self.callparameters,"\n"
        #)
        
        rc = None
        
        if self.policyintent=="tpm2/pcrs":
            rc = self.tpm2pcrs()
        elif self.policyintent=="tpm2/quote":
            rc = self.tpm2quote()
        elif self.policyintent=="sys/info":
            rc = self.sysinfo()
        else:
            print(" Intent not understood")
            rc = a10.structures.returncode.ReturnCode(
                a10.structures.constants.UNSUPPORTEDPROTOCOLINTENT, {"msg":"unsupported intent -> "+self.policyintent,"transientdata":transientdata}
            )
            print(" rc object ",rc)
       
        return rc
      
    #
    # Utility functions
    #

    def getTimeout(self):
        timeout = 20
        print("Timeout ",self.callparameters.get("a10_tpm_send_ssl"))
        if  self.callparameters.get("a10_tpm_send_ssl").get("timeout")!=None:
            timeout = self.callparameters.get("a10_tpm_send_ssl").get("timeout")
        return int(timeout)
      
    def getTCTI(self):
        #
        # The TCTI is created from the element description
        # and contains the key and the username and the endpoint IP address
        # which are then passed to ssh in the form
        #
        # cmd:ssh <username>@<ip> -i <key> tpm2_send
        #
        # For example "cmd:ssh pi@10.144.176.152 -i /var/a10keystore/lassa tpm2_send"
        #
        key = self.callparameters["a10_tpm_send_ssl"]["key"]
        username = self.callparameters["a10_tpm_send_ssl"]["username"]
        ip = urlparse(self.endpoint).hostname   # we need just the IP address, ssh does the rest

        tcti = "cmd:ssh "+username+"@"+ip+" -i "+key+" tpm2_send"
        print("CONSTRUCTED TCTI IS ",tcti)

        return tcti

    def getSSH(self):
        #
        # This is the structure used for the SSH command
        #    
        # eg: ssh <username>@<ip| -i <key>
        #
        key = self.callparameters["a10_tpm_send_ssl"]["key"]
        username = self.callparameters["a10_tpm_send_ssl"]["username"]
        ip = urlparse(self.endpoint).hostname   # we need just the IP address, ssh does the rest

        ssh = "ssh "+username+"@"+ip+" -i "+key+" "
        print("CONSTRUCTED SSH IS ",ssh)
        
        return ssh
    
    #
    # These functions implement the specific commands by calling out to tpm2_tools installed locally
    #
    # I really should add the Claim structure to the generic set of things instead of being buried away in nut10 somewhere...future TODO
    #
    # Each will return a ReturnCode complete with a Claim structure, if successful
    #  
      
    def processQuote(self,h):
        j = {}
        print("Quote part is ",h["quoted"])
        with tempfile.NamedTemporaryFile() as tf:
            b = binascii.a2b_hex(h["quoted"])
            tf.write(b)
            cmd = ["tpm2_print","-t","TPMS_ATTEST",tf.name]
            tf.seek(0)
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE) 
            o = p.communicate(input=b)[0]
            j = yaml.load(o, Loader=yaml.BaseLoader)
        print("processed as ",type(j),j)
        return j

    def tpm2quote(self):
        claim = { "header": {
                "ta_received": str(datetime.datetime.now(datetime.timezone.utc)),
                "ssl_tpm2send_timeout":str(self.getTimeout())
             },
             "payload":{},
             "signature":{}
           }       

        print("\nquote policy parameters ",self.policyparameters)

        #resolve ak
        ak_to_use = "0x810100AA"

        cmd = "tpm2_quote -c "+ak_to_use+" -l "+self.policyparameters["pcrselection"]

        #TODO: this is a bit odd because the protocol returns always success...fix later

        #TODO: tpm2_quote returns a raw structure as YAML, this needs to be processed into a fuller description
        # that tpm2_print returns
        #Maybe use pytss?

        try:
            cmdwtcti = cmd.split()+["-T",self.getTCTI()]

            print("Trying ",cmdwtcti)

            out = subprocess.check_output(cmdwtcti, stderr=subprocess.STDOUT, timeout=self.getTimeout()) 
            print("OUT=",out)
        except subprocess.CalledProcessError as exc:
            print("Status : FAIL", exc)
            claim['payload']={"msg":"Command failed to execute","exc":str(exc)}
        except subprocess.TimeoutExpired as exc:
            claim['payload']={"msg":"Connection and/or processing timedout after "+str(self.getTimeout())+"seconds"} 
        else:
            quoteyaml = yaml.load(out, Loader=yaml.BaseLoader)
            claim['payload']['hexquote']=quoteyaml
            claim['payload']['quote']=self.processQuote(quoteyaml)


        # and return

        claim["header"]["ta_complete"] = str(datetime.datetime.now(datetime.timezone.utc))

        return a10.structures.returncode.ReturnCode(
                a10.structures.constants.PROTOCOLSUCCESS, {"claim":claim,"transientdata":{}}
            )    




    def tpm2pcrs(self):
        claim = { "header": {
                "ta_received": str(datetime.datetime.now(datetime.timezone.utc)),
                "ssl_tpm2send_timeout":str(self.getTimeout())
             },
             "payload":{},
             "signature":{}
           }

        # Now create the command

        cmd = 'tpm2_pcrread'

        #TODO: this is a bit odd because the protocol returns always success...fix later

        try:
            cmdwtcti = cmd.split()+["-T",self.getTCTI()]
            print("Trying ",cmdwtcti)

            out = subprocess.check_output(cmdwtcti, stderr=subprocess.STDOUT, timeout=self.getTimeout()) 
        except subprocess.CalledProcessError as exc:
            print("Status : FAIL", exc)
            claim['payload']={"msg":"Command failed to execute","exc":str(exc)}
        except subprocess.TimeoutExpired as exc:
            claim['payload']={"msg":"Connection and/or processing timedout after "+str(self.getTimeout())+"seconds"} 
        else:
            claim['payload']['pcrs']=yaml.load(out, Loader=yaml.BaseLoader)

        # and return

        claim["header"]["ta_complete"] = str(datetime.datetime.now(datetime.timezone.utc))

        return a10.structures.returncode.ReturnCode(
                a10.structures.constants.PROTOCOLSUCCESS, {"claim":claim,"transientdata":{}}
            )    

    def sysinfo(self):
        claim = { "header": {
                "ta_received": str(datetime.datetime.now(datetime.timezone.utc)),
                "ssl_tpm2send_timeout":str(self.getTimeout())
             },
             "payload":{},
             "signature":{}
           }

        # Now create the command

        cmd = 'uname -a'

        #TODO: this is a bit odd because the protocol returns always success...fix later

        try:
            cmdwtcti = (self.getSSH()+cmd).split()
            print("Trying ",cmdwtcti)

            out = subprocess.check_output(cmdwtcti, stderr=subprocess.STDOUT, timeout=self.getTimeout()) 

        except subprocess.CalledProcessError as exc:
            print("Status : FAIL", exc)
            claim['payload']={"msg":"Command failed to execute","exc":str(exc)}
        except subprocess.TimeoutExpired as exc:
            claim['payload']={"msg":"Connection and/or processing timedout after "+str(self.getTimeout())+"seconds"} 
        else:
            claim['payload']['systeminfo']={'uname':out.decode("utf-8")}
            print("PAYLOAD=",claim['payload'])
            

        # and return

        claim["header"]["ta_complete"] = str(datetime.datetime.now(datetime.timezone.utc))

        return a10.structures.returncode.ReturnCode(
                a10.structures.constants.PROTOCOLSUCCESS, {"claim":claim,"transientdata":{}}
            )    
    