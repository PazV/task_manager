#-*- coding: utf-8 -*-

#from .db_connection import getDB
# db = getDB()
import logging
import sys
import traceback
import json
from flask import Flask, session, request, logging, g
from flask_mail import Mail, Message
import random
import app_config as cfg
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
import re
app=Flask(__name__)
app.config.update(dict(
    DEBUG = False,
    MAIL_SERVER=cfg.mail_server,
    MAIL_PORT=cfg.mail_port,
    MAIL_USERNAME=cfg.mail_username,
    MAIL_PASSWORD=cfg.mail_password,
    MAIL_USE_TLS=cfg.mail_use_tls,
    MAIL_USE_SSL=cfg.mail_use_ssl,
))
mail = Mail(app)
class GenericFunctions:
    def toDict(self,form,method):
        """
        Parameters:request.form
        Description:Obtains ImmutableMultiDict object and returns [flag success (True/False) ,data dictionary]
        """
        try:
            if method=='post':
                d=form.to_dict(flat=False)
                e=d.keys()[0]
                f=json.loads(e)
                #f=eval(e)
                return True,f
            else:
                d=form.to_dict(flat=False)
                return True,d
        except:
            exc_info = sys.exc_info()
            app.logger.info(traceback.format_exc(exc_info))
            return False,''

    # def sendMail(self,subject,msg_body,recipient):
    #     response={}
    #     try:
    #         # msg=Message('Nuevo usuario plataforma Russell Bedford', sender='pgarcia@russellbedford.mx',recipients=['pgarcia@russellbedford.mx'])
    #         # msg.html='Correo de prueba'
    #         msg=Message(subject,sender=cfg.mail_username,recipients=[recipient])
    #         msg.html=msg_body
    #         mail.send(msg)
    #         response['success']=True
    #     except:
    #         exc_info=sys.exc_info()
    #         app.logger.info(traceback.format_exc(exc_info))
    #         response['succes']=False
    #     return response

    def sendMail(self,subject,body,to_address):
        response={}
        try:
            server=smtplib.SMTP(cfg.mail_server,cfg.mail_port)
            server.login(cfg.mail_username,cfg.mail_password)
            from_address=cfg.mail_username
            msg=MIMEMultipart()
            msg['From']=from_address
            if type(to_address)==list:
                msg['To']=','.join(to_address)
                to_address.append(cfg.app_admin_mail)
                list_to=to_address
            else:
                msg['To']=to_address
                list_to=[to_address,cfg.app_admin_mail]
            # msg['To']="%s, %s"%(to_address,cfg.app_admin_mail)
            msg['Subject']=subject.decode('utf-8')
            body=self.replaceStringHtml(body)
            msg.attach(MIMEText(body,'html'))
            text=msg.as_string()

            server.sendmail(from_address,list_to,text)
            response['success']=True
        except:
            exc_info=sys.exc_info()
            app.logger.info(traceback.format_exc(exc_info))
            response['success']=False
        return response

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

    def generateRandomPassword(self,pass_len):
        """
        Parameters:pass_len(indicates the password length)
        Description:Generates a random password with the length stablished in pass_len
        """
        try:
            sample='abcdefghijklmnopqstuvwxyzABCDEFGHIJKLMNOPQRSTUVWZYX0123456789_-.$#'
            password=''.join(str(i) for i in random.sample(sample,pass_len))
            return True,password
        except:
            exc_info = sys.exc_info()
            app.logger.info(traceback.format_exc(exc_info))
            return False, ''


    def replaceString(self,text):
        rep = {
            "á":"a",
            "é":"e",
            "í":"i",
            "ó":"o",
            "ú":"u",
            "Á":"A",
            "É":"E",
            "Í":"I",
            "Ó":"O",
            "Ú":"U",
            "#":"",
            "$":"",
            "%":"",
            "&":"",
            "'":"",
            " ":"_"
        }
        rep = dict((re.escape(k), v) for k, v in rep.iteritems())
        pattern = re.compile("|".join(rep.keys()))
        new_text = pattern.sub(lambda m: rep[re.escape(m.group(0))], text)
        return new_text

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

    def as_text(self,value):
        if value is None:
            return ""
        else:
            try:
                return str(value)
            except:
                return value
