#!/usr/bin/env python
#--*-- coding: utf-8 --*--
from db_connection import getDB
db = getDB()
import generic_functions
GF=generic_functions.GenericFunctions()
import logging
import app_config as cfg
import sys
import traceback
from datetime import datetime, timedelta

print "Entra check session"
# create logger with 'spam_application'
logger = logging.getLogger('Send Notif')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('%scron_check_session.log'%cfg.log_path)
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
if not len(logger.handlers):
    logger.addHandler(fh)
    logger.addHandler(ch)

logger.info("Log info")

def main():
    try:
        open_sessions=db.query("""
            select
                session_id,
                to_char(last_action_at,'YYYY-MM-DD HH24:MI:SS') as last_action_at
            from system.user_session
            where logged=True
        """).dictresult()
        if open_sessions!=[]:
            now=datetime.now()
            for x in open_sessions:
                # without_milisec=x['last_action_at'].split(".")[0]
                compare=datetime.strptime(x['last_action_at'],"%Y-%m-%d %H:%M:%S")
                if now-compare>timedelta(minutes=60):
                    db.query("""
                        update system.user_session
                        set logged=False,
                        finish_session=now()
                        where session_id=%s
                    """%x['session_id'])
                    logger.info("cierra sesión %s"%x['session_id'])


    except:
        exc_info = sys.exc_info()
        logger.error(traceback.format_exc(exc_info))

if __name__ == '__main__':
    main()
