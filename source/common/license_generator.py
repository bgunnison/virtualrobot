"""
 Copyright (C) 2020 Brian R. Gunnison
 
 This file is part of MIDI project
 
 MIDI can not be copied and/or distributed without the express
 permission of Brian R. Gunnison

 https://build-system.fman.io/generating-license-keys
"""
import rsa # pip install rsa
import argparse
import logging


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

#in the application, but also here totest. 
class license:
    def __init__(self, settings, email, signature):

        self.valid = False
        pubkey = settings.get('SpecialData', '')
        try:
            rsa.verify(email.encode('utf-8'), signature, pubkey)
        except rsa.VerificationError:
            log.error(f'Invalid key: {email}')
            return

        log.info(f'Valid key: {email}')
        self.valid = True

    def is_valid(self):
        return self.valid

def gen_keys():
    pubkey, privkey = rsa.newkeys(2048)
    print(f'{pubkey}')
    print(f'')
    print(f'{privkey}')




def gen_pub_key():

    log.info('Virtual Robot License generator, do not distribute')

    ap = argparse.ArgumentParser()
    ap.add_argument("-e", "--email", required=True, help="email of user")
    ap.add_argument("-p", "--privkeyfile", required=True, help="private key file")
    args = vars(ap.parse_args())

    if '@' not in args['email']:
        log.error(f'No @ in email: {args["email"]}')
        return 

    try:
        privkey = open(args['privkeyfile'], 'r').read() 
    except:
        log.error('Cannot open private key file: {args["privkeyfile"]}')
        return

    # input email and priv key file (somewhere hidden on computer)
    data = args['email']
    signature = rsa.sign(data.encode('utf-8'), privkey, 'SHA-1')
    from base64 import b64encode
    print(data + '\n' + b64encode(signature).decode('ascii'))


 
# construct the argument parse and parse the arguments

if __name__ == '__main__':
    gen_keys()
    gen_pub_key()

