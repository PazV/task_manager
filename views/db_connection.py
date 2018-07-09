#-*- coding: utf-8 -*-

from pg import DB

def getDB():
    db=DB(dbname='test',user='postgres',passwd='zedberto')
    return db
