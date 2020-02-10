"""
 Copyright (C) 2020 Brian R. Gunnison
 
 This file is part of MIDI project
 
 MIDI can not be copied and/or distributed without the express
 permission of Brian R. Gunnison

 https://build-system.fman.io/generating-license-keys
"""
import os
import sys
import rsa # pip install rsa
from base64 import b64encode, b64decode                                         
import argparse
import logging
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from common.license import License

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class Keys:
    def __init__(self):
        pass


    def gen(self, product):
        snow = datetime.now()
        dt = snow.strftime("%m_%d_%Y_%H_%M_%S")
        self.priv_file = f'VirtualRobot{product}PrivateKey_{dt}.pem'
        self.pub_file = f'VirtualRobot{product}PublicKey_{dt}.pem'

        pubkey, privkey = rsa.newkeys(512)
        pub = pubkey.save_pkcs1().decode('ascii')
        pri = privkey.save_pkcs1().decode('ascii')
        
        f = open(self.priv_file, 'w')
        f.write(pri)
        log.info(f'Saved private key to file: {os.path.realpath(f.name)}\n')
        f.close()
        f = open(self.pub_file, 'w')
        f.write(pub)
        log.info(f'Saved public key to file: {os.path.realpath(f.name)}\n')
        f.close()


        print(f'{pub}\n')
        print(f'')
        print(f'{pri}\n')


    def load_priv_key(self, name):
        with open(name, mode='rb') as privatefile:
            keydata = privatefile.read()
        return rsa.PrivateKey.load_pkcs1(keydata)


    def load_pub_key(self, name):
        with open(name, mode='rb') as pubfile:
            keydata = pubfile.read()
        return rsa.PublicKey.load_pkcs1(keydata)

    def sign(self, message, privkey):
        signature = rsa.sign(message.encode('utf-8'), privkey, 'SHA-1')
        l = b64encode(signature).decode('ascii')
        print(f'{message}\n')
        print(f'{l}\n')
        return l



def test_keys():

    log.info('Virtual Robot License generator, do not distribute\n')

    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--newkeys", help="generate new key files", nargs='?', default=None)
    ap.add_argument("-v", "--version", help="product version", nargs='?', default='0.1')
    ap.add_argument("-k", "--product", help="product name", nargs='?', default='generic')
    ap.add_argument("-e", "--email", help="email of user", nargs='?', default='fred@boogie.com')
    ap.add_argument("-l", "--privkeyfile", help="private key file", nargs='?', default=None)
    ap.add_argument("-p", "--pubkeyfile", help="public key file", nargs='?', default=None)
    args = ap.parse_args()

    email = args.email

    if '@' not in email:
        log.error(f'No @ in email: {args["email"]}')
        return 

    if args.newkeys is not None:
        k = Keys()
        k.gen(args.product)
        privkf = k.priv_file
        pubkf = k.pub_file
    else:
        privkf = args.privkeyfile
        pubkf = args.pubkeyfile

    serial = 1435  # use a shelve todo database of emails and serial #s (start big so we look like large sales ;)
    message = f'VirtualRobot {args.product} Version: {args.version} SN: {serial} - ' + email
    sig = k.sign(message, k.load_priv_key(privkf))

    l = License()
    l.verify(message, sig, k.load_pub_key(pubkf))



if __name__ == '__main__':
   test_keys()

