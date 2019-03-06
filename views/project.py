#!/usr/bin/env python
#--*-- coding: utf-8 --*--
from flask import Flask, render_template, flash, redirect, url_for, session, request, logging, Blueprint, g, send_file
from passlib.hash import sha256_crypt
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.utils import secure_filename
from .db_connection import getDB
db = getDB()
from .auth import is_logged_in
import json
import traceback
from flask_mail import Mail, Message
from . import generic_functions
GF = generic_functions.GenericFunctions()
from flask import current_app as app
import sys
import time
import os
import random
import app_config as cfg
import datetime
import time

bp = Blueprint('project', __name__, url_prefix='/project')

@bp.route('/saveProject', methods=['GET','POST'])
@is_logged_in
def saveProject():
    response = {}
    try:
        if request.method == 'POST':
            flag,data = GF.toDict(request.form, 'post')
            if flag:
                if data['new_project_id']==-1:
                    data['created_by'] = data['user_id']
                    data['status_id'] = 1
                    data['resolved_date'] = '1900-01-01 00:00:00'
                    data['last_updated_by'] = data['user_id']
                    new_project = db.insert("task.project",data)
                    response['new']=True
                    response['project_id']=new_project['project_id']
                else:
                    db.query("""
                        update task.project
                        set name='%s',
                        description='%s',
                        deadline='%s 00:00:00',
                        last_updated_by=%s,
                        last_updated=now()
                        where project_id=%s
                    """%(data['name'],data['description'],data['deadline'],data['user_id'],data['new_project_id']))
                    response['new']=False
                response['success']=True
            else:
                response['success'] = False
                response['msg_response'] = 'Ocurrió un error al intentar procesar la información. Favor de intentarlo de nuevo.'

        else:
            response['success'] = False
            response['msg_response'] = 'Ocurrió un error, favor de intentarlo de nuevo.'

    except:
        response['success'] = False
        response['msg_response'] = 'Ocurrió un error.'
        exc_info = sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)

@bp.route('/getProjectInfo', methods=['GET','POST'])
@is_logged_in
def getProjectInfo():
    response = {}
    try:
        if request.method == 'POST':
            flag,data = GF.toDict(request.form, 'post')
            if flag:
                project=db.query("""
                    select
                        a.name,
                        a.description,
                        to_char(a.deadline,'DD-MM-YYYY HH:MI:SS') as deadline,
                        (select name from system.user where user_id=a.created_by) as created_by,
                        to_char(a.last_updated, 'DD-MM-YYYY HH:MI:SS') as last_updated,
                        (select name from system.user where user_id=a.last_updated_by) as last_updated_by
                    from
                        task.project a
                    where
                        a.project_id=%s
                """%data['project_id']).dictresult()
                if project!=[]:
                    html="""
                        <p><b>Nombre: </b>{name}<br><b>Descripción: </b>{description}<br><b>Fecha de vencimiento: </b>{deadline}<br><b>Creado por: </b>{created_by}<br><b>Actualizado por última vez: </b>{last_updated}<br><b>Actualizado por: </b>{last_updated_by}</p>
                    """.format(**project[0])
                    response['html'] = html
                    response['success'] = True
                    response['project_id'] = data['project_id']
                else:
                    response['success'] = False
                    response['msg_response'] = 'El proyecto no fue encontrado. Favor de intentarlo de nuevo.'
            else:
                response['success'] = False
                response['msg_response'] = 'Ocurrió un error al intentar procesar la información. Favor de intentarlo de nuevo.'

        else:
            response['success'] = False
            response['msg_response'] = 'Ocurrió un error, favor de intentarlo de nuevo.'

    except:
        response['success'] = False
        response['msg_response'] = 'Ocurrió un error.'
        exc_info = sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)

@bp.route('/getProjectList', methods=['GET','POST'])
@is_logged_in
def getProjectList():
    response={}
    try:
        if request.method=='POST':
            flag,data=GF.toDict(request.form,'post')
            if flag:
                projects=db.query("""
                    select project_id, name
                    from task.project
                    where company_id=%s and status_id in (1,6)
                """%data['company_id']).dictresult()
                projects.append({'project_id':-1,'name':'Ninguno'})
                response['success']=True
                response['data']=projects
            else:
                response['success']=False
                response['msg_response']='Ocurrió un error al intentar obtener los datos. Favor de intentarlo de nuevo.'
        else:
            response['success']=False
            response['msg_response']='Ocurrió un error. Favor de intentarlo de nuevo.'
    except:
        response['success']=False
        response['msg_response']='Ocurrió un error'
        exc_info=sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)

