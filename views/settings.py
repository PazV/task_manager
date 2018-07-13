#--*-- coding: utf-8 --*--
from flask import Flask, render_template, flash, redirect, url_for, session, request, logging, Blueprint, g, send_file
from .db_connection import getDB
db = getDB()
from .auth import is_logged_in
import json
import traceback
from . import generic_functions
GF=generic_functions.GenericFunctions()
from flask import current_app as app
import sys
import os

bp = Blueprint('settings', __name__, url_prefix='/settings')

@bp.route('/saveNotificationSettings', methods=['GET','POST'])
def saveNotificationSettings():
    response={}
    try:
        flag,data=GF.toDict(request.form,'post')
        if flag:
            exists=db.query("""
                select count(*)
                from system.notification_settings
                where company_id=%s
            """%data['company_id']).dictresult()[0]
            if exists['count']==0:
                db.insert('system.notification_settings',data)
                response['msg_response']="La configuración ha sido agregada."
            else:
                db.query("""
                    update system.notification_settings
                    set admin_report_frequency='%s',
                    assignee_days='%s',
                    supervisor_days='%s',
                    admin_days='%s'
                    where company_id=%s
                """%(data['admin_report_frequency'],data['assignee_days'],data['supervisor_days'],data['admin_days'],data['company_id']))
                response['msg_response']="La configuración ha sigo actualizada."
            response['success']=True
        else:
            response['msg_response']="Ocurrió un error al intentar obtener la información, favor de intentarlo de nuevo."
            response['success']=False
    except:
        response['success']=False
        response['msg_response']="Ocurrió un error, favor de intentar de nuevo."
        exc_info=sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)

@bp.route('/getNotificationSettings', methods=['GET','POST'])
def getNotificationSettings():
    response={}
    try:
        flag,data=GF.toDict(request.form,'post')
        if flag:
            info=db.query("""
                select
                    notification_settings_id,
                    company_id,
                    admin_report_frequency,
                    assignee_days,
                    supervisor_days,
                    admin_days
                from system.notification_settings
                where company_id=%s
            """%data['company_id']).dictresult()
            if info!=[]:
                response['data']=info[0]
                response['has_info']=True
            else:
                response['has_info']=False
            response['success']=True
        else:
            response['success']=False
            response['msg_response']="Ocurrió un error al intentar obtener la información."
    except:
        response['success']=False
        response['msg_response']="Ocurrió un error, favor de intentarlo nuevamente."
        exc_info=sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)
