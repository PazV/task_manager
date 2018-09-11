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
logger = logging.getLogger('Send User Notif')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('%scron_send_user_notif.log'%cfg.log_path)
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

        assignee_html_message="""
            <p>Estimado {user_name}:</p>
                <p>Le recordamos que tiene pendiente por resolver las siguientes tareas:</p>
                <table style="width: 100%; border-collapse: collapse;" border="1">
                <tbody>
                <tr style="height: 15px;">
                <td style="width: 11.9339%; text-align: center; height: 15px;"><strong>Prioridad</strong></td>
                <td style="width: 43.0992%; text-align: center; height: 15px;"><strong>Nombre</strong></td>
                <td style="width: 22.9669%; text-align: center; height: 15px;"><strong>Responsable</strong></td>
                <td style="width: 22%; text-align: center; height: 15px;"><strong>Fecha de vencimiento</strong></td>
                </tr>
                {rows}
                </tbody>
                </table>
                <p>Para ingresar a la plataforma, dar click <a href="{link}">aqu&iacute;</a>.</p>
                <p><img src="data:image/png;base64,{mail_img}" alt="" width="352" height="81" /></p>
        """

        row_expired_red_flag="""
            <tr style="height: 28px;">
                <td style="width: 11.9339%; height: 22px;"><img style="display: block; margin-left: auto; margin-right: auto;" src="data:image/png;base64,{img_red_flag}" alt="" width="15" height="18" /></td>
                <td style="width: 43.0992%; height: 22px;"><span style="color: #ff0000;">{name}</span></td>
                <td style="width: 22.9669%; text-align: center; height: 22px;"><span style="color: #ff0000;">{in_charge}</span></td>
                <td style="width: 22%; text-align: center; height: 22px;"><span style="color: #ff0000;">{deadline}</span></td>
            </tr>
        """


        row_red_flag="""
            <tr style="height: 28px;">
                <td style="width: 11.9339%; height: 22px;"><img style="display: block; margin-left: auto; margin-right: auto;" src="data:image/png;base64,{img_red_flag}" alt="" width="15" height="18" /></td>
                <td style="width: 43.0992%; height: 22px;">{name}</td>
                <td style="width: 22.9669%; text-align: center; height: 22px;">{in_charge}</td>
                <td style="width: 22%; text-align: center; height: 22px;">{deadline}</td>
            </tr>
        """

        row_yellow_flag="""
            <tr style="height: 28px;">
                <td style="width: 11.9339%; height: 22px;"><img style="display: block; margin-left: auto; margin-right: auto;" src="data:image/png;base64,{img_yellow_flag}" alt="" width="15" height="18" /></td>
                <td style="width: 43.0992%; height: 22px;">{name}</td>
                <td style="width: 22.9669%; text-align: center; height: 22px;">{in_charge}</td>
                <td style="width: 22%; text-align: center; height: 22px;">{deadline}</td>
            </tr>
        """



        notif_list=db.query("""
            select *,
            to_char(last_admin_notification,'DD-MM-YYYY HH24:MI:SS') as last_admin_notification
            from system.notification_settings
        """).dictresult()
        if notif_list!=[]:
            for nl in notif_list:
                assignee_days=int(nl['assignee_days'].split("_")[0])
                supervisor_days=int(nl['supervisor_days'].split("_")[0])
                admin_days=int(nl['admin_days'].split("_")[0])

                users=db.query("""
                    select
                        user_id,
                        name as user_name,
                        email,
                        user_type_id
                    from
                        system.user
                    where
                        company_id=%s
                    and enabled in (1,3)
                """%nl['company_id']).dictresult()
                if users!=[]:
                    for u in users:
                        rows=""
                        has_tasks=False
                        logger.info("Haciendo usuario : %s"%u['user_name'])
                        if u['user_type_id'] in (2,3):
                            expired_tasks=db.query("""
                                select
                                    name,
                                    to_char(assignee_deadline, 'DD-MM-YYYY HH24:MI:SS') as deadline,
                                    (select a.name from system.user a where a.user_id=supervisor_id) as in_charge
                                from task.task
                                where status_id in (1,6)
                                and company_id=%s
                                and assignee_id=%s
                                and assignee_deadline<now()
                                order by assignee_deadline asc
                            """%(nl['company_id'],u['user_id'])).dictresult()
                            if expired_tasks!=[]:
                                has_tasks=True
                                for x in expired_tasks:
                                    x['img_red_flag']=cfg.img_red_flag
                                    new_row=row_expired_red_flag.format(**x)
                                    rows+=new_row

                            red_flag_tasks=db.query("""
                                select
                                    name,
                                    to_char(assignee_deadline, 'DD-MM-YYYY HH24:MI:SS') as deadline,
                                    (select a.name from system.user a where a.user_id=supervisor_id) as in_charge
                                from task.task
                                where status_id in (1,6)
                                and company_id=%s
                                and assignee_id=%s
                                and now() between assignee_deadline - INTERVAL '%s DAYS' and assignee_deadline
                                order by assignee_deadline asc
                            """%(nl['company_id'],u['user_id'],assignee_days)).dictresult()
                            if red_flag_tasks!=[]:
                                has_tasks=True
                                for x in red_flag_tasks:
                                    x['img_red_flag']=cfg.img_red_flag
                                    new_row=row_red_flag.format(**x)
                                    rows+=new_row

                            yellow_flag_tasks=db.query("""
                                select
                                    name,
                                    to_char(assignee_deadline, 'DD-MM-YYYY HH24:MI:SS') as deadline,
                                    (select a.name from system.user a where a.user_id=supervisor_id) as in_charge
                                from task.task
                                where status_id in (1,6)
                                and company_id=%s
                                and assignee_id=%s
                                and now() < assignee_deadline - INTERVAL '%s DAYS'
                                order by assignee_deadline asc
                            """%(nl['company_id'],u['user_id'],assignee_days)).dictresult()
                            if yellow_flag_tasks!=[]:
                                has_tasks=True
                                for x in yellow_flag_tasks:
                                    x['img_yellow_flag']=cfg.img_yellow_flag
                                    new_row=row_yellow_flag.format(**x)
                                    rows+=new_row

                            if has_tasks==True:
                                if u['user_type_id']==3:
                                    message_dict={
                                        'rows':rows,
                                        'link':cfg.host,
                                        'mail_img':cfg.mail_img,
                                        'user_name':u['user_name']
                                    }
                                    message=assignee_html_message.format(**message_dict)
                                    MF.sendMail(u['email'],'Tareas pendientes',message)
                            if u['user_type_id']==2:
                                supervisor_has_tasks=False
                                sup_rows=""
                                expired_tasks_sup=db.query("""
                                    select
                                        name,
                                        to_char(supervisor_deadline, 'DD-MM-YYYY HH24:MI:SS') as deadline,
                                        (select a.name from system.user a where a.user_id=assignee_id) as in_charge
                                    from task.task
                                    where status_id in (1,6)
                                    and company_id=%s
                                    and supervisor_id=%s
                                    and supervisor_deadline<now()
                                    order by supervisor_deadline asc
                                """%(nl['company_id'],u['user_id'])).dictresult()
                                if expired_tasks_sup!=[]:
                                    supervisor_has_tasks=True
                                    for x in expired_tasks_sup:
                                        x['img_red_flag']=cfg.img_red_flag
                                        new_row=row_expired_red_flag.format(**x)
                                        sup_rows+=new_row
                                red_flag_sup=db.query("""
                                    select
                                        name,
                                        to_char(supervisor_deadline, 'DD-MM-YYYY HH24:MI:SS') as deadline,
                                        (select a.name from system.user a where a.user_id=assignee_id) as in_charge
                                    from task.task
                                    where status_id in (1,6)
                                    and company_id=%s
                                    and supervisor_id=%s
                                    and now() between supervisor_deadline - INTERVAL '%s DAYS' and supervisor_deadline
                                    order by supervisor_deadline asc
                                """%(nl['company_id'],u['user_id'],supervisor_days)).dictresult()
                                if red_flag_sup!=[]:
                                    supervisor_has_tasks=True
                                    for x in red_flag_sup:
                                        x['img_red_flag']=cfg.img_red_flag
                                        new_row=row_red_flag.format(**x)
                                        sup_rows+=new_row
                                yellow_flag_sup=db.query("""
                                    select
                                        name,
                                        to_char(supervisor_deadline, 'DD-MM-YYYY HH24:MI:SS') as deadline,
                                        (select a.name from system.user a where a.user_id=assignee_id) as in_charge
                                    from task.task
                                    where status_id in (1,6)
                                    and company_id=%s
                                    and supervisor_id=%s
                                    and now() < supervisor_deadline - INTERVAL '%s DAYS'
                                    order by supervisor_deadline asc
                                """%(nl['company_id'],u['user_id'],supervisor_days)).dictresult()
                                if yellow_flag_sup!=[]:
                                    supervisor_has_tasks=True
                                    for x in yellow_flag_sup:
                                        x['img_yellow_flag']=cfg.img_yellow_flag
                                        new_row=row_yellow_flag.format(**x)
                                        sup_rows+=new_row
                                if has_tasks==True or supervisor_has_tasks==True:
                                    sup_assignee_msg=""
                                    sup_msg=""
                                    message_sup='<p>Estimado {user_name}:</p>'
                                    if has_tasks==True:
                                        sup_assignee_msg="""
                                            <p>Le recordamos que tiene pendiente por resolver las siguientes tareas:</p>
                                            <table style="width: 100%; border-collapse: collapse;" border="1">
                                            <tbody>
                                            <tr style="height: 15px;">
                                            <td style="width: 11.9339%; text-align: center; height: 15px;"><strong>Prioridad</strong></td>
                                            <td style="width: 43.0992%; text-align: center; height: 15px;"><strong>Nombre</strong></td>
                                            <td style="width: 22.9669%; text-align: center; height: 15px;"><strong>Responsable</strong></td>
                                            <td style="width: 22%; text-align: center; height: 15px;"><strong>Fecha de vencimiento</strong></td>
                                            </tr>
                                            {rows}
                                            </tbody>
                                            </table>
                                            <p>&nbsp;</p>
                                        """
                                    if supervisor_has_tasks==True:
                                        sup_msg="""
                                            <p>Le recordamos que las siguientes tareas no han sido resueltas:</p>
                                            <table style="width: 100%; border-collapse: collapse;" border="1">
                                            <tbody>
                                            <tr style="height: 15px;">
                                            <td style="width: 11.9339%; text-align: center; height: 15px;"><strong>Prioridad</strong></td>
                                            <td style="width: 43.0992%; text-align: center; height: 15px;"><strong>Nombre</strong></td>
                                            <td style="width: 22.9669%; text-align: center; height: 15px;"><strong>Responsable</strong></td>
                                            <td style="width: 22%; text-align: center; height: 15px;"><strong>Fecha de vencimiento</strong></td>
                                            </tr>
                                            {sup_rows}
                                            </tbody>
                                            </table>
                                            <p>&nbsp;</p>
                                            <p>Para ingresar a la plataforma, dar click <a href="{link}">aqu&iacute;</a>.</p>
                                            <p><img src="data:image/png;base64,{mail_img}" alt="" width="352" height="81" /></p>
                                        """
                                    format_sup_msg={
                                        'rows':rows,
                                        'sup_rows':sup_rows,
                                        'mail_img':cfg.mail_img,
                                        'link':cfg.host,
                                        'user_name':u['user_name']
                                    }
                                    message_sup+=sup_assignee_msg
                                    message_sup+=sup_msg
                                    message_supervisor=message_sup.format(**format_sup_msg)
                                    MF.sendMail(u['email'],'Tareas pendientes',message_supervisor)

                        elif u['user_type_id'] in (1,4,6):
                            has_tasks=False
                            rows=""
                            expired_admin_tasks=db.query("""
                                select
                                    name,
                                    to_char(deadline, 'DD-MM-YYYY HH24:MI:SS') as deadline,
                                    (select a.name from system.user a where a.user_id=supervisor_id) as in_charge
                                from task.task
                                where status_id in (1,6)
                                and company_id=%s
                                and deadline<now()
                                order by deadline asc
                            """%nl['company_id']).dictresult()
                            if expired_admin_tasks!=[]:
                                has_tasks=True
                                for x in expired_admin_tasks:
                                    x['img_red_flag']=cfg.img_red_flag
                                    new_row=row_expired_red_flag.format(**x)
                                    rows+=new_row

                            red_flag_admin=db.query("""
                                select
                                    name,
                                    to_char(deadline, 'DD-MM-YYYY HH24:MI:SS') as deadline,
                                    (select a.name from system.user a where a.user_id=supervisor_id) as in_charge
                                from task.task
                                where status_id in (1,6)
                                and company_id=%s
                                and now() between deadline - INTERVAL '%s DAYS' and deadline
                                order by deadline asc
                            """%(nl['company_id'],admin_days)).dictresult()
                            if red_flag_admin!=[]:
                                has_tasks=True
                                for x in red_flag_admin:
                                    x['img_red_flag']=cfg.img_red_flag
                                    new_row=row_red_flag.format(**x)
                                    rows+=new_row

                            yellow_flag_admin=db.query("""
                                select
                                    name,
                                    to_char(deadline, 'DD-MM-YYYY HH24:MI:SS') as deadline,
                                    (select a.name from system.user a where a.user_id=supervisor_id) as in_charge
                                from task.task
                                where status_id in (1,6)
                                and company_id=%s
                                and now() < deadline - INTERVAL '%s DAYS'
                                order by deadline asc
                            """%(nl['company_id'],admin_days)).dictresult()
                            if yellow_flag_admin!=[]:
                                has_tasks=True
                                for x in yellow_flag_admin:
                                    x['img_yellow_flag']=cfg.img_yellow_flag
                                    new_row=row_yellow_flag.format(**x)
                                    rows+=new_row
                            if has_tasks==True:
                                admin_msg="""
                                    <p>Estimado {user_name}:</p>
                                        <p>Le recordamos que tiene pendientes las siguientes tareas:</p>
                                        <table style="width: 100%; border-collapse: collapse;" border="1">
                                        <tbody>
                                        <tr style="height: 15px;">
                                        <td style="width: 11.9339%; text-align: center; height: 15px;"><strong>Prioridad</strong></td>
                                        <td style="width: 43.0992%; text-align: center; height: 15px;"><strong>Nombre</strong></td>
                                        <td style="width: 22.9669%; text-align: center; height: 15px;"><strong>Responsable</strong></td>
                                        <td style="width: 22%; text-align: center; height: 15px;"><strong>Fecha de vencimiento</strong></td>
                                        </tr>
                                        {rows}
                                        </tbody>
                                        </table>
                                        <p>Para ingresar a la plataforma, dar click <a href="{link}">aqu&iacute;</a>.</p>
                                        <p><img src="data:image/png;base64,{mail_img}" alt="" width="352" height="81" /></p>
                                """
                                format_admin_msg={
                                    'rows':rows,
                                    'link':cfg.host,
                                    'mail_img':cfg.mail_img,
                                    'user_name':u['user_name']
                                }
                                MF.sendMail(u['email'],'Tareas pendientes',admin_msg.format(**format_admin_msg))







        logger.info(notif_list)
    except:
        exc_info = sys.exc_info()
        logger.error(traceback.format_exc(exc_info))

if __name__ == '__main__':
    main()


print "Termina cron"