@bp.route('/getProjects', methods=['GET','POST'])
@is_logged_in
def getProjects():
    response={}
    try:
        if request.method=='POST':
            user_type_id=int(request.form['user_type_id'])
            user_id=int(request.form['user_id'])
            company_id=int(request.form['company_id'])
            first=request.form['first']
            filter=json.loads(request.form['filter'])

            if first=="true":
                response['first']=True
                oldest_project=db.query("""
                    select to_char(deadline,'YYYY-MM-DD') as deadline,
                    to_char(deadline,'DD-MM-YYYY') as deadline_return
                    from task.project
                    where company_id=%s
                    and status_id=1
                    order by deadline asc
                    limit 1
                """%company_id).dictresult()

                newest_project=db.query("""
                    select
                        to_char(deadline,'YYYY-MM-DD') as deadline,
                        to_char(deadline,'DD-MM-YYYY') as deadline_return
                    from task.project
                    where company_id=%s
                    and status_id=1
                    order by deadline desc limit 1
                """%company_id).dictresult()
                status=" and a.status_id=1"
                created_by=""
                search=""
                if oldest_project!=[]:
                    date_from=oldest_project[0]['deadline']
                    date_to=newest_project[0]['deadline']
                    response['date_from']=oldest_project[0]['deadline']
                    response['date_to']=newest_project[0]['deadline']
                else:
                    today=datetime.datetime.now()
                    date_from='%s-%s-01'%(today.year,str(today.month).zfill(2))
                    date_to='%s-%s-%s'%(today.year,str(today.month).zfill(2),str(today.day).zfill(2))
                    response['date_from']=False
                    response['date_to']=False
                date_filter=" and a.deadline between '%s 00:00:00' and '%s 23:59:59'"%(date_from,date_to)
            else:
                response['first']=False
                date_from=filter['from']
                date_to=filter['to']
                status=""
                created_by=""
                search=""
                if filter['status_id']!=-1:
                    status=" and a.status_id=%s"%filter['status_id']
                if filter['created_by']!=-1:
                    created_by=" and a.created_by=%s"%filter['created_by']
                if int(filter['date_type'])==1:
                    date_filter=" and a.created between '%s 00:00:00' and '%s 23:59:59'"%(date_from,date_to)
                else:
                    date_filter=" and a.deadline between '%s 00:00:00' and '%s 23:59:59'"%(date_from,date_to)
                if filter['search']!="":
                    search=" and a.name ilike '%%%s%%'"%filter['search']

            projects=db.query("""
                select
                    a.project_id,
                    a.name,
                    a.description,
                    (select name from system.user where user_id=a.created_by) as created_by,
                    to_char(a.created,'DD-MM-YYYY') as created,
                    to_char(a.deadline,'DD-MM-YYYY') as deadline,
                    (select count(task_id) from task.task where project_id=a.project_id) as tasks,
                    b.description as status
                from
                    task.project a,
                    task.status b
                where
                    company_id=%s
                and a.status_id=b.status_id
                %s %s %s %s
                order by a.name
            """%(company_id,status,created_by,date_filter,search)).dictresult()

            total=db.query("""
                select
                    count(*)
                from
                    task.project a
                where
                    a.company_id=%s
                    %s %s %s %s
            """%(company_id,status,created_by,date_filter,search)).dictresult()

            response['data']=projects
            response['recordsTotal']=total[0]['count']
            response['recordsFiltered']=total[0]['count']
            response['success']=True

        else:
            response['success']=False
            response['msg_response']='Ocurrió un error, cargue la página nuevamente.'
    except:
        response['success']=False
        response['msg_response']='Ocurrió un error, favor de intentarlo de nuevo.'
        exc_info=sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)

@bp.route('/getCreatedBy', methods=['GET','POST'])
@is_logged_in
def getCreatedBy():
    response={}
    try:
        flag,data=GF.toDict(request.form,'post')
        if flag:
            users=db.query("""
                select
                    user_id,
                    name
                from
                    system.user
                where
                    company_id=%s
                and enabled in (1,3)
                order by name
            """%data['company_id']).dictresult()
            users.append({'user_id':-1,'name':'Todos'})
            response['data']=users
            response['success']=True
        else:
            response['success']=False
            response['msg_response']='Ocurrió un error, favor de cargar la página nuevamente.'
    except:
        response['success']=False
        response['msg_response']='Ocurrió un error, favor de intentarlo nuevamente.'
        exc_info=sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)

