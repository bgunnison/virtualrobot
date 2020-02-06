"""
 Copyright (C) 2020 Brian R. Gunnison
 
 This file is part of MIDI project
 
 MIDI can not be copied and/or distributed without the express
 permission of Brian R. Gunnison

 https://build-system.fman.io/generating-license-keys
"""
import rsa # pip install rsa
from base64 import b64encode
import argparse
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

#in the application, but also here totest. 
class License:
    def __init__(self):
        self.valid = False

    def verify(self, email, signature, pubkey= None, settings=None):
        if settings is not None:
            pubkey = settings.get('VirtualRobotPublicKey', '')

        try:
            rsa.verify(email.encode('utf-8'), signature, pubkey)
        except rsa.VerificationError:
            log.error(f'Invalid key: {email}')
            return

        log.info(f'Valid key: {email}')
        self.valid = True

    def is_valid(self):
        return self.valid


class Keys:
    def __init__(self):
        pass


    def gen(self):
        snow = datetime.now()
        dt = snow.strftime("%m_%d_%Y_%H_%M_%S")
        self.priv_file = f'VirtualRobotPrivateKey{dt}.pem'
        self.pub_file = f'VirtualRobotPublicKey{dt}.pem'

        pubkey, privkey = rsa.newkeys(2048)
        pub = pubkey.save_pkcs1().decode('ascii')
        pri = privkey.save_pkcs1().decode('ascii')
        
        f = open(self.priv_file, 'w')
        f.write(pri)
        f.close()
        f = open(self.pub_file, 'w')
        f.write(pub)
        f.close()

        print(f'{pub}')
        print(f'')
        print(f'{pri}')


    def load_priv_key(name):
        with open(name, mode='rb') as privatefile:
            keydata = privatefile.read()
        return rsa.PrivateKey.load_pkcs1(keydata)


    def load_pub_key(name):
        with open(name, mode='rb') as pubfile:
            keydata = pubfile.read()
        return rsa.PublicKey.load_pkcs1(keydata)

    def sign(Self, message, privkey):
        signature = rsa.sign(mesage.encode('utf-8'), privkey, 'SHA-1')
        l = b64encode(signature).decode('ascii')
        print(data + '\n' + l)
        return l



def test_keys():

    log.info('Virtual Robot License generator, do not distribute')

    ap = argparse.ArgumentParser(argparse.SUPPRESS)
    ap.add_argument("-e", "--email", required=True, help="email of user")
    ap.add_argument("-v", "--privkeyfile", required=True, help="private key file")
    ap.add_argument("-p", "--pubkeyfile", required=True, help="public key file")
    args = vars(ap.parse_args())

    if '@' not in args['email']:
        log.error(f'No @ in email: {args["email"]}')
        return 

    k = Keys()

    k.gen()

    if args['privkeyfile'] == None:
        privkf = k.priv_file

    if args['pubkeyfile'] == None:
        pubkf = k.pub_file



    sig = k.sign(args['email'], k.load_priv_key(privkf))

    l = License()
    l.verify(args['email'], l, k.load_pub_key(pubkf))



if __name__ == '__main__':
   test_keys()

