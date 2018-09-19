#-*- coding: utf-8 -*-

from flask import Flask, render_template, flash, redirect, url_for, session, request, logging, Blueprint, g
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash
from pg import DB
from .db_connection import getDB
import logging
db = getDB()
from .auth import is_logged_in
import json
from . import generic_functions
import traceback
import sys
import app_config as cfg
from flask import current_app as app
GF=generic_functions.GenericFunctions()
#app=Flask(__name__)
bp = Blueprint('users',__name__, url_prefix='/users')

@bp.route('/changePassword', methods=['GET','POST'])
@is_logged_in
def changePassword():
    """
    Parameters:{user_id,old_password,new_password}
    Description: Changes password of a given user
    """
    response={}
    try:
        if request.method=='POST':
            flag,data=GF.toDict(request.form,'post')

            if flag:
                old_pass=db.query("""
                    select password
                    from system.user
                    where user_id=%s
                """%data['user_id']).dictresult()
                response['success']=False
                if old_pass!=[]:
                    if check_password_hash(old_pass[0]['password'],data['old_password']):
                        if data['new_password']==data['confirm_password']:
                            if len(data['new_password'])>=6:
                                if data['new_password'].replace(" ","")==data['new_password']:
                                    if data['new_password']!=data['old_password']:
                                        db.query("""
                                            update system.user
                                            set password='%s',
                                            last_updated='now()'
                                            where user_id=%s
                                        """%(generate_password_hash(data['new_password']),data['user_id']))
                                        response['msg_response']="La contraseña ha sido actualizada."
                                        response['success']=True
                                    else:
                                        response['msg_response']="Su nueva contraseña debe ser distinta a la contraseña actual."
                                else:
                                    response['msg_response']="La contraseña no debe contener espacios."
                            else:
                                response['msg_response']="La contraseña debe contener al menos 6 caracteres."
                        else:
                            response['msg_response']="Los datos ingresados en nueva contraseña y confirmar contraseña deben coincidir."
                    else:
                        response['msg_response']="La contraseña ingresada no coincide con su contraseña actual."
                else:
                    response['msg_response']="Ocurrió un error al intentar obtener sus datos actuales, favor de intentarlo nuevamente."
            else:
                response['msg_response']="Ocurrió un error al intentar obtener sus datos actuales, favor de intentarlo nuevamente."
        else:
            response['msg_response']="Intentelo de nuevo."
    except:
        response['success']=False
        response['msg_response']="Ocurrió un error, favor de intentarlo nuevamente."
        exc_info = sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)

@bp.route('/getUsers',methods=['GET','POST'])
@is_logged_in
def getUsers():
    """
    Parameters:{user_id}
    Description:Retrieves a list of users that belong to the given company_id
    """
    response={}
    try:

        start=int(request.form['start'])
        limit=int(request.form['length'])
        company_id=request.form['company_id']
        try:
            data_from=request.form['from']
            condition=" and a.user_type_id not in (1,4,5,6)"
        except:
            condition=""

        users=db.query("""
            select
                a.user_id,
                a.login,
                a.email,
                a.name,
                b.user_type_id,
                b.user_type
            from
                system.user a,
                system.user_type b
            where
                a.company_id=%s
            and
                a.user_type_id=b.user_type_id
            and enabled in (1,3) %s
            order by name
            offset %s limit %s
        """%(company_id,condition,start,limit)).dictresult()
        total=db.query("""
            select
                count(*)
            from
                system.user a,
                system.user_type b
            where
                a.company_id=%s
            and
                a.user_type_id=b.user_type_id
            and enabled in (1,3) %s
        """%(company_id,condition)).dictresult()
        response['data']=users
        response['recordsTotal']=total[0]['count']
        response['recordsFiltered']=total[0]['count']
        response['success']=True

    except:
        response['success']=False
        response['msg_response']='Ocurrió un error, favor de intentarlo nuevamente.'
        exc_info = sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)

@bp.route('/disableUser', methods=['GET','POST'])
@is_logged_in
def disableUser():
    response={}
    try:
        flag,data=GF.toDict(request.form,'post')
        if flag:
            has_tasks=db.query("""
                select
                    count(*)
                from
                    task.task
                where
                    (assignee_id=%s or supervisor_id=%s)
                and status_id in (1,2,6)
            """%(data['user_id'],data['user_id'])).dictresult()[0]
            if has_tasks['count']==0:
                db.query("""
                    update system.user
                    set enabled=2
                    where user_id=%s
                """%data['user_id'])
                response['success']=True
                response['msg_response']='El usuario ha sido deshabilitado.'
            else:
                response['success']=False
                response['msg_response']='El usuario no puede ser deshabilitado, pues aún tiene tareas asignadas.'
        else:
            response['success']=False
            response['msg_response']="Ocurrió un error al intentar procesar la información, favor de intentarlo nuevamente."
    except:
        response['success']=False
        response['msg_response']="Ocurrió un error, favor de intentarlo nuevamente."
        exc_info=sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)

