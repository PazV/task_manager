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
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
import re

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
            server=smtplib.SMTP(cfg.mail_server,cfg.mail_port)
            server.login(cfg.mail_username,cfg.mail_password)
            from_address=cfg.mail_username
            msg=MIMEMultipart()
            msg['From']=from_address
            msg['To']=to_address
            msg['Subject']=subject.decode('utf-8')
            body=self.replaceStringHtml(body)
            msg.attach(MIMEText(body,'html'))
            text=msg.as_string()
            server.sendmail(from_address,[to_address,cfg.app_admin_mail],text)
        except:
            success=False
            exc_info=sys.exc_info()
            logger.error(traceback.format_exc(exc_info))
        return success

    def replaceStringHtml(self,text):
        rep = {
            "á":"&aacute;",
            "é":"&eacute;",
            "í":"&iacute;",
            "ó":"&oacute;",
            "ú":"&uacute;",
            "Á":"&Aacute;",
            "É":"&Eacute;",
            "Í":"&Iacute;",
            "Ó":"&Oacute;",
            "Ú":"&Uacute;",
            "ñ":"&ntilde;",
            "Ñ":"&Ntilde;"
        }
        rep = dict((re.escape(k), v) for k, v in rep.iteritems())
        pattern = re.compile("|".join(rep.keys()))
        new_text = pattern.sub(lambda m: rep[re.escape(m.group(0))], text)
        return new_text

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
                logger.info("Empezando empresa %s"%x['company_id'])
                # ASSIGNEE'S NOTIFICATIONS
                assignee_days=int(x['assignee_days'].split("_")[0])
                logger.info("assignee days %s"%assignee_days)
                assignee_date=str(now_date-timedelta(days=assignee_days))
                logger.info("assignee date %s"%assignee_date)

                company_name=db.query("""
                    select name from system.company where company_id=%s
                """%x['company_id']).dictresult()[0]

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
                    and now() between assignee_deadline - INTERVAL '%s DAYS' and assignee_deadline
                """%(x['company_id'],assignee_days)).dictresult()

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
                        pa['mail_img']=cfg.mail_img
                        pa['company']=company_name['name']
                        msg=assignee_template['body'].format(**pa)
                        MF.sendMail(recipient,assignee_template['subject'].format(**pa),msg)

                expired_tasks_assignee=db.query("""
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
                    and assignee_deadline<now()
                """%(x['company_id'])).dictresult()
                if expired_tasks_assignee!=[]:
                    exp_assignee_template=db.query("""
                        select * from template.generic_template where type_id=29
                    """).dictresult()[0]
                    for eta in expired_tasks_assignee:
                        logger.info("Tarea: %s, fecha limite auxiliar:%s"%(eta['name'],eta['assignee_deadline']))
                        recipient=db.query("""
                            select email from system.user where user_id=%s
                        """%eta['assignee_id']).dictresult()[0]['email']
                        eta['link']=cfg.host
                        eta['mail_img']=cfg.mail_img
                        eta['company']=company_name['name']
                        msg=exp_assignee_template['body'].format(**eta)
                        MF.sendMail(recipient,exp_assignee_template['subject'].format(**eta),msg)

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
                    and now() between supervisor_deadline - INTERVAL '%s DAYS' and supervisor_deadline
                """%(x['company_id'],supervisor_days)).dictresult()

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
                        ps['mail_img']=cfg.mail_img
                        ps['company']=company_name['name']
                        msg=supervisor_template['body'].format(**ps)
                        MF.sendMail(recipient,supervisor_template['subject'].format(**ps),msg)

                expired_tasks_supervisor=db.query("""
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
                    and supervisor_deadline<now()
                """%(x['company_id'])).dictresult()
                if expired_tasks_supervisor!=[]:
                    exp_supervisor_template=db.query("""
                        select * from template.generic_template where type_id=30
                    """).dictresult()[0]
                    for ets in expired_tasks_supervisor:
                        logger.info("Tarea: %s, fecha limite supervisor:%s"%(ets['name'],ets['supervisor_deadline']))
                        recipient=db.query("""
                            select email from system.user where user_id=%s
                        """%ets['supervisor_id']).dictresult()[0]['email']
                        ets['link']=cfg.host
                        ets['mail_img']=cfg.mail_img
                        ets['company']=company_name['name']
                        msg=exp_supervisor_template['body'].format(**ets)
                        MF.sendMail(recipient,exp_supervisor_template['subject'].format(**ets),msg)

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
                    and now() between deadline - INTERVAL '%s DAYS' and deadline
                """%(x['company_id'],admin_days)).dictresult()

                if pending_tasks_admin!=[]:
                    admin_template=db.query("""
                        select * from template.generic_template where type_id=15
                    """).dictresult()[0]
                    for pad in pending_tasks_admin:
                        logger.info("Tarea: %s, fecha limite administrador:%s"%(pad['name'],pad['deadline']))
                        recipient=db.query("""
                            select email from system.user where company_id=%s and user_type_id in (1,6)
                        """%x['company_id']).dictresult()[0]['email']
                        pad['link']=cfg.host
                        pad['mail_img']=cfg.mail_img
                        pad['company']=company_name['name']
                        msg=admin_template['body'].format(**pad)
                        MF.sendMail(recipient,admin_template['subject'].format(**pad),msg)

                expired_tasks_admin=db.query("""
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
                    and deadline<now()
                """%(x['company_id'])).dictresult()

                if expired_tasks_admin!=[]:
                    exp_admin_template=db.query("""
                        select * from template.generic_template where type_id=31
                    """).dictresult()[0]
                    for etad in expired_tasks_admin:
                        logger.info("Tarea: %s, fecha limite administrador:%s"%(etad['name'],etad['deadline']))
                        recipient=db.query("""
                            select email from system.user where company_id=%s and user_type_id in (1,6)
                        """%x['company_id']).dictresult()[0]['email']
                        etad['link']=cfg.host
                        etad['mail_img']=cfg.mail_img
                        etad['company']=company_name['name']
                        msg=exp_admin_template['body'].format(**etad)
                        MF.sendMail(recipient,exp_admin_template['subject'].format(**etad),msg)



        logger.info(notif_list)
    except:
        exc_info = sys.exc_info()
        logger.error(traceback.format_exc(exc_info))

if __name__ == '__main__':
    main()


print "Termina cron"