@bp.route('/getProjectTasks', methods=['GET','POST'])
@is_logged_in
def getProjectTasks():
    response={}
    try:
        if request.method=='POST':
            company_id=int(request.form['company_id'])
            project_id=int(request.form['project_id'])
            tasks=db.query("""
                select
                    a.task_id,
                    a.name,
                    (select name from system.user where user_id=a.supervisor_id) as supervisor,
                    (select name from system.user where user_id=a.assignee_id) as assignee,
                    b.description as status,
                    to_char(a.deadline,'DD-MM-YYYY') as deadline,
                    a.status_id
                from
                    task.status b,
                    task.task a
                where
                    a.project_id=%s
                and a.status_id=b.status_id
                and a.company_id=%s
            """%(project_id,company_id)).dictresult()

            total_tasks=db.query("""
                select count(a.task_id)
                from task.task a
                where a.project_id=%s
                and a.company_id=%s
            """%(project_id,company_id)).dictresult()

            response['data']=tasks
            response['recordsTotal']=total_tasks[0]['count']
            response['recordsFiltered']=total_tasks[0]['count']
            response['success']=True

        else:
            response['success']=False
            response['msg_response']='Ocurrió un error, favor de intentarlo nuevamente.'
    except:
        response['success']=False
        response['msg_response']='Ocurrió un error, favor de intentarlo de nuevo.'
        exc_info=sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)

@bp.route('/getSearchedProjectTasks', methods=['GET','POST'])
@is_logged_in
def getSearchedProjectTasks():
    response={}
    try:
        if request.method=='POST':
            filters=json.loads(request.form['filters'])
            company_id=int(request.form['company_id'])
            user_id=int(request.form['user_id'])
            user_type_id=int(request.form['user_type_id'])
            if int(filters['date_type'])==2:
                date_filter=" and a.deadline between '%s 00:00:00' and '%s 23:59:59' "%(filters['from'],filters['to'])
            else:
                date_filter=" and a.created between '%s 00:00:00' and '%s 23:59:59' "%(filters['from'],filters['to'])
            search_filter=""
            if filters['search']!="":
                search_filter=" and a.name ilike '%%%s%%'"%filters['search']
            status_filter=""
            if int(filters['status_id'])!=-1:
                status_filter=" and a.status_id=%s"%filters['status_id']
            tasks=db.query("""
                select
                    a.task_id,
                    a.name,
                    to_char(a.deadline,'DD-MM-YYYY') as deadline,
                    (select name from system.user where user_id=a.supervisor_id) as supervisor,
                    (select name from system.user where user_id=a.assignee_id) as assignee,
                    b.description as status
                from
                    task.status b,
                    task.task a
                where
                    a.company_id=%s
                and a.status_id=b.status_id
                %s %s %s
            """%(company_id,status_filter,date_filter,search_filter)).dictresult()
            task_total=db.query("""
                select count(a.task_id)
                from task.task a
                where a.company_id=%s
                and a.status_id=%s %s %s
            """%(company_id,filters['status_id'],date_filter,search_filter)).dictresult()
            response['data']=tasks
            response['recordsTotal']=task_total[0]['count']
            response['recordsFiltered']=task_total[0]['count']
            response['success']=True
        else:
            response['success']=False
            response['msg_response']='Ocurrió un error, favor de intentarlo de nuevo.'
    except:
        response['success']=False
        response['msg_response']='Ocurrió un error, favor de intentarlo de nuevo.'
        exc_info=sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)

#revisa si la tarea ya se encuentra agregada a algún proyecto
@bp.route('/checkTaskProject', methods=['GET','POST'])
@is_logged_in
def checkTaskProject():
    response={}
    try:
        flag,data=GF.toDict(request.form,'post')
        if flag:
            #obtiene id del proyecto de la tarea seleccionada
            task_project=db.query("""
                select project_id from task.task
                where task_id=%s
            """%data['task_id']).dictresult()
            app.logger.info(type(task_project[0]['project_id']))
            if task_project!=[]:
                if int(task_project[0]['project_id'])!=-1:
                    project_name=db.query("""
                        select name from task.project where project_id=%s
                    """%task_project[0]['project_id']).dictresult()
                    response['success']=True
                    response['needs_confirm']=True
                    response['msg_response']='La tarea se encuentra asignada al proyecto %s, ¿Desea continuar?'%project_name[0]['name']
                else:
                    response['success']=True
                    response['needs_confirm']=False
            else:
                response['success']=False
                response['msg_response']='Ocurrió un problema al obtener los datos de la tarea seleccionada, favor de intentarlo de nuevo más tarde.'
        else:
            response['success']=False
            response['msg_response']='Ocurrió un error, favor de intentarlo de nuevo.'
    except:
        response['success']=False
        response['msg_response']='Ocurrió un error, favor de intentarlo de nuevo más de tarde.'
        exc_info=sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)

