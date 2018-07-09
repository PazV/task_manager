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

            order by name
            offset %s limit %s
        """%(company_id,start,limit)).dictresult()
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
        """%company_id).dictresult()
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


# @users.route('/users/<str:company_id>')
# @is_logged_in
# def getUserList(company_id):
