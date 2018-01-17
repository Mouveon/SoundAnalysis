#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import RPi.GPIO as GPIO
import subprocess
import logging
import logging.handlers
import threading
import socket
import fcntl
import struct
import netifaces

#Parametre du fichier de log
LOG_FILENAME='/var/log/raspiswitch.log'
TAILLE=20000
SAVE=5
level=logging.DEBUG

#Etat du systeme
CHECK=5

etat=False


#def recupWlan():
#    my_logger=logging.getLogger('GardienBienEntendu')
#    my_logger.debug('DESACTIVATION DES INTERFACES WIFI INUTILES')

#    ret = ""
#    allIfaces = pyiface.getIfaces()
#    for iface in allIfaces:
#        ret += iface.name

#    posi_deb = ret.find("w")
#    posi_fin = ret.find("0",posi_deb+5)
#
#    if posi_fin == -1:
#        posi_fin = len(ret)

#    a=ret[posi_deb:posi_fin]

#    b= str(filter(str.isdigit,a)).translate(None,'0')
    
#    ret1 = []

#    for ch in b:
#        ret1.append(ch)

#    for k in ret1:
#        iff=pyiface.Interface(name="wlan"+k)
    #print "wlan"+k
#        iff.flags=iff.flags & ~pyiface.IFF_UP





#Fonction reflexe/interruption
def switch(pin):
    my_logger=logging.getLogger('GardienBienEntendu')
    my_logger.debug('INTERRUPTION DETECTE')
    subprocess.call(['sudo', 'reboot'], stdin=None, stdout=None, stderr=None, shell=False)              

