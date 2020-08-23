import pandas as pd
import re
import os
from fnmatch import fnmatch
import time
import pyhibp
import configparser
path = '/'.join((os.path.abspath(__file__).replace('\\', '/')).split('/')[:-1])
config = configparser.ConfigParser()
config.read(os.path.join(path, 'settings.conf'))
api = config['settings']['hibpapikey']
delay = float(config['settings']['timedelay'])
pyhibp.set_user_agent(ua="nynerd's HIBP Project")
pyhibp.set_api_key(key=api)

def intro():
    print("""
    
  _    _ _____ ____  _____    _____  _____ _____  _____  ______ _____  
 | |  | |_   _|  _ \|  __ \  |  __ \|_   _|  __ \|  __ \|  ____|  __ \ 
 | |__| | | | | |_) | |__) | | |__) | | | | |__) | |__) | |__  | |__) |
 |  __  | | | |  _ <|  ___/  |  _  /  | | |  ___/|  ___/|  __| |  _  / 
 | |  | |_| |_| |_) | |      | | \ \ _| |_| |    | |    | |____| | \ \ 
 |_|  |_|_____|____/|_|      |_|  \_\_____|_|    |_|    |______|_|  \_\
                                                                       
                                                                       

""")

def percentage(part, whole):
  return 100 * float(part)/float(whole)
####Function to scan all the csv files
def scanner(path): #Scans for every csv files in adirectory that doesn't have _breaches in its filename
    filesv =[]
    root = path
    pattern = "*.csv"
    for path, subdirs, files in os.walk(root):
        for name in files:
            if fnmatch(name, pattern):
                if '_breaches' not in name:
                    filesv.append(os.path.join(path, name).replace('\\','/'))
    try:
        breach_file = f"{path}/{config['settings']['combinedfilename']}"
        filesv.remove(breach_file)
    except Exception:
        pass
    config.set("settings", "totalcsv", str(len(filesv)))
    config.write(open("settings.conf", "w"))
    return filesv

