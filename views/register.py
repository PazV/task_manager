 # -*- coding: utf-8 -*-
from flask import Flask, render_template, flash, redirect, url_for, session, request, logging, Blueprint, g
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.datastructures import ImmutableMultiDict
from .db_connection import getDB
import logging
db = getDB()
from .auth import is_logged_in
import json
import traceback
from flask_mail import Mail, Message
import random
import sys
import re
import os
import pwd
import grp
from . import generic_functions
GF=generic_functions.GenericFunctions()
import app_config as cfg
# from flask import current_app as app
#from flask import current_app as app
bp = Blueprint('register', __name__, url_prefix='/register')


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

@bp.route('/new_company', methods=['GET','POST'])
@is_logged_in
def new_company():
    logging.info("entra a new company")
    form = RegisterNewCompany(request.form)
    logging.info(form['business_name'])

    if request.method == 'POST' and form.validate():
        logging.info("validated correctly")
        logging.info(request.form)
    else:
        logging.info("ocurrio un error")
        logging.info(form.errors)

    return render_template('home.html', form=form)

@bp.route('/dogrid', methods=['GET','POST'])
@is_logged_in
def dogrid():
    logging.info("entra a funcion dogrid")
    form = RegisterNewCompany(request.form)
    if request.method == 'POST'  and form.validate():
        logging.info("entra if")
        logging.info(request.form)
        return redirect(url_for(index))
    return render_template('home.html', form=form)

@bp.route('/saveNewCompany', methods=['GET','POST'])
@is_logged_in
def saveNewCompany():
    """
    Parameters:{business_name,name,address,phone}
    Description: Saves in DB new company
    """
    logging.info("entra a save company")
    response={}
    try:
        if request.method == 'POST':
            flag,dict=toDict(request.form,'post')
            if flag:
                logging.info("success: %s"%dict)
                for k,v in dict.iteritems():
                    if len(v.strip())==0:
                        response['success']=False
                        response['msg_response']='Existen campos vacíos, no es posible realizar el registro de la empresa.'
                        break
                if 'success' not in response:
                    new_folder=replaceString(dict['business_name'])[0:10]
                    company=db.insert('system.company',dict)
                    folder="%s_%s"%(new_folder,company['company_id'])
                    db.query("""
                        update system.company
                        set task_folder='%s'
                        where company_id=%s
                    """%(folder,company['company_id']))
                    logging.info(company)
                    # if not os.path.exists('/usr/local/arctic/tmp/%s'%folder):
                    #     os.makedirs('/usr/local/arctic/tmp/%s'%folder)
                    #     uid = pwd.getpwnam("pgarcia").pw_uid
                    #     gid = grp.getgrnam("pgarcia").gr_gid
                    #     path = '/usr/local/arctic/tmp/%s'%folder
                    if not os.path.exists('%s%s'%(cfg.task_path,folder)):
                        os.makedirs('%s%s'%(cfg.task_path,folder))
                        uid = pwd.getpwnam(cfg.admin_uid).pw_uid
                        gid = grp.getgrnam(cfg.admin_gid).gr_gid
                        path = '%s%s'%(cfg.task_path,folder)
                        os.chown(path, uid, gid)


                    response['success']=True
                    response['msg_response']='La empresa <b>%s</b> ha sido registrada.'%dict['name']

            else:
                response['success']=False
                response['msg_response']='Ocurrió un error al intentar obtener los datos del formulario, favor de intentarlo nuevamente.'

        else:
            logging.info("GET")

            response['success']=True
            response['msg_response']='La empresa ha sido registrada exitosamente.'

    except:
        response['success']=False
        response['msg_response']='Ocurrió un error al intentar registrar la empresa.'
        exc_info = sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)

@bp.route('/getCompanies', methods=['GET','POST'])
@is_logged_in
def getCompanies():
    """
    Parameters:user_id
    Description:Gets list of registered companies.
    """
    response={}
    try:
        if request.method=='POST':
            flag,dict=toDict(request.form,'post')
            if flag:
                if dict['company_id']==-1:
                    companies=db.query("""
                        select
                            company_id,
                            business_name ||' - '|| name as name
                        from
                            system.company
                        order by name asc
                    """).dictresult()
                else:
                    companies=[]
                response['success']=True
                response['data']=companies
            else:
                response['success']=False
                response['msg_response']='Ocurrió un error, favor de intentarlo de nuevo.'
        else:
            response['success']=False
            response['msg_response']='Favor de iniciar sesión nuevamente.'

    except:
        response['success']=False
        response['msg_response']='Ocurrió un error, favor de intentarlo de nuevo.'
        exc_info = sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)

