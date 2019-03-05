import hashlib
import random
import math

from urllib3.connectionpool import xrange

message = "Hola te voy a ingresar una milloná" #Mensaje mandado
hash = "" #Poner en Hexadecimal
bits = 32 #Número de bits de la clave
#Se usa sha256, si se cree que se usa otro cambiar el código


def getKey1():
    """ Pasa la clave a binario y luego calcula el hashing"""
    print("PRUEBA AL MENSAJE: " + message)
    print("CON EL HASH: " + hash)

    combinations = pow(2, bits)
    rango = xrange(combinations)
    i = 0
    while (i < combinations):

        posibleKey = str(format(random.sample(rango, 1)[0], "b"))
        print("Probando con: " + posibleKey)

        if hashlib.sha256((message + posibleKey).encode()).hexdigest() == hash or hashlib.sha256(
                (posibleKey + message).encode()).hexdigest() == hash:
            return "KEY: " + str(posibleKey)

        i += 1
    return "NotFounded"


def getKey2():
    """calcula el hashing sin pasar la clave a binario"""
    print("PRUEBA AL MENSAJE: " + message)
    print("CON EL HASH: " + hash)

    combinations = pow(2, bits)
    rango = xrange(combinations)
    i = 0
    while (i < combinations):

        posibleKey = str(random.sample(rango, 1)[0])
        print("Probando con: " + posibleKey)

        if hashlib.sha256((message + posibleKey).encode()).hexdigest() == hash or hashlib.sha256(
                (posibleKey + message).encode()).hexdigest() == hash:
            return "KEY: " + str(posibleKey)
        i += 1

    return "NotFounded"


def getKey3():
    """ Pasa la clave a binario complentando con 0 y luego calcula el hashing"""
    print("PRUEBA AL MENSAJE: " + message)
    print("CON EL HASH: " + hash)

    combinations = pow(2, bits)
    rango = xrange(combinations)
    i = 0
    while (i < combinations):

        posibleKey = str(format(random.sample(rango, 1)[0], "032b"))
        print("Probando con: " + posibleKey)

        if hashlib.sha256((message + posibleKey).encode()).hexdigest() == hash or hashlib.sha256(
                (posibleKey + message).encode()).hexdigest() == hash:
            return "KEY: " + str(posibleKey)

        i += 1
    return "NotFounded"


if __name__ == '__main__':
    getKey1()
