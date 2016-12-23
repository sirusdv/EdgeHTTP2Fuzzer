
# HTTP/2 Peach Pit for Microsoft Edge

:fire: To make use of this Peach pit you must have a commercial copy of the [Peach Fuzzer](https://peachfuzzer.com). :fire:

Here at [Duo Labs](https://duo.com/labs) we believe that open sourcing security research tools helps the the greater research community push technology forward. If you find this release useful please consider joining us in sharing your tools which are typically considered proprietary with the public in the spirit of bettering security for everyone. 

This peach pit implements the HTTP/2 protocol ([RFC-7540](https://tools.ietf.org/html/rfc7540)) and is targetted at Microsoft Edge. It was developed as part of a Duo Labs research project and has been run through about 150,000 iterations. Traffic samples within this release were generated with the use of the [h2o](https://github.com/h2o/h2o) server. With a little bit of work and understanding of the protocol, it should be retargetable to Firefox/Chrome.

-- [@sirus](https://twitter.com/sirus)

## Details
 
 
#### HPACK_src/**
Contains C# code implementing the ```HPACKInteger``` packed integer type and the ```HuffmanTransformer``` string transformer as laid out in [RFC-7541](https://tools.ietf.org/html/rfc7541).
 
#### TLSProxy/**
As Peach currently does not support setting ALPNs on the ```SSlListener``` a pass through proxy  was implemented. It must be run alongside the main Peach.exe instance. Also contains CA cert that must be installed on the target.

#### Data/**
Contains binary samples to feed Peach. Exercises PUSH_PROMISE and related functionality. 


#### HTTP2_Data.xml
Contains all the data models in the HTTP/2 protocol. 

#### HTTP2_State.xml
Contains Peach state model for driving testing of Edge.

#### HTTP2_Client.xml
Contains agent configurations and the fuzzer run configuration. Defaults to using MSCER-2 monitoring but direct ```WindowsDebugger``` monitors are available.
 
#### mscer2*.py
As Edge launches five separate processes per fuzzing iteration attaching to all of them takes a significant amount of time.  As an alternative I've implemented a [MSCER-2](https://msdn.microsoft.com/en-us/library/dd942170.aspx) monitor. MSCER-2 is the Windows Error Reporting protocol. Details on how to leverage this can be found [here](https://duo.com/blog/remote-fuzzer-monitoring-with-windows-error-reporting-wer).
 
## Fuzzer Configuration
In this section SUT (system under test) will refer to a Windows 10 host that is to be running Edge with an IP of ```10.23.1.74```. Host will refer to the system running Peach.exe with the IP of ```10.23.1.53```.

### SUT Preparation

#### Install CA Cert
Using the windows certificate manager install the ```TLSProxy/ca.crt``` in to the trusted CA cert store.

#### Hostname Configuration
An entry pointing at the Host machine must be made in ```C:\windows\system32\drivers\etc\hosts``` under the name ```TARGET``` to for TLS to work:
```
10.23.1.53 TARGET
```

#### PageHeap Configuration
The easiest way to configure page heap is by utilizing the [EdgeDbg](https://github.com/SkyLined/EdgeDbg) package by Skylined and running ```EdgePageHeap.cmd ON``` otherwise manually configure through ``gflags.exe`` for the following five images:
* microsoftedge.exe
* microsoftedgecp.exe
* runtimebroker.exe
* browser_broker.exe
* applicationframehost.exe

#### MS-CER2 Collection

To use the native crash collection facilities of Windows the following registry key must be imported:

```
Windows Registry Editor Version 5.00

[HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\Windows Error Reporting]
"CorporateWerPortNumber"=dword:000022b1
"CorporateWerServer"="TARGET"
"Disabled"=dword:00000000
"EnableZip"=dword:00000001
"DisableQueue"=dword:00000001

[HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\Windows Error Reporting\Consent]
"DefaultConsent"=dword:00000004
```

#### Start Peach Agent 
Launch the PeachAgent.exe binary from an elevated command prompt and configure firewall settings to allow incoming connections from your Host machine.

### Host Preparation

#### Configure Pit
Edit ```HTTP2_Client.xml``` and change the IP address of the remote agent to point to your SUT:
```
<Agent name="RemoteAgent" location="tcp://10.23.1.74:9001"> <!-- Change to IP of SUT-->
```
Further down, configure the interface that for the MS-CER2 monitor to bind to:
```
<Param name="Host" value="10.23.1.53" /> <!--  CHANGE TO IP TO HOST. -->
```



## Start Fuzzing

#### Run TLSProxy
Start the TLS unwrapping proxy by executing:
```
python2 TLSProxy/h2unwrap.py
```
You will be able to monitor the traffic going to and from the SUT.  

#### Test Peach
You should be good to go! Run a validation pass to make sure all the plumbing is working with:

```
mono Peach.exe --plugins=. -1 HTTP2_Client.xml
```
You should see Edge start, a page load and then edge close. 

#### Start Fuzzing
If all goes well you should be ready to start fuzzing by dropping the ```-1``` argument:

```
mono Peach.exe --plugins=. HTTP2_Client.xml
```