#Fonction de configuration du systeme (Serveur/Client/Serveur+partag co)
def changement():
    #On recuperre notre logger
    my_logger=logging.getLogger('GardienBienEntendu')
    #Lecture de l'état du switch
    val=GPIO.input(22)
    vol=GPIO.input(27)
    my_logger.debug('Pin 22: %s', val)
    my_logger.debug('Pin 27: %s', vol)
   
    #Etat 1
    if val==1 and vol==0:
        #print('Serveur Prive')
        #Creation des messages de debug dans le log
        my_logger.debug('POSITION SERVEUR SUR RESEAU PRIVE. Temps ecoule en seconde:')

        #configuration des ip 
        fichier=open("/etc/dhcpcd.conf", "w")
        fichier.write("hostname")
        fichier.write("\nclientid")
        fichier.write("\npersistent")
        fichier.write("\noption rapid_commit")
        fichier.write("\noption domain_name_servers, domain_name, domain_search, host_name")
        fichier.write("\noption classless_static_routes")
        fichier.write("\noption ntp_servers")
        fichier.write("\nrequire dhcp_server_identifier")
        fichier.write("\nslaac private")
        fichier.write("\nnohook lookup-hostname")
        fichier.write("\n")
        fichier.write("\ninterface wlan0")
        fichier.write("\ninform 192.168.2.2")
        fichier.write("\nstatic routers=192.168.2.1")
        fichier.write("\n")
        fichier.write("\ninterface eth0")
        fichier.write("\ninform 192.168.2.3/24")
        fichier.write("\nstatic routers=192.168.2.1")
        fichier.write("\n")
        fichier.write("\ninterface br0")
        fichier.write("\ninform 192.168.2.1/24")
        fichier.write("\nstatic routers=192.168.2.1")  
        fichier.close()

        #connexion automatique
        fichier=open("/etc/wpa_supplicant/wpa_supplicant.conf", "w")
        fichier.write("\nctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev")
        fichier.write("\nupdate_config=1")
        fichier.write("\ncountry=FR")
        fichier.close()
    
        #point d'acces
        fichier=open("/etc/default/hostapd", "w")
        fichier.write("# Defaults for hostapd initscript")
        fichier.write('#\nDAEMON_CONF="/etc/hostapd/hostapd_BienEntendu.conf"')
        fichier.close()

        #Configuration du point d'acces
        fichier=open("/etc/hostapd/hostapd_BienEntendu.conf", "w")
        fichier.write('\ninterface=wlan0')
        fichier.write("\nbridge=br0")
        fichier.write('\ndriver=nl80211')
        fichier.write('\ncountry_code=FR')
        fichier.write('\nssid=BienEntendu')
        fichier.write('\nhw_mode=g')
        fichier.write('\nchannel=6')
        fichier.write('\nwpa=2')
        fichier.write('\nwpa_passphrase=mezule08')
        fichier.write("\nwpa_key_mgmt=WPA-PSK")
        fichier.write("\nwpa_pairwise=CCMP")
        fichier.write("\nrsn_pairwise=CCMP")
        fichier.close()
        
        #serveur dhcp
        fichier=open("/etc/dnsmasq.conf", "w")
        fichier.write('\ninterface=br0')
        fichier.write('\ndhcp-range=192.168.2.10,192.168.2.99,12h')
        fichier.close()  
        
        #Demarrage des services qu'on veut  
        #Je suis sur y'a moyen de faire sans redemarrer
        subprocess.call(['sudo', 'systemctl','start','dhcpcd.service'], stdin=None, stdout=None, stderr=None, shell=False)
        subprocess.call(['sudo', 'brctl','addbr','br0'], stdin=None, stdout=None, stderr=None, shell=False)
        subprocess.call(['sudo', 'brctl','addif','br0','eth0'], stdin=None, stdout=None, stderr=None, shell=False)
        subprocess.call(['sudo', 'systemctl','start','hostapd.service'], stdin=None, stdout=None, stderr=None, shell=False)
        subprocess.call(['sudo', 'systemctl','start','dnsmasq.service'], stdin=None, stdout=None, stderr=None, shell=False)
        subprocess.call(['sudo', 'systemctl','start','shairport.service'], stdin=None, stdout=None, stderr=None, shell=False)

        tmp=1
    
    #Etat 2
    elif val==0 and vol==0:
        #print('Client')

        #Creation des messages de debug dans le log
        my_logger.debug('POSITION CLIENT')
        
        #IP
        fichier=open("/etc/dhcpcd.conf", "w")
        fichier.write("hostname")
        fichier.write("\nclientid")
        fichier.write("\npersistent")
        fichier.write("\noption rapid_commit")
        fichier.write("\noption domain_name_servers, domain_name, domain_search, host_name")
        fichier.write("\noption classless_static_routes")
        fichier.write("\noption ntp_servers")
        fichier.write("\nrequire dhcp_server_identifier")
        fichier.write("\nslaac private")
        fichier.write("\nnohook lookup-hostname")
        fichier.write("\n")
        fichier.write("\ninterface wlan0")
        fichier.write("\n")
        fichier.write("\ninterface eth0")
        fichier.close()

        #Co auto wifi
        fichier=open("/etc/wpa_supplicant/wpa_supplicant.conf", "w")
        fichier.write("\nctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev")
        fichier.write("\nupdate_config=1")
        fichier.write("\ncountry=FR")
        fichier.write("\n ")
        fichier.write("\nnetwork={")
        fichier.write('\n        ssid="BienEntendu"')
        fichier.write('\n        psk="mezule08"')
        fichier.write("\n        key_mgmt=WPA-PSK")
        fichier.write("\n}")
        fichier.close()

        #Point d'acces
        fichier=open("/etc/default/hostapd", "w")
        fichier.write("# Defaults for hostapd initscript")
        fichier.write('\n#DAEMON_CONF="/etc/hostapd/hostapd_BienEntendu.conf"')
        fichier.close()

        fichier=open("/etc/hostapd/hostapd_BienEntendu.conf", "w")
        fichier.write('\n')
        fichier.close()

        #Serveur DHCP
        fichier=open("/etc/dnsmasq.conf", "w")
        fichier.write("\n")
        fichier.close()

        subprocess.call(['sudo', 'systemctl','start','dhcpcd.service'], stdin=None, stdout=None, stderr=None, shell=False)
        subprocess.call(['sudo', 'ifup','wlan0'], stdin=None, stdout=None, stderr=None, shell=False)  
        subprocess.call(['sudo', 'systemctl','start','shairport.service'], stdin=None, stdout=None, stderr=None, shell=False)

      
        tmp=2

    #Etat 3
    elif val==0 and vol==1:
        #print('Serveur partage')

        #Creation des messages de debug dans le log
        my_logger.debug('POSITION SERVEUR AVEC ACCES INTERNET')
        
        #IP
        fichier=open("/etc/dhcpcd.conf", "w")
        fichier.write("hostname")
        fichier.write("\nclientid")
        fichier.write("\npersistent")
        fichier.write("\noption rapid_commit")
        fichier.write("\noption domain_name_servers, domain_name, domain_search, host_name")
        fichier.write("\noption classless_static_routes")
        fichier.write("\noption ntp_servers")
        fichier.write("\nrequire dhcp_server_identifier")
        fichier.write("\nslaac private")
        fichier.write("\nnohook lookup-hostname")
        fichier.write("\n")
        fichier.write("\ninterface wlan0")
        fichier.write("\n")
        fichier.write("\ninterface eth0")
        fichier.write("\n")
        fichier.write("\ninterface br0")
        fichier.close()

        #Serveur DHCP
        fichier=open("/etc/dnsmasq.conf", "w")
        fichier.write("\n")
        fichier.close()

        #Co auto
        fichier=open("/etc/wpa_supplicant/wpa_supplicant.conf", "w")
        fichier.write("\nctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev")
        fichier.write("\nupdate_config=1")
        fichier.write("\ncountry=FR")
        fichier.close()

        #Point d'acces
        fichier=open("/etc/default/hostapd", "w")
        fichier.write("# Defaults for hostapd initscript")
        fichier.write('#\nDAEMON_CONF="/etc/hostapd/hostapd_BienEntendu.conf"')
        fichier.close()

        fichier=open("/etc/hostapd/hostapd_BienEntendu.conf", "w")
        fichier.write('\ninterface=wlan0')
        fichier.write("\nbridge=br0")
        fichier.write('\ndriver=nl80211')
        fichier.write('\ncountry_code=FR')
        fichier.write('\nssid=BienEntendu')
        fichier.write('\nhw_mode=g')
        fichier.write('\nchannel=6')
        fichier.write('\nwpa=2')
        fichier.write('\nwpa_passphrase=mezule08')
        fichier.write("\nwpa_key_mgmt=WPA-PSK")
        fichier.write("\nwpa_pairwise=CCMP")
        fichier.write("\nrsn_pairwise=CCMP")
        fichier.close()

        #Demarrage des services qu'on veut
        subprocess.call(['sudo', 'systemctl','start','dhcpcd.service'], stdin=None, stdout=None, stderr=None, shell=False)
        subprocess.call(['sudo', 'brctl','addbr','br0'], stdin=None, stdout=None, stderr=None, shell=False)
        subprocess.call(['sudo', 'brctl','addif','br0','eth0'], stdin=None, stdout=None, stderr=None, shell=False)
        subprocess.call(['sudo', 'systemctl','start','hostapd.service'], stdin=None, stdout=None, stderr=None, shell=False)
        subprocess.call(['sudo', 'systemctl','start','dnsmasq.service'], stdin=None, stdout=None, stderr=None, shell=False)
        subprocess.call(['sudo', 'systemctl','start','shairport.service'], stdin=None, stdout=None, stderr=None, shell=False)

        tmp=3

    return tmp