###Function to detect all the emails from the csv files followed by scanner() function
def detectemails(): #returns the list of unique emails from all csv files and subfiles
    filesv = scanner(path=path)
    emailslist = []
    for fi in filesv:
        with open(fi,'r',encoding='utf-8')as f:
            data_frame = f.readlines()
        emails = re.findall(r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+", str(data_frame))
        for e in emails:
            if e != "":
                if e not in emailslist:
                    emailslist.append(e)
    print(f"{len(emailslist)} Unique Emails Detected From {len(filesv)} CSV FILES")
    config.set("settings", "totalemails", str(len(emailslist)))
    config.write(open("settings.conf", "w"))
    return emailslist

def individual(files,resume):
    config.set("settings", "completedcsv", "0")
    if resume == False:
        config.set("settings", "totalcsvscanned", "0")
    config.write(open("settings.conf", "w"))  
    files = files
    csvindex = 0
    for fi in files:
        print(f'\nNow Scanning : {fi}')
        csvindex+=1
        with open(fi,'r')as f:
            data_frame = f.readlines()
            f.close()
        emails = re.findall(r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+", str(data_frame))
        #emails = list(dict.fromkeys(emails))
        columns = data_frame[0]
        breach_file = fi+'_breaches.csv'
        with open(breach_file,'w')as f:
            f.write("Emails,Breaches,Breach Information,Paste Information,"+ columns)
            f.close()
        already_scanned=[]
        i=0
        for e in emails:
            
            i+=1
            if e in already_scanned:
                pass
            else:
                print(f'     +{e}')
                already_scanned.append(e)
                time.sleep(delay)
                resp = pyhibp.get_account_breaches(account=e, truncate_response=True)
                time.sleep(delay)
                pastes = pyhibp.get_pastes(email_address=e)
                if resp:
                    breaches = f"Found in {len(resp)} Breaches"
                    Breach_Informations = str(resp)[:32700]
                    try:
                        lines = []
                        for i in range(len(data_frame)):
                            if e in data_frame[i]:
                                lines.append(data_frame[i])
                        other_informations = lines[0].replace('\n','')
                    except Exception:
                        other_informations = ""
                    pas = f"Found in {len(pastes)} Pastes"
                    with open(breach_file,'a',encoding='UTF-8')as f:
                        string = f"""{e},{breaches},"{Breach_Informations}",{pas},{other_informations}\n"""
                        f.write(string)
                        f.close()
                    time.sleep(delay) 
        
        if resume:
            config.set("settings", "totalcsvscanned", str(csvindex))
            config.write(open("settings.conf", "w"))
        else:
            resume_count = int(config['settings']['totalcsvscanned'])
            config.set("settings", "totalcsvscanned", str(resume_count+1))
            config.write(open("settings.conf", "w"))
        per = percentage(csvindex,len(files))
        print(f"{per}% Completed")
    config.set("settings", "completedcsv", "1")
    config.write(open("settings.conf", "w"))


def combinedfile(breach_file,unique_emails,resume):
    config.set("settings", "combinedfilename", breach_file)
    config.set("settings", "completedemails", "0")
    if resume == False:
        config.set("settings", "totalemailsscanned", "0") 
    config.write(open("settings.conf", "w"))
    if resume == False:
        with open(breach_file,'w')as f:
            f.write(f"Emails,Breaches,Breach Informations,Paste Information\n")
            f.close()
    i=0
    for email in unique_emails:
        i+=1
        e=email
        time.sleep(delay)
        resp = pyhibp.get_account_breaches(account=e, truncate_response=True)
        time.sleep(delay)
        pastes = pyhibp.get_pastes(email_address=e)
        breaches = f"Found in {len(resp)} Breaches"
        if resp:
            Breach_Informations = str(resp)[:32700]
            pas = f"Found in {len(pastes)} Pastes"
            with open(breach_file,'a',encoding='UTF-8')as f:
                string = f"""{e},{breaches},"{Breach_Informations}",{pas}\n"""
                f.write(string)
            time.sleep(delay)
            per = percentage(i,len(unique_emails))
            print(f"{per}% Completed") 
        if resume:
            config.set("settings", "totalemailsscanned", str(i))
            config.write(open("settings.conf", "w"))
        else:
            resume_count = int(config['settings']['totalemailsscanned'])
            config.set("settings", "totalemailsscanned", str(resume_count+1))
            config.write(open("settings.conf", "w"))
    config.set("settings", "completedemails", "1")
    config.write(open("settings.conf", "w"))

def returnnonusedemails(breach_file,unique_emails):
    with open(breach_file,'r') as f:
        data_frame = f.readlines()
    emails = re.findall(r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+", str(data_frame))    
    nonusedemails=[]
    for email in unique_emails:
        if email not in emails:
            nonusedemails.append(email)
    return nonusedemails

def returnresumefiles():
    csvcompleted = int(config['settings']['totalcsvscanned'])
    files = scanner(path=path)
    resumingfiles = []
    for i in range(csvcompleted,len(files)):
        resumingfiles.append(files[i])
    return resumingfiles
        

if __name__ == "__main__":
    intro()
    completedemails = int(config['settings']['completedemails'])
    completedcsv = int(config['settings']['completedcsv'])
    option = int(input("\n\nPlease Select An Option \n[1]Individual Copy\n[2]Combined Breach Info :"))
    if option == 2:
        if completedemails:
            #breach_file = config['settings']['combinedfilename']
            breach_file= input("Enter a filename where you want to save Breach Informations: ")
            combinedfile(breach_file=breach_file,unique_emails=detectemails(),resume=False)
        else:
            suboption = int(input("\n\n+-----------------------------+\n\nIncomplete Session Detected, \n[1]Continue from previous session\n[2]Restart Operation :"))
            if suboption == 1: 
                breach_file = (config['settings']['combinedfilename'])
                uni = returnnonusedemails(breach_file=breach_file,unique_emails=detectemails())
                combinedfile(breach_file=breach_file,unique_emails=uni,resume=True)
            else:
                breach_file= input("Enter a filename where you want to save Breach Informations: ")
                combinedfile(breach_file=breach_file,unique_emails=detectemails(),resume=False)
    elif option == 1:
        if completedcsv:
            #breach_file = config['settings']['combinedfilename']
            individual(files=scanner(path=path),resume=False)
        else:
            suboption = int(input("\n\n+-----------------------------+\n\nIncomplete Session Detected, \n[1]Continue from previous session\n[2]Restart Operation :"))
            if suboption == 1: 
                individual(files=returnresumefiles(),resume=True)
            else:
                individual(files=scanner(path=path),resume=False)