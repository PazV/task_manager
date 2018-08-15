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
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
import re
from openpyxl import Workbook


print "Entra do admin report"
# create logger with 'spam_application'
logger = logging.getLogger('Send Notif')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('%scron_admin_report.log'%cfg.log_path)
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
        MF=MailFunctions()
        today=date.today()
        admins=db.query("""
            select
                user_id,
                name,
                company_id,
                email
            from
                system.user
            where
                user_type_id=1
            and enabled in (1,3)
        """).dictresult()
        for a in admins:
            notif_settings=db.query("""
                select
                    admin_report_frequency,
                    to_char(last_admin_notification,'YYYY-MM-DD') as last_admin_notification
                from system.notification_settings
                where company_id=%s
            """%a['company_id']).dictresult()
            do_report=False
            if notif_settings!=[]:
                frequency=notif_settings[0]['admin_report_frequency'].split("_")
                last_admin_notification=notif_settings[0]['last_admin_notification'].split("-")
                d_last_notification=date(int(last_admin_notification[0]),int(last_admin_notification[1]),int(last_admin_notification[2]))
                if frequency[1]=='d': #days
                    if 1==1:
                    # if today-timedelta(days=int(frequency[0]))==d_last_notification: #if True, generates a new report
                        do_report=True
                        interval_from=str(today-timedelta(days=int(frequency[0])))
                        interval_to=str(today+timedelta(days=int(frequency[0])))
                elif frequency[1]=='w':
                    #if today-timedelta(days=int(frequency[0])*7)==d_last_notification:
                    if 1==1:
                        do_report=True
                        interval_from=str(today-timedelta(days=int(frequency[0])*7))
                        interval_to=str(today+timedelta(days=int(frequency[0])*7))
                elif frequency[1]=='m':
                    #if today-relativedelta(months=int(frequency[0]))==d_last_notification:
                    if 1==1:
                        do_report=True
                        interval_from=str(today-relativedelta(months=int(frequency[0])))
                        interval_to=str(today+relativedelta(months=int(frequency[0])))
                else:
                    do_report=False
                do_report=True
                if do_report==True:
                    created_tasks=db.query("""
                        select
                            a.name,
                            a.description,
                            to_char(a.deadline,'DD-MM-YYYY') as deadline,
                            (select name from system.user where user_id=a.supervisor_id) as supervisor,
                            to_char(a.supervisor_deadline,'DD-MM-YYYY') as supervisor_deadline,
                            (select name from system.user where user_id=a.assignee_id) as assignee,
                            to_char(a.assignee_deadline,'DD-MM-YYYY') as assignee_deadline,
                            to_char(a.created,'DD-MM-YYYY') as created,
                            (select name from system.user where user_id=a.created_by) as created_by
                        from
                            task.task a
                        where
                            company_id=%s
                        and created between '%s 00:00:00' and '%s 23:59:59'
                    """%(a['company_id'],interval_from,interval_to)).dictresult()
                    created_tasks_title=['Nombre','Descripción','Fecha límite','Supervisor','Fecha límite supervisor','Auxiliar','Fecha límite auxiliar','Fecha de creación','Creado por']
                    created_tasks_d_order=['name','description','deadline','supervisor','supervisor_deadline','assignee','assignee_deadline','created','created_by']

                    expired_assignee_tasks=db.query("""
                        select
                            a.name,
                            a.description,
                            to_char(a.deadline,'DD-MM-YYYY') as deadline,
                            (select name from system.user where user_id=a.supervisor_id) as supervisor,
                            to_char(a.supervisor_deadline,'DD-MM-YYYY') as supervisor_deadline,
                            (select name from system.user where user_id=a.assignee_id) as assignee,
                            to_char(a.assignee_deadline,'DD-MM-YYYY') as assignee_deadline,
                            to_char(a.created,'DD-MM-YYYY') as created,
                            (select name from system.user where user_id=a.created_by) as created_by,
                            to_char(a.last_updated, 'DD-MM-YYYY') as last_updated,
                            (select name from system.user where user_id=a.user_last_updated) as user_last_updated
                        from
                            task.task a
                        where
                            company_id=%s
                        and assignee_deadline between '%s 00:00:00' and '%s 23:59:59'
                        and status_id in (1,6)
                    """%(a['company_id'],interval_from,interval_to)).dictresult()

                    expired_assignee_tasks_title=['Nombre','Descripción','Fecha límite','Supervisor','Fecha límite supervisor','Auxiliar','Fecha límite auxiliar','Fecha de creación','Creado por','Actualizado por última vez','Actualizado por']
                    expired_assignee_tasks_d_order=['name','description','deadline','supervisor','supervisor_deadline','assignee','assignee_deadline','created','created_by','last_updated','user_last_updated']

                    expired_supervisor_tasks=db.query("""
                        select
                            a.name,
                            a.description,
                            to_char(a.deadline,'DD-MM-YYYY') as deadline,
                            (select name from system.user where user_id=a.supervisor_id) as supervisor,
                            to_char(a.supervisor_deadline,'DD-MM-YYYY') as supervisor_deadline,
                            (select name from system.user where user_id=a.assignee_id) as assignee,
                            to_char(a.assignee_deadline,'DD-MM-YYYY') as assignee_deadline,
                            to_char(a.created,'DD-MM-YYYY') as created,
                            (select name from system.user where user_id=a.created_by) as created_by,
                            to_char(a.last_updated, 'DD-MM-YYYY') as last_updated,
                            (select name from system.user where user_id=a.user_last_updated) as user_last_updated
                        from
                            task.task a
                        where
                            company_id=%s
                        and supervisor_deadline between '%s 00:00:00' and '%s 23:59:59'
                        and status_id in (1,6)
                    """%(a['company_id'],interval_from,interval_to)).dictresult()

                    expired_supervisor_tasks_title=['Nombre','Descripción','Fecha límite','Supervisor','Fecha límite supervisor','Auxiliar','Fecha límite auxiliar','Fecha de creación','Creado por','Actualizado por última vez','Actualizado por']
                    expired_supervisor_tasks_d_order=['name','description','deadline','supervisor','supervisor_deadline','assignee','assignee_deadline','created','created_by','last_updated','user_last_updated']

                    expired_admin_tasks=db.query("""
                        select
                            a.name,
                            a.description,
                            to_char(a.deadline,'DD-MM-YYYY') as deadline,
                            (select name from system.user where user_id=a.supervisor_id) as supervisor,
                            to_char(a.supervisor_deadline,'DD-MM-YYYY') as supervisor_deadline,
                            (select name from system.user where user_id=a.assignee_id) as assignee,
                            to_char(a.assignee_deadline,'DD-MM-YYYY') as assignee_deadline,
                            to_char(a.created,'DD-MM-YYYY') as created,
                            (select name from system.user where user_id=a.created_by) as created_by,
                            to_char(a.last_updated, 'DD-MM-YYYY') as last_updated,
                            (select name from system.user where user_id=a.user_last_updated) as user_last_updated
                        from
                            task.task a
                        where
                            company_id=%s
                        and deadline between '%s 00:00:00' and '%s 23:59:59'
                        and status_id in (1,6)
                    """%(a['company_id'],interval_from,interval_to)).dictresult()

                    expired_admin_tasks_title=['Nombre','Descripción','Fecha límite','Supervisor','Fecha límite supervisor','Auxiliar','Fecha límite auxiliar','Fecha de creación','Creado por','Actualizado por última vez','Actualizado por']
                    expired_admin_tasks_d_order=['name','description','deadline','supervisor','supervisor_deadline','assignee','assignee_deadline','created','created_by','last_updated','user_last_updated']

                    resolved_tasks=db.query("""
                        select
                            a.name,
                            a.description,
                            to_char(a.deadline,'DD-MM-YYYY') as deadline,
                            (select name from system.user where user_id=a.supervisor_id) as supervisor,
                            to_char(a.supervisor_deadline,'DD-MM-YYYY') as supervisor_deadline,
                            (select name from system.user where user_id=a.assignee_id) as assignee,
                            to_char(a.assignee_deadline,'DD-MM-YYYY') as assignee_deadline,
                            to_char(a.created,'DD-MM-YYYY') as created,
                            (select name from system.user where user_id=a.created_by) as created_by,
                            to_char(a.last_updated, 'DD-MM-YYYY') as last_updated,
                            (select name from system.user where user_id=a.user_last_updated) as user_last_updated,
                            to_char(a.resolved_date,'DD-MM-YYYY') as resolved_date,
                            a.comments
                        from
                            task.task a
                        where
                            company_id=%s
                        and resolved_date between '%s 00:00:00' and '%s 23:59:59'
                        and status_id = 2
                    """%(a['company_id'],interval_from,interval_to)).dictresult()

                    resolved_tasks_title=['Nombre','Descripción','Fecha límite','Supervisor','Fecha límite supervisor','Auxiliar','Fecha límite auxiliar','Fecha de creación','Creado por','Actualizado por última vez','Actualizado por','Fecha en que se resolvió','Comentarios']
                    resolved_tasks_d_order=['name','description','deadline','supervisor','supervisor_deadline','assignee','assignee_deadline','created','created_by','last_updated','user_last_updated','resolved_date','comments']

                    closed_tasks=db.query("""
                        select
                            a.name,
                            a.description,
                            to_char(a.deadline,'DD-MM-YYYY') as deadline,
                            (select name from system.user where user_id=a.supervisor_id) as supervisor,
                            to_char(a.supervisor_deadline,'DD-MM-YYYY') as supervisor_deadline,
                            (select name from system.user where user_id=a.assignee_id) as assignee,
                            to_char(a.assignee_deadline,'DD-MM-YYYY') as assignee_deadline,
                            to_char(a.created,'DD-MM-YYYY') as created,
                            (select name from system.user where user_id=a.created_by) as created_by,
                            to_char(a.last_updated, 'DD-MM-YYYY') as last_updated,
                            (select name from system.user where user_id=a.user_last_updated) as user_last_updated,
                            to_char(a.resolved_date,'DD-MM-YYYY') as resolved_date,
                            a.comments,
                            a.supervisor_comments
                        from
                            task.task a
                        where
                            company_id=%s
                        and last_updated between '%s 00:00:00' and '%s 23:59:59'
                        and status_id = 4
                    """%(a['company_id'],interval_from,interval_to)).dictresult()

                    closed_tasks_title=['Nombre','Descripción','Fecha límite','Supervisor','Fecha límite supervisor','Auxiliar','Fecha límite auxiliar','Fecha de creación','Creado por','Actualizado por última vez','Actualizado por','Fecha en que se resolvió','Comentarios','Comentarios del supervisor']
                    closed_tasks_d_order=['name','description','deadline','supervisor','supervisor_deadline','assignee','assignee_deadline','created','created_by','last_updated','user_last_updated','resolved_date','comments','supervisor_comments']

                    declined_tasks=db.query("""
                        select
                            a.name,
                            a.description,
                            to_char(a.deadline,'DD-MM-YYYY') as deadline,
                            (select name from system.user where user_id=a.supervisor_id) as supervisor,
                            to_char(a.supervisor_deadline,'DD-MM-YYYY') as supervisor_deadline,
                            (select name from system.user where user_id=a.assignee_id) as assignee,
                            to_char(a.assignee_deadline,'DD-MM-YYYY') as assignee_deadline,
                            to_char(a.created,'DD-MM-YYYY') as created,
                            (select name from system.user where user_id=a.created_by) as created_by,
                            to_char(a.last_updated, 'DD-MM-YYYY') as last_updated,
                            (select name from system.user where user_id=a.user_last_updated) as user_last_updated,
                            a.declining_cause
                        from
                            task.task a
                        where
                            company_id=%s
                        and last_updated between '%s 00:00:00' and '%s 23:59:59'
                        and status_id = 3
                    """%(a['company_id'],interval_from,interval_to)).dictresult()

                    declined_tasks_title=['Nombre','Descripción','Fecha límite','Supervisor','Fecha límite supervisor','Auxiliar','Fecha límite auxiliar','Fecha de creación','Creado por','Actualizado por última vez','Actualizado por','Motivo para declinar']
                    declined_tasks_d_order=['name','description','deadline','supervisor','supervisor_deadline','assignee','assignee_deadline','created','created_by','last_updated','user_last_updated','declining_cause']

                    canceled_tasks=db.query("""
                        select
                            a.name,
                            a.description,
                            to_char(a.deadline,'DD-MM-YYYY') as deadline,
                            (select name from system.user where user_id=a.supervisor_id) as supervisor,
                            to_char(a.supervisor_deadline,'DD-MM-YYYY') as supervisor_deadline,
                            (select name from system.user where user_id=a.assignee_id) as assignee,
                            to_char(a.assignee_deadline,'DD-MM-YYYY') as assignee_deadline,
                            to_char(a.created,'DD-MM-YYYY') as created,
                            (select name from system.user where user_id=a.created_by) as created_by,
                            to_char(a.last_updated, 'DD-MM-YYYY') as last_updated,
                            (select name from system.user where user_id=a.user_last_updated) as user_last_updated,
                            a.declining_cause
                        from
                            task.task a
                        where
                            company_id=%s
                        and last_updated between '%s 00:00:00' and '%s 23:59:59'
                        and status_id = 5
                    """%(a['company_id'],interval_from,interval_to)).dictresult()

                    canceled_tasks_title=['Nombre','Descripción','Fecha límite','Supervisor','Fecha límite supervisor','Auxiliar','Fecha límite auxiliar','Fecha de creación','Creado por','Actualizado por última vez','Actualizado por','Motivo para declinar']
                    canceled_tasks_d_order=['name','description','deadline','supervisor','supervisor_deadline','assignee','assignee_deadline','created','created_by','last_updated','user_last_updated','declining_cause']

                    list_list=[
                        {'title':created_tasks_title,'data':created_tasks,'sheet_name':'Tareas creadas','data_order':created_tasks_d_order},
                        {'title':expired_assignee_tasks_title, 'data':expired_assignee_tasks,'sheet_name':'Tareas aux exp','data_order':expired_assignee_tasks_d_order},
                        {'title':expired_supervisor_tasks_title, 'data':expired_supervisor_tasks, 'sheet_name':'Tareas sup exp','data_order':expired_supervisor_tasks_d_order},
                        {'title':expired_admin_tasks_title, 'data':expired_admin_tasks,'sheet_name':'Tareas exp','data_order':expired_admin_tasks_d_order},
                        {'title':resolved_tasks_title, 'data':resolved_tasks,'sheet_name':'Resueltas','data_order':resolved_tasks_d_order},
                        {'title':closed_tasks_title, 'data':closed_tasks,'sheet_name':'Cerradas','data_order':closed_tasks_d_order},
                        {'title':declined_tasks_title, 'data':declined_tasks,'sheet_name':'Declinadas','data_order':declined_tasks_d_order},
                        {'title':canceled_tasks_title, 'data':canceled_tasks,'sheet_name':'Canceladas','data_order':canceled_tasks_d_order}
                    ]

                    wb = Workbook()
                    sheet_number = 0
                    for ll in list_list:
                        logger.info("------------Haciendo %s-----------------"%ll['sheet_name'])
                        if ll['data']!=[]:
                            ws = wb.create_sheet("%s"%ll['sheet_name'],sheet_number)
                            sheet_number+=1
                            for i in range(1,len(ll['title'])+1):
                                ws.cell(row=1,column=i,value=ll['title'][i-1])
                            row=2
                            for x in ll['data']:
                                logger.info(x)
                                for r in range(0,len(ll['data_order'])-1):
                                    logger.info("%s : %s"%(ll['data_order'][r],x[ll['data_order'][r]]))
                                    ws.cell(row=row,column=r+1,value=x[ll['data_order'][r]])
                                row+=1

                    fecha=str(datetime.today())
                    fecha=fecha.replace(" ","_")
                    fecha=fecha.replace(":","_")
                    fecha=fecha.replace(".","_")
                    wb.save('/tmp/prueba_%s.xlsx'%fecha)

            else:
                logger.info("La empresa company_id %s no tiene configuración de notificaciones."%a['company_id'])

        logger.info("Termina reporte administrador")

    except:
        exc_info = sys.exc_info()
        logger.error(traceback.format_exc(exc_info))

if __name__ == '__main__':
    main()
