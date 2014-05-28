import os
import random
import struct
from io import BytesIO
from Crypto.Cipher import AES
from modoboa.lib import parameters
from modoboa.lib.exceptions import ModoboaException


def init_storage_dir():
    storage_dir = parameters.get_admin("STORAGE_DIR")
    if os.path.exists(storage_dir):
        return
    try:
        os.mkdir(storage_dir)
    except IOError, e:
        raise ModoboaException(
            _("Failed to create the directory that will contains PDF documents (%s)" % e)
        )


def get_creds_filename(account):
    storage_dir = parameters.get_admin("STORAGE_DIR")
    return os.path.join(storage_dir, account.username + ".pdf")


def delete_credentials(account):
    fname = get_creds_filename(account)
    if not os.path.exists(fname):
        return
    try:
        os.remove(fname)
    except OSError, e:
        pass


def crypt_and_save_to_file(content, filename, length, chunksize=64*1024):
    key = parameters.get_admin("SECRET_KEY", app="admin")
    iv = ''.join(chr(random.randint(0, 0xFF)) for i in range(16))
    encryptor = AES.new(key, AES.MODE_CBC, iv)
    with open(filename, 'wb') as fp:
        fp.write(struct.pack('<Q', length))
        fp.write(iv)
        while True:
            chunk = content.read(chunksize)
            if not len(chunk):
                break
            elif len(chunk) % 16:
                chunk += ' ' * (16 - len(chunk) % 16)
            fp.write(encryptor.encrypt(chunk))


def decrypt_file(filename, chunksize=24*1024):
    buff = BytesIO()
    key = parameters.get_admin("SECRET_KEY", app="admin")
    with open(filename, 'rb') as fp:
        origsize = struct.unpack('<Q', fp.read(struct.calcsize('Q')))[0]
        iv = fp.read(16)
        decryptor = AES.new(key, AES.MODE_CBC, iv)
        while True:
            chunk = fp.read(chunksize)
            if not len(chunk):
                break
            buff.write(decryptor.decrypt(chunk))
        buff.truncate(origsize)
    return buff.getvalue()