@bp.route('/addTaskToProject', methods=['GET','POST'])
@is_logged_in
def addTaskToProject():
    response={}
    try:
        flag,data=GF.toDict(request.form,'post')
        if flag:
            #buscar proyecto al que está asignada la tarea.
            task_project=db.query("""
                select project_id
                from task.task
                where task_id=%s
            """%data['task_id']).dictresult()
            if task_project!=[]:
                if int(task_project[0]['project_id'])==int(data['project_id']):
                    response['success']=False
                    response['msg_response']='La tarea ya se encuentra agregada al proyecto.'
                else:
                    db.query("""
                        update task.task
                        set project_id=%s,
                        last_updated=now(),
                        user_last_updated=%s
                        where task_id=%s
                    """%(data['project_id'],data['user_id'],data['task_id']))
                    db.query("""
                        update task.project
                        set last_updated=now(),
                        last_updated_by=%s
                        where project_id=%s
                    """%(data['user_id'],data['project_id']))
                    response['success']=True
                    response['msg_response']='La tarea ha sido agregada al proyecto.'
            else:
                response['success']=False
                response['msg_response']='Ocurrió un problema al intentar obtener los datos del proyecto, favor de intentarlo de nuevo más tarde.'
        else:
            response['success']=False
            response['msg_response']='Ocurrió un error, favor de intentarlo de nuevo más tarde.'
    except:
        response['success']=False
        response['msg_response']='Ocurrió un error, favor de intentarlo de nuevo más tarde.'
        exc_info=sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)

@bp.route('/removeTaskFromProject', methods=['GET','POST'])
@is_logged_in
def removeTaskFromProject():
    response={}
    try:
        flag,data=GF.toDict(request.form, 'post')
        if flag:
            db.query("""
                update task.task
                set project_id=-1
                where task_id=%s
            """%data['task_id'])
            db.query("""
                update task.project
                set last_updated=now(),
                last_updated_by=%s
                where project_id=%s
            """%(data['user_id'],data['project_id']))
            response['success']=True
            response['msg_response']='La tarea ha sido eliminada del proyecto.'
        else:
            response['success']=False
            response['msg_response']='Ocurrió un error al intentar obtener los datos de la tarea, favor de intentarlo de nuevo más tarde.'
    except:
        response['success']=False
        response['msg_response']='Ocurrió un error, favor de intentarlo de nuevo más tarde.'
        exc_info=sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)

@bp.route('/deleteProject', methods=['GET','POST'])
@is_logged_in
def deleteProject():
    response={}
    try:
        flag,data=GF.toDict(request.form,'post')
        if flag:
            db.query("""
                update task.task
                set project_id=-1
                where project_id=%s
            """%data['project_id'])
            db.query("""
                delete from task.project where project_id=%s
            """%data['project_id'])
            response['success']=True
            response['msg_response']='El proyecto ha sido eliminado.'
        else:
            response['success']=False
            response['msg_response']='Ocurrió un error al intentar obtener los datos del proyecto, favor de intentarlo de nuevo.'
    except:
        response['success']=False
        response['msg_response']='Ocurrió un error, favor de intentarlo de nuevo más tarde.'
        exc_info=sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)

@bp.route('/getRecipientsInfo', methods=['GET','POST'])
@is_logged_in
def getRecipientsInfo():
    response={}
    try:
        flag,data=GF.toDict(request.form,'post')
        if flag:
            project_user=db.query("""
                select created_by from task.project where project_id=%s
            """%data['project_id']).dictresult()
            task_users=db.query("""
                select
                    supervisor_id,
                    assignee_id,
                    created_by
                from
                    task.task
                where
                    project_id=%s
            """%data['project_id']).dictresult()
            users=[]
            users.append(str(int(project_user[0]['created_by'])))
            for x in task_users:
                users.append(str(int(x['supervisor_id'])))
                users.append(str(int(x['assignee_id'])))
                users.append(str(int(x['created_by'])))
            unique_users=list(set(users))
            user_list=','.join(unique_users)

            users_info=db.query("""
                select user_id, name from system.user where user_id in (%s)
            """%user_list).dictresult()
            html=''
            div='''
                <div class="custom-control custom-checkbox" style="margin-left:10px;">
                    <input type="checkbox" class="custom-control-input" id="check_user_{user_id}" name="user_id_{user_id}">
                    <label class="custom-control-label" for="check_user_{user_id}">{name}</label>
                </div>
            '''

            for u in users_info:
                html+=div.format(**u)

            sender=db.query("""
                select user_id, name from system.user where user_id=%s
            """%data['user_id']).dictresult()
            response['sender']=sender[0]['name']
            response['success']=True
            response['divs']=html
        else:
            response['success']=False
            response['msg_response']='Ocurrió un error al intentar obtener los datos de los usuarios, favor de intentarlo más tarde.'

    except:
        response['success']=False
        response['msg_response']='Ocurrió un error, favor de intentarlo de nuevo más tarde.'
        exc_info=sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)


