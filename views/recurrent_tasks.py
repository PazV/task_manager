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
import datetime
from dateutil.relativedelta import relativedelta
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
import re


print "Entra recurrent tasks"
# create logger with 'spam_application'
logger = logging.getLogger('Send Notif')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('%scron_rec_tasks.log'%cfg.log_path)
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

class DateFunctions:
    def getDaysDiff(self,created,other_date,new_created):
        try:
            success=True
            logger.info("dod %s"%other_date)
            logger.info("dc %s"%created)
            dod=datetime.date(int(other_date.split("-")[2]),int(other_date.split("-")[1]),int(other_date.split("-")[0]))
            dc=datetime.date(int(created.split("-")[2]),int(created.split("-")[1]),int(created.split("-")[0]))
            ndc=datetime.date(int(new_created.split("-")[2]),int(new_created.split("-")[1]),int(new_created.split("-")[0]))
            days=(dod-dc).days
            new_dd=ndc+datetime.timedelta(days=days)
            new_date=new_dd.strftime("%Y-%m-%d")
        except:
            success=False
            new_date=""
            exc_info=sys.exc_info()
            logger.error(traceback.format_exc(exc_info))
        return success, new_date

    def sendMail(self,to_address,subject,body):
        success=True
        try:
            server=smtplib.SMTP(cfg.mail_server,cfg.mail_port)
            server.login(cfg.mail_username,cfg.mail_password)
            from_address=cfg.mail_username
            # to_address="pgarcia@russellbedford.mx"
            msg=MIMEMultipart()
            msg['From']=from_address
            msg['To']=to_address
            msg['Subject']=subject.decode('utf-8')
            body=self.replaceStringHtml(body)
            msg.attach(MIMEText(body,'html'))
            text=msg.as_string()
            server.sendmail(from_address,to_address,text)
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
        DF=DateFunctions()
        companies=db.query("""
            select company_id,name from system.company where company_id=3
        """).dictresult()

        today=datetime.date.today().strftime("%d-%m-%Y")

        assignee_template=db.query("""
            select * from template.generic_template where type_id=1
        """).dictresult()[0]

        supervisor_template=db.query("""
            select * from template.generic_template where type_id=18
        """).dictresult()[0]

        created_tasks=""
        task_error=""
        for c in companies:
            created_tasks+="Empresa company_id: %s - %s : \n"%(c['company_id'],c['name'])
            task_error+="Empresa company_id: %s - %s : \n"%(c['company_id'],c['name'])
            tasks=db.query("""
                select
                    task_id,
                    name,
                    description,
                    to_char(deadline, 'DD-MM-YYYY') as deadline,
                    supervisor_id,
                    to_char(supervisor_deadline, 'DD-MM-YYYY') as supervisor_deadline,
                    assignee_id,
                    to_char(assignee_deadline, 'DD-MM-YYYY') as assignee_deadline,
                    to_char(created, 'DD-MM-YYYY') as created,
                    company_id,
                    recurrent_frequency,
                    notify_admin,
                    created_by
                from
                    task.task
                where
                    --task_id=39
                    company_id=%s
                and recurrent=True
            """%c['company_id']).dictresult()
            
            if tasks!=[]:
                for x in tasks:
                    frequency=int(x['recurrent_frequency'])
                    created=datetime.date(int(x['created'].split("-")[2]),int(x['created'].split("-")[1]),int(x['created'].split("-")[0]))
                    if created+relativedelta(months=frequency)==datetime.date.today():
                        success_nd,new_deadline=DF.getDaysDiff(x['created'],x['deadline'],today)
                        if success_nd==True:
                            success_nad,new_assignee_deadline=DF.getDaysDiff(x['created'],x['assignee_deadline'],today)
                            if success_nad==True:
                                success_nsd,new_supervisor_deadline=DF.getDaysDiff(x['created'],x['supervisor_deadline'],today)
                                if success_nsd==True:
                                    new_task={
                                        'name':x['name'],
                                        'description':x['description'],
                                        'deadline':new_deadline,
                                        'supervisor_id':x['supervisor_id'],
                                        'supervisor_deadline':new_supervisor_deadline,
                                        'assignee_id':x['assignee_id'],
                                        'assignee_deadline':new_assignee_deadline,
                                        'created':'now',
                                        'company_id':x['company_id'],
                                        'recurrent':True,
                                        'recurrent_frequency':x['recurrent_frequency'],
                                        'notify_admin':x['notify_admin'],
                                        'status_id':1,
                                        'created_by':x['created_by'],
                                        'user_last_updated':x['created_by'],
                                        'last_updated':'now'
                                    }
                                    insert_new_task=db.insert('task.task',new_task)
                                    assignee=db.query("""
                                        select
                                            name,email from system.user where user_id=%s
                                    """%x['assignee_id']).dictresult()[0]
                                    supervisor=db.query("""
                                        select
                                            name,email from system.user where user_id=%s
                                    """%x['supervisor_id']).dictresult()[0]
                                    new_task['link']=cfg.host
                                    new_task['assignee']=assignee['name']
                                    new_task['supervisor']=supervisor['name']
                                    assignee_msg=assignee_template['body'].format(**new_task)
                                    DF.sendMail(assignee['email'],'Tarea nueva',assignee_msg)
                                    supervisor_msg=supervisor_template['body'].format(**new_task)
                                    DF.sendMail(supervisor['email'],'Tarea nueva',supervisor_msg)

                                    db.query("""
                                        update task.task set recurrent=False where task_id=%s
                                    """%x['task_id'])


                                    logger.info("Se crea la tarea task_id %s '%s'"%(insert_new_task['task_id'],insert_new_task['name']))
                                    created_tasks+="Se crea la tarea task_id %s '%s'\n"%(insert_new_task['task_id'],insert_new_task['name'])

                                else:
                                    logger.error("Ocurrió un error al intentar obtener la fecha límite del supervisor de la tarea task_id: %s"%x['task_id'])
                                    task_error+="Ocurrió un error al intentar obtener la fecha límite del supervisor de la tarea task_id: %s \n"%x['task_id']
                            else:
                                logger.error("Ocurrió un error al intentar obtener la fecha límite de auxiliar de la tarea task_id: %s"%x['task_id'])
                                task_error+="Ocurrió un error al intentar obtener la fecha límite de auxiliar de la tarea task_id: %s \n"%x['task_id']
                        else:
                            logger.error("Ocurrió un error al intentar obtener la fecha límite de la tarea task_id: %s"%x['task_id'])
                            task_error+="Ocurrió un error al intentar obtener la fecha límite de la tarea task_id: %s \n"%x['task_id']

                DF.sendMail(cfg.app_admin_mail,'Tareas recurrentes creadas',created_tasks)
                DF.sendMail(cfg.app_admin_mail,'Tareas recurrentes con error',task_error)

        logger.info("Termina recurrent tasks")

    except:
        exc_info = sys.exc_info()
        logger.error(traceback.format_exc(exc_info))

if __name__ == '__main__':
    main()
