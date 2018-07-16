#!/usr/bin/env python

from db_connection import getDB
db = getDB()
import generic_functions
GF=generic_functions.GenericFunctions()
import logging
import app_config as cfg
import sys
import traceback
from datetime import datetime, timedelta
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

print "Entra cron"
# create logger with 'spam_application'
logger = logging.getLogger('Send Notif')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('%scron_send_notif.log'%cfg.log_path)
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

class MailFunctions:
    def sendMail(self,to_address,subject,body):
        success=True
        try:
            server=smtplib.SMTP('smtpparla.spamina.com',587)
            server.login("pgarcia@russellbedford.mx","d2hC4qFFxq")
            from_address="pgarcia@russellbedford.mx"
            # to_address="pgarcia@russellbedford.mx"
            msg=MIMEMultipart()
            msg['From']=from_address
            msg['To']=to_address
            msg['Subject']=subject.decode('utf-8')
            msg.attach(MIMEText(body,'html'))
            text=msg.as_string()
            server.sendmail(from_address,to_address,text)
        except:
            success=False
            exc_info=sys.exc_info()
            logger.error(traceback.format_exc(exc_info))
        return success

def main():
    try:
        MF=MailFunctions()
        now_date=datetime.now()
        now_str=str(now_date).split(" ")[0]

        notif_list=db.query("""
            select *,
            to_char(last_admin_notification,'DD-MM-YYYY HH24:MI:SS') as last_admin_notification
            from system.notification_settings
        """).dictresult()
        if notif_list!=[]:
            for x in notif_list:
                # ASSIGNEE'S NOTIFICATIONS
                assignee_days=int(x['assignee_days'].split("_")[0])
                logger.info("assignee days %s"%assignee_days)
                assignee_date=str(now_date-timedelta(days=assignee_days))
                logger.info("assignee date %s"%assignee_date)

                pending_tasks_assignee=db.query("""
                    select
                        task_id,
                        name,
                        description,
                        assignee_id,
                        to_char(assignee_deadline, 'DD-MM-YYYY HH24:MI:SS') as assignee_deadline,
                        (select a.name from system.user a where a.user_id=assignee_id) as assignee,
                        (select a.name from system.user a where a.user_id=supervisor_id) as supervisor
                    from task.task
                    where status_id in (1,6)
                    and company_id=%s
                    and assignee_deadline between '%s 00:00:00' and '%s 23:59:59'
                """%(x['company_id'],assignee_date.split(" ")[0],now_str)).dictresult()
                
                if pending_tasks_assignee!=[]:
                    assignee_template=db.query("""
                        select * from template.generic_template where type_id=13
                    """).dictresult()[0]
                    for pa in pending_tasks_assignee:
                        logger.info("Tarea: %s, fecha limite auxiliar:%s"%(pa['name'],pa['assignee_deadline']))
                        recipient=db.query("""
                            select email from system.user where user_id=%s
                        """%pa['assignee_id']).dictresult()[0]['email']
                        pa['link']=cfg.host
                        msg=assignee_template['body'].format(**pa)
                        MF.sendMail(recipient,assignee_template['subject'],msg)

                #SUPERVISOR'S NOTIFICATIONS
                supervisor_days=int(x['supervisor_days'].split("_")[0])
                logger.info("supervisor days %s"%supervisor_days)
                supervisor_date=str(now_date-timedelta(days=supervisor_days))
                logger.info("supervisor date %s"%supervisor_date)
                pending_tasks_supervisor=db.query("""
                    select
                        task_id,
                        name,
                        description,
                        supervisor_id,
                        to_char(assignee_deadline, 'DD-MM-YYYY HH24:MI:SS') as assignee_deadline,
                        to_char(supervisor_deadline, 'DD-MM-YYYY HH24:MI:SS') as supervisor_deadline,
                        (select a.name from system.user a where a.user_id=assignee_id) as assignee,
                        (select a.name from system.user a where a.user_id=supervisor_id) as supervisor
                    from task.task
                    where status_id in (1,6)
                    and company_id=%s
                    and supervisor_deadline between '%s 00:00:00' and '%s 23:59:59'
                """%(x['company_id'],supervisor_date.split(" ")[0],now_str)).dictresult()

                if pending_tasks_supervisor!=[]:
                    supervisor_template=db.query("""
                        select * from template.generic_template where type_id=14
                    """).dictresult()[0]
                    for ps in pending_tasks_supervisor:
                        logger.info("Tarea: %s, fecha limite supervisor:%s"%(ps['name'],ps['supervisor_deadline']))
                        recipient=db.query("""
                            select email from system.user where user_id=%s
                        """%ps['supervisor_id']).dictresult()[0]['email']
                        ps['link']=cfg.host
                        msg=supervisor_template['body'].format(**ps)
                        MF.sendMail(recipient,supervisor_template['subject'],msg)

                #ADMIN NOTIFICATIONS
                admin_days=int(x['admin_days'].split("_")[0])
                logger.info("admin days %s"%admin_days)
                admin_date=str(now_date-timedelta(days=admin_days))
                logger.info("admin date %s"%admin_date)
                pending_tasks_admin=db.query("""
                    select
                        task_id,
                        name,
                        description,
                        to_char(assignee_deadline, 'DD-MM-YYYY HH24:MI:SS') as assignee_deadline,
                        to_char(supervisor_deadline, 'DD-MM-YYYY HH24:MI:SS') as supervisor_deadline,
                        to_char(deadline, 'DD-MM-YYYY HH24:MI:SS') as deadline,
                        (select a.name from system.user a where a.user_id=assignee_id) as assignee,
                        (select a.name from system.user a where a.user_id=supervisor_id) as supervisor
                    from task.task
                    where status_id in (1,6)
                    and company_id=%s
                    and deadline between '%s 00:00:00' and '%s 23:59:59'
                """%(x['company_id'],admin_date.split(" ")[0],now_str)).dictresult()

                if pending_tasks_admin!=[]:
                    admin_template=db.query("""
                        select * from template.generic_template where type_id=15
                    """).dictresult()[0]
                    for pad in pending_tasks_admin:
                        logger.info("Tarea: %s, fecha limite administrador:%s"%(pad['name'],pad['deadline']))
                        recipient=db.query("""
                            select email from system.user where company_id=%s and user_type_id=1
                        """%x['company_id']).dictresult()[0]['email']
                        pad['link']=cfg.host
                        msg=admin_template['body'].format(**pad)
                        MF.sendMail(recipient,admin_template['subject'],msg)



                logger.info("pending tasks assigne")
                logger.info(pending_tasks_assignee)


        logger.info(notif_list)
    except:
        exc_info = sys.exc_info()
        logger.error(traceback.format_exc(exc_info))

if __name__ == '__main__':
    main()


print "Termina cron"