@bp.route('/getUserType',methods=['GET','POST'])
@is_logged_in
def getUserType():
    response={}
    try:
        if request.method=='POST':
            flag,dict=toDict(request.form,'post')
            if flag:
                if dict['get']=='admin': #obtiene tipos de usuario para usuario administrador
                    user_type=db.query("""
                        select
                            user_type_id,
                            user_type
                        from
                            system.user_type
                        where
                            admin_privileges=True
                        and user_type <> 'root'
                    """).dictresult()
                elif dict['get']=='all':
                    user_type=db.query("""
                        select
                            user_type_id,
                            user_type
                        from
                            system.user_type
                        where
                            admin_privileges=False
                    """).dictresult()
                else:
                    user_type=[]
                response['success']=True
                response['data']=user_type
            else:
                response['success']=False
                response['msg_response']='Ocurrió un error, favor de intentarlo de nuevo.'
        else:
            response['success']=False
            response['msg_response']='Favor de iniciar sesión nuevamente.'
    except:
        response['success']=False
        response['msg_response']='Ocurrió un error, favor de intentarlo nuevamente.'
        exc_info = sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)


# @bp.route('/sendMail', methods=['GET','POST'])
# def sendMail():
#     logging.info("entra mail")
#     msg=Message('Hello',sender='pgarcia@russellbedford.mx',recipients=['pazgarcia91@gmail.com'])
#     msg.body='Prueba mensaje flask'
#     mail.send(msg)
#     return 'Sent'