@bp.route('/sendProjectNotification', methods=['GET','POST'])
@is_logged_in
def sendProjectNotification():
    response={}
    try:
        flag,data=GF.toDict(request.form,'post')
        if flag:
            template=db.query("""
                select * from template.generic_template where type_id=35
            """).dictresult()
            project_info=db.query("""
                select
                    a.name,
                    a.description,
                    (select name from system.user where user_id=a.created_by) as created_by,
                    to_char(a.deadline,'DD-MM-YYYY HH:MI:SS') as deadline,
                    (select name from system.company where company_id=a.company_id) as company
                from
                    task.project a
                where
                    a.project_id=%s
            """%data['project_id']).dictresult()[0]
            task_names=db.query("""
                select
                    name
                from
                    task.task
                where project_id=%s
            """%data['project_id']).dictresult()
            html_task_names=""
            app.logger.info(task_names)
            if task_names!=[]:
                html_task_names=' '.join('<li>%s</li>'%tn['name'] for tn in task_names)

            sender=db.query("""
                select name, email from system.user where user_id=%s
            """%data['sender']).dictresult()
            recipients=[]
            for d in data:
                if d[:8]=='user_id_':
                    if data[d]==True:
                        recipients.append(d.split("user_id_")[1])

            recipients_ids=','.join(recipients)
            recipient_mails=db.query("""
                select email from system.user where user_id in (%s)
            """%recipients_ids).dictresult()
            recipients_mail_list=[]
            for rm in recipient_mails:
                recipients_mail_list.append(rm['email'])
            project_info['msg_from']=sender[0]['name']
            project_info['msg']=data['message'].encode('utf-8')
            project_info['link']=cfg.host
            project_info['mail_img']=cfg.mail_img
            project_info['tasks']=html_task_names
            message=template[0]['body'].format(**project_info)
            # app.logger.info(message)
            GF.sendMail(template[0]['subject'].format(**project_info),message,recipients_mail_list)
            project_notification={
                'project_id':data['project_id'],
                'msg_from':data['sender'],
                'msg_to':recipients_ids,
                'message':data['message'].encode('utf-8'),
                'send_date':'now'
            }
            db.insert("task.project_notification",project_notification)
            response['success']=True
            response['msg_response']='La notificación ha sido enviada.'
        else:
            response['success']=False
            response['msg_response']='Ocurrió un error al intentar obtener los datos del proyecto, favor de intentarlo de nuevo más tarde.'
    except:
        response['success']=False
        response['msg_response']='Ocurrió un error, favor de intentarlo de nuevo más tarde.'
        exc_info=sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)


@bp.route('/getProjectNotificationHistory', methods=['GET','POST'])
@is_logged_in
def getProjectNotificationHistory():
    response={}
    try:
        flag,data=GF.toDict(request.form,'post')
        if flag:
            notif=db.query("""
                select *,
                to_char(send_date,'DD-MM-YYYY HH:MI:SS') as send_date
                from task.project_notification
                where project_id=%s
                order by project_notification_id desc
            """%data['project_id']).dictresult()
            if notif!=[]:
                response['has_messages']=True
                divs=''
                for x in notif:
                    msg_from=db.query("""
                        select name from system.user where user_id=%s
                    """%x['msg_from']).dictresult()[0]
                    msg_to_list=db.query("""
                        select name from system.user where user_id in (%s)
                    """%x['msg_to']).dictresult()
                    msg_to=', '.join(e['name'] for e in msg_to_list)
                    divs+='''
                        <div class="card card-mail"><div class="card-header card-header-mail"><h6><b>De:</b> %s</h6><h6><b>A:</b> %s</h6></div><div class="card-body card-body-mail"><span class="span-mail-date">Enviado: %s</span><hr class="hr-mail-date" /><p class="card-text">%s</p></div></div>
                    '''%(msg_from['name'],msg_to,x['send_date'],x['message'])
                response['messages']=divs
            else:
                response['has_messages']=False
            response['success']=True
        else:
            response['success']=False
            response['msg_response']='Ocurrió un error al intentar obtener los datos del proyecto, favor de intentarlo de nuevo.'
    except:
        response['success']=False
        response['msg_response']='Ocurrió un error, favor de intentarlo de nuevo más tarde.'
        exc_info=sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)
