import json
import logging

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.exceptions import InvalidSignature

from setup_logger import logger
from block import Block

# Set logger to name of class
logger = logging.getLogger('Transaction')


class Transaction:
    """Class to represent a transaction"""

    def __init__(self, fromAddr, toAddr, ammount):
        """Initialise transaction data"""
        self.fromAddr = fromAddr
        self.toAddr = toAddr
        self.ammount = ammount

        logger.debug(f"Transaction declared: {self.calculateHash()}")

    def __str__(self):
        """Output transaction in human readable format"""
        return f"Ammount: {self.ammount} From: {self.fromAddr} To: {self.toAddr}"

    def toJson(self):
        """Output transaction in human readable JSON format"""
        tx = {
            "From": self.fromAddr,
            "To": self.toAddr,
            "Ammount": self.ammount
        }

        return json.dumps(tx, indent=4)

    def calculateHash(self):
        """Create a sha256 hash of the transaction for use when signing"""
        digest = hashes.Hash(hashes.SHA256())
        digest.update(bytes(str(self), 'utf-8'))

        return digest.finalize()

    def signTransaction(self, signingKey):
        """Digitally sign sha256 hash of transaction with ECDSA"""

        # Verify that the from address is the public signing key
        # i.e. the person sending is the person signing
        if signingKey.public_key().public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo) != self.fromAddr:
            raise Exception("You cannot sign transactions for other people")

        # reate hash of the transaction
        txHash = self.calculateHash()
        logging.debug(f"{self.fromAddr.decode()} attmptng to sign {txHash}")

        # Sign the hash
        self.signature = signingKey.sign(txHash, ec.ECDSA(hashes.SHA256()))
        logging.debug(f"Signature created: {self.signature}")

    def isValid(self):
        """
        Check a single transaction is valid
        Checking for signature presence, and validlity 
        Key used for verification is the senders public key/ address
        """
        logging.debug(f"Making sure transaction is valid")

        # Special case: mining reward
        if self.fromAddr == None:
            logging.debug(f"No from address, assuming mining reward tx")
            return True

        # If tx is not signed
        if not self.signature or len(self.signature) == 0:
            logging.debug(
                f"Signature: {self.signature} len: {len(self.signature)}")
            raise Exception("Transaction needs to be signed")

        # Verify signature
        # Generate public key from address
        key = serialization.load_pem_public_key(self.fromAddr)
        logging.debug(f"Created key from address")

        try:
            key.verify(self.signature, self.calculateHash(),
                       ec.ECDSA(hashes.SHA256()))
            logging.debug(f"Signature valid")
            return True
        except InvalidSignature:
            print("Signature verifcation failed")
        except:
            print("Somthing went wrong...")

        logging.warning(
            f"There was an issue with transaction validation for {str(self)}")
        return False