@bp.route('/createUser',methods=['GET','POST'])
@is_logged_in
def createUser():
    response={}
    try:
        if request.method=='POST':
            flag,dict=toDict(request.form,'post')

            if flag:
                if dict['user_id']==-1:
                    condition=""
                else:
                    condition=" and user_id<>%s"%dict['user_id']
                #check if login and mail already exists
                exist_email=db.query("""
                    select
                        count(*)
                    from
                        system.user
                    where
                        email='%s'
                    and company_id=%s %s
                """%(dict['email'],dict['company_id'],condition)).dictresult()
                exist_email[0]['count']=0 #bypass email validation
                if exist_email[0]['count']==0:
                    company_name=db.query("""
                        select name from system.company where company_id=%s
                    """%dict['company_id']).dictresult()[0]
                    if dict['user_id']==-1:
                        exist_login=db.query("""
                            select
                                count(*)
                            from
                                system.user
                            where
                                login='%s'
                            --and company_id=%s
                        """%(dict['login'].lower(),dict['company_id'])).dictresult()
                        if exist_login[0]['count']==0:
                            if dict['user_type_id'] in (1,6):
                                #busca si ya existe un usuario administrador para la empresa
                                admin_users=db.query("""
                                    select count(*) from system.user where user_type_id in (1,6)
                                    and company_id=%s
                                """%dict['company_id']).dictresult()[0]['count']
                                if admin_users==0:
                                    passwd_success,passwd=generateRandomPassword(8)
                                    if passwd_success:
                                        dict['password']=generate_password_hash(passwd)
                                        login=dict['login'].strip()
                                        dict['login']=replaceString(login)
                                        dict['login']=dict['login'].lower()
                                        dict['name']=dict['name'].strip()
                                        dict['name']=dict['name'].decode('utf-8')
                                        dict['email']=dict['email'].strip()
                                        del dict['user_id']
                                        db.insert('system.user',dict)

                                        message=db.query("""
                                            select * from template.generic_template where type_id=7
                                        """).dictresult()[0]

                                        recipient=dict['email']
                                        dict['password']=passwd
                                        dict['link']=cfg.host
                                        dict['mail_img']=cfg.mail_img
                                        dict['company']=company_name['name']
                                        msg=message['body'].format(**dict)
                                        GF.sendMail(message['subject'],msg,recipient)

                                        response['success']=True
                                        response['msg_response']='Usuario registrado, se ha enviado un correo con los datos de acceso a la dirección de correo ingresada.'
                                    else:
                                        response['success']=False
                                        response['msg_response']='Ocurrió un error al intentar realizar el registro, favor de intentarlo de nuevo más tarde.'
                                else:
                                    response['success']=False
                                    response['msg_response']='Ya existe un usuario administrador para esta empresa.'
                            else:
                                passwd_success,passwd=generateRandomPassword(8)
                                if passwd_success:
                                    dict['password']=generate_password_hash(passwd)
                                    login=dict['login'].strip()
                                    dict['login']=replaceString(login)
                                    dict['login']=dict['login'].lower()
                                    dict['name']=dict['name'].strip()
                                    dict['name']=dict['name'].decode('utf-8')
                                    dict['email']=dict['email'].strip()
                                    del dict['user_id']
                                    db.insert('system.user',dict)

                                    message=db.query("""
                                        select * from template.generic_template where type_id=7
                                    """).dictresult()[0]

                                    recipient=dict['email']
                                    dict['password']=passwd
                                    dict['link']=cfg.host
                                    dict['mail_img']=cfg.mail_img
                                    dict['company']=company_name['name']
                                    msg=message['body'].format(**dict)
                                    GF.sendMail(message['subject'],msg,recipient)

                                    response['success']=True
                                    response['msg_response']='Usuario registrado, se ha enviado un correo con los datos de acceso a la dirección de correo ingresada.'
                                else:
                                    response['success']=False
                                    response['msg_response']='Ocurrió un error al intentar realizar el registro, favor de intentarlo de nuevo más tarde.'

                        else:
                            response['success']=False
                            response['msg_response']='El usuario (login) ingresado ya se encuentra registrado, favor de ingresar uno nuevo.'
                    else:

                        dict['name']=dict['name'].strip()
                        dict['name']=dict['name'].decode('utf-8')
                        dict['email']=dict['email'].strip()
                        dict['last_updated']='now'
                        #verificar si desea cambiar perfil
                        old_profile=db.query("""
                            select user_type_id from system.user where user_id=%s
                        """%dict['user_id']).dictresult()
                        if old_profile[0]['user_type_id']==dict['user_type_id']:
                            db.update('system.user',dict)
                            response['success']=True
                            response['msg_response']='El usuario ha sido actualizado.'
                        else:
                            if old_profile[0]['user_type_id']==3:
                                has_tasks=db.query("""
                                    select count(*) from task.task
                                    where assignee_id=%s
                                    and status_id in (1,6)
                                """%dict['user_id']).dictresult()
                                if has_tasks[0]['count']==0:
                                    db.update('system.user',dict)
                                    response['success']=True
                                    response['msg_response']='El usuario ha sido actualizado.'
                                else:
                                    response['success']=False
                                    response['msg_response']='El usuario no puede ser actualizdo, pues a&uacute;n cuenta con tareas asignadas.'
                            else:
                                has_tasks=db.query("""
                                    select count(*) from task.task
                                    where supervisor_id=%s
                                    and status_id in (1,2,3,6)
                                """%dict['user_id']).dictresult()
                                if has_tasks[0]['count']==0:
                                    db.update('system.user',dict)
                                    response['success']=True
                                    response['msg_response']='El usuario ha sido actualizado.'
                                else:
                                    #revisar si las tareas asignadas declinadas han sido declinadas por el supervisor
                                    declined_tasks=db.query("""
                                        select count(*) from task.task
                                        where status_id=3
                                        and supervisor_id=%s
                                        and declined_by=%s
                                    """%(dict['user_id'],dict['user_id'])).dictresult()
                                    if declined_tasks[0]['count']==has_tasks[0]['count']:
                                        db.update('system.user',dict)
                                        response['success']=True
                                        response['msg_response']='El usuario ha sido actualizado.'
                                    else:
                                        response['success']=False
                                        response['msg_response']='El usuario no puede ser actualizado, pues a&uacute;n cuenta con tareas asignadas.'

                else:
                    response['success']=False
                    response['msg_response']='La dirección de correo ya se encuentra registrada para la empresa seleccionada.'
            else:
                response['success']=False
                response['msg_response']='Ocurrió un error al intentar procesar los datos ingresados, favor de intentarlo de nuevo.'
        else:
            response['success']=False
            response['msg_response']='Intentelo nuevamente.'
    except:
        response['success']=False
        response['msg_response']='Ocurrió un error inesperado, favor de intentarlo de nuevo más tarde.'
        exc_info = sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)

def toDict(form,method):
    """
    Parameters:request.form
    Description:Obtains ImmutableMultiDict object and returns [flag success (True/False) ,data dictionary]
    """
    try:
        if method=='post':
            d=form.to_dict(flat=False)
            e=d.keys()[0]
            f=eval(e)
            return True,f
        else:
            d=form.to_dict(flat=False)
            return True,d
    except:
        exc_info = sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
        return False,''

def generateRandomPassword(pass_len):
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


def replaceString(text):
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
