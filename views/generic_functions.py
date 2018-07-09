#-*- coding: utf-8 -*-

from .db_connection import getDB
import logging
import sys
import traceback
import json
db = getDB()
from flask import Flask, session, request, logging, g
from flask_mail import Mail, Message
import random
app=Flask(__name__)
app.config.update(dict(
    DEBUG = True,
    MAIL_SERVER='smtpparla.spamina.com',
    MAIL_PORT=587,
    MAIL_USERNAME='pgarcia@russellbedford.mx',
    MAIL_PASSWORD='d2hC4qFFxq',
    MAIL_USE_TLS=True,
    MAIL_USE_SSL=False,
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

    def sendMail(self,subject,msg_body,recipient):
        response={}
        try:
            # msg=Message('Nuevo usuario plataforma Russell Bedford', sender='pgarcia@russellbedford.mx',recipients=['pgarcia@russellbedford.mx'])
            # msg.html='Correo de prueba'
            msg=Message(subject,sender='pgarcia@russellbedford.mx',recipients=[recipient])
            msg.html=msg_body
            mail.send(msg)
            response['success']=True
        except:
            exc_info=sys.exc_info()
            app.logger.info(traceback.format_exc(exc_info))
            response['succes']=False
        return response

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
