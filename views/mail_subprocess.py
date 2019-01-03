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

print "Entra mail subprocess"
# create logger with 'spam_application'
logger = logging.getLogger('Mail Subprocess')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('%smail_subprocess.log'%cfg.log_path)
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
        #el argv[0] corresponde a la ruta del archivo subproceso
        tasks_list=eval(sys.argv[1])
        company_id=int(sys.argv[2])

        company=db.query("""
            select name from system.company where company_id=%s
        """%company_id).dictresult()[0]['name']
        template=db.query("""
            select * from template.generic_template where type_id=24
        """).dictresult()[0]
        admin=db.query("""
            select name, user_id, email from system.user where company_id=%s and user_type_id in (1,6)
        """%company_id).dictresult()[0]

        for x in tasks_list:
            task_info=db.query("""
                select
                    (select name from system.user where user_id=a.supervisor_id) as supervisor,
                    a.name,
                    (select name from system.user where user_id=a.assignee_id) as assignee,
                    a.description,
                    to_char(a.assignee_deadline,'DD-MM-YYYY HH24:MI:SS') as assignee_deadline,
                    to_char(a.supervisor_deadline,'DD-MM-YYYY HH24:MI:SS') as supervisor_deadline,
                    to_char(a.deadline, 'DD-MM-YYYY HH24:MI:SS') as deadline,
                    notify_admin,
                    supervisor_id,
                    assignee_id
                from
                    task.task a
                where a.task_id=%s
            """%x).dictresult()[0]
            task_info['company']=company
            task_info['link']=cfg.host
            task_info['mail_img']=cfg.mail_img

            msg=template['body'].format(**task_info)
            recipients=db.query("""
                select email from system.user where user_id in (%s,%s) and company_id=%s
            """%(task_info['supervisor_id'],task_info['assignee_id'],company_id)).dictresult()
            if task_info['notify_admin']=='t':
                if int(task_info['supervisor_id'])!=int(admin['user_id']):
                    recipients.append({'email':admin['email']})
            mail_recipients=[]
            for r in recipients:
                mail_recipients.append(r['email'])
            GF.sendMail(template['subject'].format(**task_info),msg,mail_recipients)

            logger.info("Envía correo tarea: {name}".format(**task_info))

        logger.info("Termina subproceso")


    except:
        exc_info = sys.exc_info()
        logger.error(traceback.format_exc(exc_info))

if __name__ == '__main__':
    main()