@bp.route('/getManagerUserList', methods=['GET','POST'])
@is_logged_in
def getManagerUserList():
    response={}
    try:
        start=int(request.form['start'])
        limit=int(request.form['length'])
        company_id=request.form['company_id']
        disabled=request.form['show_disabled_users']

        if disabled=="true":
            enabled=" and a.enabled in (1,2,3) "
        else:
            enabled=" and a.enabled in (1,3) "
        users=db.query("""
            select
                a.user_id,
                a.name,
                a.email,
                a.login,
                b.user_type,
                case when a.enabled=1 then 'Habilitado' when a.enabled=2 then 'Deshabilitado' else 'Bloqueado' end as status
            from
                system.user_type b,
                system.user a
            where
                a.user_type_id=b.user_type_id
            and a.company_id=%s %s
            order by name asc
            offset %s limit %s
        """%(company_id,enabled,start,limit)).dictresult()

        for x in users:
            session=db.query("""
                select * from system.user_session
                where user_id=%s
                order by session_id desc
                limit 1
            """%x['user_id']).dictresult()
            if session!=[]:
                if session[0]['logged']==True:
                    x['session']='Abierta'
                else:
                    x['session']='Cerrada'
                x['session_id']=session[0]['session_id']
            else:
                x['session']='Nuevo'
                x['session_id']=-1
        total_users=db.query("""
            select
                count(a.*)
            from
                system.user_type b,
                system.user a
            where
                a.user_type_id=b.user_type_id
            and a.company_id=%s %s
        """%(company_id,enabled)).dictresult()
        response['success']=True
        response['data']=users
        response['recordsTotal']=total_users[0]['count']
        response['recordsFiltered']=total_users[0]['count']

    except:
        response['success']=False
        response['msg_response']='Ocurrió un error, favor de intentarlo de nuevo.'
        exc_info=sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)

@bp.route('/sendNewPassword', methods=['GET','POST'])
@is_logged_in
def sendNewPassword():
    response={}
    try:
        flag,data=GF.toDict(request.form,'post')
        if flag:
            passwd_success,passwd=GF.generateRandomPassword(8)
            if passwd_success:
                password=generate_password_hash(passwd)
                db.query("""
                    update system.user
                    set password='%s',
                    last_updated=now()
                    where user_id=%s
                """%(password,data['user_id']))
                user_data=db.query("""
                    select name, email, login, company_id from system.user where user_id=%s
                """%data['user_id']).dictresult()
                company_name=db.query("""
                    select name from system.company where company_id=%s
                """%user_data[0]['company_id']).dictresult()[0]
                user_data[0]['password']=passwd
                template=db.query("""
                    select * from template.generic_template where type_id=21
                """).dictresult()[0]
                user_data[0]['mail_img']=cfg.mail_img
                user_data[0]['company']=company_name['name']
                msg=template['body'].format(**user_data[0])
                GF.sendMail(template['subject'],msg,user_data[0]['email'])
                response['success']=True
                response['msg_response']='Se ha enviado la nueva contraseña.'
            else:
                response['success']=False
                response['msg_response']='Ocurrió un error, favor de intentarlo de nuevo.'
        else:
            response['success']=False
            response['msg_response']='Ocurrió un error al intentar obtener la información, favor de intentarlo de nuevo.'
    except:
        response['success']=False
        response['msg_response']="Ocurrió un error, favor de intentarlo de nuevo."
        exc_info=sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)

@bp.route('/closeSession', methods=['GET','POST'])
@is_logged_in
def closeSession():
    response={}
    try:
        flag,data=GF.toDict(request.form,'post')
        if flag:
            db.query("""
                update system.user_session
                set logged=False
                where session_id=%s
                and user_id=%s
            """%(data['session_id'],data['user_id']))
            response['success']=True
            response['msg_response']='La sesión ha sido cerrada.'
        else:
            response['success']=False
            response['msg_response']='Ocurrió un error al intentar obtener los datos, favor de intentarlo de nuevo.'
    except:
        response['success']=False
        response['msg_response']='Ocurrió un error, favor de intentarlo de nuevo más tarde.'
        exc_info=sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)

@bp.route('/unblockUser', methods=['GET','POST'])
@is_logged_in
def unblockUser():
    response={}
    try:
        flag,data=GF.toDict(request.form,'post')
        if flag:
            db.query("""
                update system.user
                set enabled=1,
                login_attempts=0
                where user_id=%s
            """%data['user_id'])
            response['success']=True
            response['msg_response']='El usuario ha sido desbloqueado.'
        else:
            response['success']=False
            response['msg_response']='Ocurrió un error al intentar obtener los datos, favor de intentarlo de nuevo.'
    except:
        response['success']=False
        response['msg_response']='Ocurrió un error, favor de intentarlo de nuevo más tarde.'
        exc_info=sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)

@bp.route('/enableUser', methods=['GET','POST'])
@is_logged_in
def enableUser():
    response={}
    try:
        flag,data=GF.toDict(request.form,'post')
        if flag:
            db.query("""
                update system.user
                set enabled=1
                where user_id=%s
            """%data['user_id'])
            response['success']=True
            response['msg_response']='El usuario ha sido habilitado.'
        else:
            response['success']=False
            response['msg_response']='Ocurrió un error al intentar obtener los datos, favor de intentarlo de nuevo.'
    except:
        response['success']=False
        response['msg_response']='Ocurrió un error, favor de intentarlo de nuevo más tarde.'
        exc_info=sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)