#def display(a,b):
#    if a == False:
#        tmp_ip=2
#    else:
#        tmp_ip=0
#    if b == False:
#        tmp_bridge=4
#    else:
#        tmp_bridge=0
#    return tmp_bridge+tmp_ip

#Recuperation des addreses IP
def estActive(ifname):
    try:
        fichier=open("/sys/class/net/"+ifname+"/operstate","r")
        if fichier.read(2) == "up":
            tmp_act=True
        else:
            tmp_act=False
   
        fichier.close()

    except IOError:
        tmp_act=False
    
    return tmp_act


def get_ip_address(ifname):
    a = netifaces.ifaddresses(ifname)
    try:
        return a[netifaces.AF_INET][0].get('addr')
    except IOError:
        return 0
    except KeyError:
        return 0

#Daemon thread qui s'occupera du clignotement de la led
def blink():
    my_logger=logging.getLogger('GardienBienEntendu')
    my_logger.debug('LANCEMENT DE LA LED DE SECURITE')

    global etat
    while True:
        #Demarrage du systeme
        #if etat.empty():
        #    print("demarrage op")
        #    GPIO.output(17,1)
        #    time.sleep(0.5)
        #    GPIO.output(17,0)
        #    time.sleep(0.5)
        #Tout va bien
        #Petit probleme poto
    #print "le second etat",etat
        if etat == False :
            #print("ou par la")
            GPIO.output(17,1)
            time.sleep(1)
            GPIO.output(17,0)
            time.sleep(1)
        else:
            GPIO.output(17,1)
            time.sleep(1)

