#-*- coding: utf-8 -*-

from flask import Flask, render_template, flash, redirect, url_for, session, request, logging, Blueprint, g
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash
from .db_connection import getDB
import logging
import sys
import traceback
import json
from flask import current_app as app
from . import generic_functions
GF=generic_functions.GenericFunctions()
db = getDB()
import app_config as cfg
bp=Blueprint('auth',__name__, url_prefix='/auth')
# @auth.route('/login')
# def login():
    # return render_template('prueba.html')
#Check if user logged in


# @auth.route('/')
# @is_logged_in
# def main_view():
#     logging.info("main view")
#     #return render_template(url_for('home'))
#     return render_template('home.html')


@bp.route('/login', methods=['GET','POST'])
def login():
    error=''
    if request.method == 'POST':
        login = request.form['username']
        login=login.strip()
        login=login.lower()
        password = request.form['password']
        user = db.query("""
            select * from system.user where login='%s'
        """%(login)).dictresult()

        if user==[]:
            error = 'Usuario no encontrado.'
            flash(u'Usuario no encontrado','user')
        else:
            if user[0]['login_attempts']>3:
                #bloqueado
                db.query("""
                    update system.user set enabled=3 where user_id=%s
                """%user[0]['user_id'])
                error='El usuario se encuentra bloqueado, favor de contactar a su consultor.'
                flash(u'El usuario se encuentra bloqueado, favor de contactar a su consultor.','user')
            elif not check_password_hash(user[0]['password'],password):
                error = 'Contraseña incorrecta.'.decode('utf-8')
                flash(u'Contraseña incorrecta','pass')
                db.query("""
                    update system.user set login_attempts=%s
                    where user_id=%s
                """%(user[0]['login_attempts']+1,user[0]['user_id']))
            else:
                error=''
        if error!='':
            logging.info("error: %s"%error)
            #return render_template('login.html', error=error)
        else:
            #closes all active sessions
            db.query("""
                update system.user_session set logged=False
                where user_id=%s and logged=True
            """%user[0]['user_id'])
            # active_sessions=db.query("""
            #     select count(*) from system.user_session
            #     where user_id=%s and logged=True
            # """%user[0]['user_id']).dictresult()
            # if active_sessions[0]['count']==0:
            new_session={
                'user_id':user[0]['user_id'],
                'start_session':'now',
                'logged':True
            }
            inserted_session=db.insert('system.user_session',new_session)
            session['logged_in']=True
            session['username']=login
            session['user_id']=user[0]['user_id']
            session['session_id']=inserted_session['session_id']
            g.session_id=session['session_id']
            logging.info("Inicia sesión usuario %s"%user[0]['user_id'])
            msg='Inicio de sesión correcto'.decode('utf-8')
            db.query("""
                update system.user set login_attempts=0 where user_id=%s
            """%user[0]['user_id'])
            return redirect(url_for('index'))
            # else:
            #     error='Usted ya tiene una sesión activa.'
            #     flash(u'Usted ya tiene una sesión activa.','main_msg')
    else:
        logging.info("no post")
        # return render_template('login.html')
    return render_template('login.html',error=error)

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            logged=db.query("""
                select logged from system.user_session
                where session_id=%s
            """%session['session_id']).dictresult()

            if logged!=[]:
                if logged[0]['logged']==True:
                    db.query("""
                        update system.user_session
                        set last_action_at=now()
                        where session_id=%s
                    """%session['session_id'])
                    return f(*args, **kwargs)
                else:
                    flash('Unauthorized, Please login', 'danger')
                    return redirect(url_for('auth.login'))
            else:
                flash('Unauthorized, Please login', 'danger')
                return redirect(url_for('auth.login'))
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('auth.login'))
    return wrap

@bp.route('/logout')
@is_logged_in
def logout():

    db.query("""
        update system.user_session
        set finish_session='now',
        logged=False
        where user_id=%s
    """%session['user_id'])
    session.clear()

    return redirect(url_for('auth.login'))

@bp.route('/recoverPassword', methods=['GET','POST'])
def recoverPassword():
    response={}
    try:
        flag,data=GF.toDict(request.form,'post')
        if flag:
            login=data['login'].lower()
            login=login.strip()
            exists=db.query("""
                select * from system.user
                where login='%s' and email='%s'
            """%(data['login'].lower().strip(),data['email'].strip())).dictresult()

            if exists!=[]:
                passwd_success,passwd=GF.generateRandomPassword(8)
                if passwd_success:
                    new_password=generate_password_hash(passwd)
                    db.query("""
                        update system.user
                        set password='%s',
                        last_updated='now'
                        where user_id=%s
                    """%(new_password,exists[0]['user_id']))
                    message=db.query("""
                        select * from template.generic_template where type_id=12
                    """).dictresult()[0]
                    msg_info={
                        'login':exists[0]['login'],
                        'passwd':passwd,
                        'link':cfg.host,
                        'mail_img':cfg.mail_img
                    }
                    company_name=db.query("""
                        select name from system.company where company_id=%s
                    """%exists[0]['company_id']).dictresult()[0]
                    msg_info['company']=company_name['name']
                    msg=message['body'].format(**msg_info)
                    GF.sendMail(message['subject'],msg,exists[0]['email'])

                    response['success']=True
                    response['msg_response']='Se ha enviado un mensaje a su correo con su nueva contraseña.'
                else:
                    response['success']=False
                    response['msg_response']='Ha ocurrido un error al intentar generar su nueva contraseña, favor de intentarlo nuevamente.'
            else:
                response['success']=False
                response['msg_response']='Los datos ingresados no coinciden con ningún usuario registrado, favor de verificarlos.'
        else:
            response['success']=False
            response['msg_response']='Ocurrió un error al intentar obtener los datos, favor de intentarlo nuevamente.'
    except:
        response['success']=False
        response['msg_response']='Ocurrió un error, favor de intentarlo nuevamente.'
        exc_info=sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)