#Check l'internet
def internetActif():
    try:
        subprocess.check_call(["ping","-c","1","-n","-W","2","8.8.8.8"],stdin=None,stdout=None,stderr=None,shell=False)
        return True
    except subprocess.CalledProcessError:
        return False


#Grand gardien du systeme, indication de la stabilité en résumé
def secuLed(x):
    global etat

    my_logger=logging.getLogger('GardienBienEntendu')    
    my_logger.debug('VERIFICATION DE LA STABILITE LANCE')
    while True:
        tmp_etat=True
        #print tmp_etat

        #S'il s'agit de la position serveur prive
        if x==1:
            #Bonne IP?
            if (get_ip_address('br0') != '192.168.2.1' and
                get_ip_address('wlan0') != '192.168.2.1' and
                get_ip_address('eth0') != '192.168.2.3'):

                #Probleme au niveau des interfaces
                tmp_etat=False
            #Interface active?
            if (not(estActive('br0') and estActive('eth0') and estActive('wlan0'))):
                #Das gud
                tmp_etat=False

            a=subprocess.check_output(["brctl","show","br0"],stdin=None,stderr=None,shell=False).decode("utf-8")
                #Passerelle active?
            if (a.find("eth0") == -1 and a.find("wlan0") == -1):
                #Passerelle foireuse
                tmp_etat=False
        #S'il s'agit de la position client
        elif x==2:
        #Interface active?
            if (not(estActive('wlan0'))):
                #RAS
                tmp_etat=False
        #S'il s'agit de la position serveur partage
        elif x==3:
        #Interface active?
            if (not(estActive('br0') and
                estActive('wlan0') and
                estActive('eth0')) ):
                
                #RAS
                #print "il passe ici"
                tmp_etat=False
    
            #Passerelle active?
            a=subprocess.check_output(["brctl","show","br0"],stdin=None,stderr=None,shell=False).decode("utf-8")
            if (a.find("eth0") == -1 and a.find("wlan0") == -1):
                #Passerelle foireuse
                tmp_etat=False

            if (internetActif() == False):
                tmp_etat=False

        #Maintenant on resume la totalite du systeme en un booleen
        etat=tmp_etat
        
        time.sleep(CHECK)
    
def main():
    i=0
    #Creation du logger
    my_logger=logging.getLogger('GardienBienEntendu')    
    #Seuil du log. On affiche les message jusqu'au lvl debug ici
    my_logger.setLevel(level)

    #On creer notre superviseur de log
    handler=logging.handlers.RotatingFileHandler(LOG_FILENAME,maxBytes=TAILLE,backupCount=SAVE)
    #Formatteur de log
    formatter=logging.Formatter('%(asctime)s : %(name)s : %(levelname)s : %(message)s')    
    handler.setFormatter(formatter)
    my_logger.addHandler(handler)    
    #Pour interagir avec journalctl il faudra passer a python3 (a voir)

    my_logger.debug('LANCEMENT DE RASPISWITCH')

    GPIO.setmode(GPIO.BCM)
    #On configure les pins d'entrée (fil rouge et vert sur la rasp precedente)
    GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    #On ajoute la fonction de callback a chaque interruption + petit temps rebond
    GPIO.add_event_detect(22,GPIO.BOTH,bouncetime=200)
    GPIO.add_event_callback(22,switch)
    GPIO.add_event_detect(27,GPIO.BOTH,bouncetime=200)
    GPIO.add_event_callback(27,switch)

    #Parametrage de la led
    GPIO.setup(17, GPIO.OUT)

    try:
        #Initialisation du systeme au boot
        my_logger.debug('LECTURE DU MODE (Serv/Client/ServPriv)')
        position=changement()

        #recupWlan()    
        #On lance le monitoring avec la led
        prog = threading.Thread(name='daemon',target=blink)
        prog.setDaemon(True)
        #print "lancement du daemon"
        prog.start()
        #On lance le service indéfiniement avec délais pour ne pas fatiguer
        secuLed(position)               
    finally:
        #Avant de partir on nettoie les ports pour eviter des cours circuits en cas d'interruption
        GPIO.cleanup()
        my_logger.debug('ARRET NON PREVU PORT GPIO REINITIALISE')


if __name__=="__main__":
    main()

