#--*-- coding: utf-8 --*--
from flask import Flask, render_template, flash, redirect, url_for, session, request, logging, Blueprint, g, send_file
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
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
GF=generic_functions.GenericFunctions()
from flask import current_app as app
#app=Flask(__name__)
import sys
import time
import os
import random
import app_config as cfg
bp = Blueprint('task', __name__, url_prefix='/task')

@bp.route('/getSupervisor',methods=['GET','POST'])
def getSupervisor():
    response={}
    try:
        if request.method=='POST':
            flag,data=GF.toDict(request.form,'post')
            if flag:
                condition=""
                if int(data['user_type_id'])==2:
                    condition=" and user_id=%s"%data['user_id']
                supervisor=db.query("""
                    select
                        user_id as supervisor_id,
                        name
                    from
                        system.user
                    where
                        user_type_id=2
                    and company_id=%s
                    and enabled in (1,3) %s
                """%(int(data['company_id']),condition)).dictresult()
                response['data']=supervisor
                response['success']=True
            else:
                response['success']=False
                response['msg_response']='Ocurrió un error al intentar obtener la información.'
        else:
            response['success']=False
            response['msg_response']='Inténtelo de nuevo.'
    except:
        response['success']=False
        response['msg_response']='Ocurrió un error.'
        exc_info = sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)

@bp.route('/getAssignee',methods=['GET','POST'])
def getAssignee():
    response={}
    try:
        # app.logger.info('Info')
        if request.method=='POST':
            flag,data=GF.toDict(request.form,'post')
            if flag:
                assignee=db.query("""
                    select
                        user_id as assignee_id,
                        name
                    from
                        system.user
                    where
                        user_type_id=3
                    and company_id=%s
                    and enabled in (1,3)
                """%(int(data['company_id']))).dictresult()
                response['data']=assignee
                response['success']=True
            else:
                response['success']=False
                response['msg_response']='Ocurrió un error al intentar obtener la información.'
        else:
            response['success']=False
            response['msg_response']='Inténtelo de nuevo.'
    except:
        response['success']=False
        response['msg_response']='Ocurrió un error.'
        exc_info = sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)

@bp.route('/saveTask',methods=['GET','POST'])
def saveTask():
    response={}
    try:
        flag,data=GF.toDict(request.form,'post')
        if flag:
            app.logger.info(data)
            valid=True
            for k,v in data.iteritems():
                if v=="" or v==None:
                    valid=False
            if valid:
                deadline=time.strptime(data['deadline'],"%Y-%m-%d")
                supervisor_deadline=time.strptime(data['supervisor_deadline'],"%Y-%m-%d")
                assignee_deadline=time.strptime(data['assignee_deadline'],"%Y-%m-%d")
                if assignee_deadline<=supervisor_deadline and supervisor_deadline<=deadline:
                    data['status_id']=1
                    data['created']='now'
                    data['last_updated']='now'
                    data['user_last_updated']=data['user_id']
                    data['created_by']=data['user_id']
                    data['supervisor_deadline']="%s 23:59:59"%data['supervisor_deadline']
                    data['assignee_deadline']="%s 23:59:59"%data['assignee_deadline']
                    data['deadline']="%s 23:59:59"%data['deadline']
                    app.logger.info("antes de insert")
                    app.logger.info(data)
                    new_task=db.insert('task.task',data)
                    documents=json.loads(data['document'])
                    for x in documents:
                        doc={
                            'task_id':new_task['task_id'],
                            'name':x['name'],
                            'document_type_id':x['document_type_id'],
                            'description':x['description']
                        }
                        db.insert('task.document',doc)

                    task_info=db.query("""
                        select
                            (select name from system.user where user_id=a.supervisor_id) as supervisor,
                            a.name,
                            (select name from system.user where user_id=a.assignee_id) as assignee,
                            a.description,
                            to_char(a.assignee_deadline,'DD-MM-YYYY HH24:MI:SS') as assignee_deadline,
                            to_char(a.supervisor_deadline,'DD-MM-YYYY HH24:MI:SS') as supervisor_deadline
                        from
                            task.task a
                        where a.task_id=%s
                    """%new_task['task_id']).dictresult()[0]

                    message=db.query("""
                        select * from template.generic_template where type_id=1
                    """).dictresult()[0]
                    recipient=db.query("""
                        select email from system.user where user_id=%s
                    """%data['assignee_id']).dictresult()[0]['email']
                    msg=message['body'].format(**task_info)
                    GF.sendMail(message['subject'],msg,recipient)

                    response['success']=True
                    response['msg_response']='La tarea ha sido creada.'
                else:
                    response['success']=False
                    msg=""
                    if assignee_deadline>supervisor_deadline:
                        msg+="La fecha límite del auxiliar debe ser igual o menor a la fecha límite del supervisor.<br>"
                    if supervisor_deadline>deadline:
                        msg+="La fecha límite del supervisor debe ser menor o igual a la fecha de vencimiento de la tarea."
                    response['msg_response']=msg
            else:
                response['success']=False
                response['msg_response']="Existen campos vacíos o incompletos."
        else:
            response['success']=False
            response['msg_response']='Ocurrió un error al procesar los datos, inténtelo de nuevo.'
    except:
        response['success']=False
        response['msg_response']='Ocurrió un error, favor de intentarlo de nuevo.'
        exc_info=sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)

@bp.route("/getTask", methods=['GET','POST'])
def getTask():
    response={}
    try:
        if request.method=='POST':
            user_type_id=int(request.form['user_type_id'])
            user_id=int(request.form['user_id'])
            user=""
            deadline=""
            filter=json.loads(request.form['filter'])
            filters=""
            for key,value in filter.iteritems():
                if value!=-1:
                    filters+=" and %s = %s"%(key,value)
            if user_type_id in (1,4,5):
                user=""
                deadline="to_char(a.deadline,'DD-MM-YYYY') as deadline"
            elif user_type_id==2:
                user=" and supervisor_id=%s"%user_id
                deadline="to_char(a.supervisor_deadline,'DD-MM-YYYY') as deadline"
            elif user_type_id==3:
                user=" and assignee_id=%s"%user_id
                deadline="to_char(a.assignee_deadline,'DD-MM-YYYY') as deadline"

            task=db.query("""
                select
                    a.task_id,
                    a.name,
                    a.description,
                    %s,
                    a.supervisor_id,
                    a.assignee_id,
                    to_char(a.created,'DD-MM-YYYY') as created,
                    a.company_id,
                    a.status_id,
                    (select name from system.user where user_id=a.assignee_id) as assignee,
                    (select name from system.user where user_id=a.supervisor_id) as supervisor,
                    b.description as status
                from
                    task.status b,
                    task.task a
                where
                    a.company_id=%s
                and a.status_id=b.status_id
                %s %s
                order by created asc
                offset %s limit %s
            """%(deadline,int(request.form['company_id']),user,filters,int(request.form['start']),int(request.form['length']))).dictresult()
            total=db.query("""
                select
                    count(*)
                from
                    task.status b,
                    task.task a
                where
                    a.company_id=%s
                and a.status_id=b.status_id
                %s %s
            """%(int(request.form['company_id']),user,filters)).dictresult()
            response['data']=task
            response['recordsTotal']=total[0]['count']
            response['recordsFiltered']=total[0]['count']
            response['success']=True
        else:
            response['success']=False
            response['msg_response']='Cargue la página nuevamente.'
    except:
        response['success']=False
        response['msg_response']='Ocurrió un error, favor de intentarlo de nuevo.'
        exc_info=sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)

@bp.route('/getTaskDetails',methods=['GET','POST'])
def getTaskDetails():
    response={}
    try:
        flag,data=GF.toDict(request.form,'post')
        if flag:
            deadline=""
            if data['user_type_id'] in (1,4,5):
                deadline="a.deadline"
            elif data['user_type_id']==2:
                deadline="a.supervisor_deadline"
            elif data['user_type_id']==3:
                deadline="a.assignee_deadline"
            task=db.query("""
                select
                    a.task_id,
                    a.name,
                    a.description,
                    to_char(%s,'DD-MM-YYYY') as deadline,
                    (select name from system.user where user_id=a.assignee_id) as assignee,
                    (select name from system.user where user_id=a.supervisor_id) as supervisor,
                    to_char(a.created,'DD-MM-YYYY') as created,
                    b.description as status,
                    to_char(a.resolved_date,'DD-MM-YYYY HH24:MI:SS') as resolved_date,
                    (select name from system.user where user_id=a.created_by) as created_by,
                    a.comments,
                    a.status_id
                from
                    task.status b,
                    task.task a
                where
                    a.task_id=%s
                and a.status_id=b.status_id
                and a.company_id=%s
            """%(deadline,data['task_id'],data['company_id'])).dictresult()[0]

            documents=db.query("""
                select
                    a.document_id,
                    a.name,
                    b.document_type,
                    a.file_path,
                    to_char(a.loaded,'DD-MM-YYYY HH24:MI:SS') as loaded
                from
                    task.document_type b,
                    task.document a
                where
                    a.task_id=%s
                and a.document_type_id=b.document_type_id
            """%data['task_id']).dictresult()
            if data['from']=='details' or data['from']=='decline':
                doc_list=""
                if documents!=[]:
                    for x in documents:
                        if x['file_path']=="":
                            doc_list+="<li>%s (%s)</li>"%(x['name'],x['document_type'])
                        else:
                            # doc_list+="<li>%s (%s) <br> cargado %s</li>"%(x['name'],x['document_type'],x['loaded'])
                            if task['status_id']==4:
                                random_number=int(random.random()*100000)
                                doc_list+="""
                                    <div style="display:inline-block"><li>%s (%s) <br> cargado %s</li><a href="/task/downloadEvidence/%s_%s" target="_blank" role="button" class="btn btn-danger detail-ev-buttons" data-toggle="tooltip" title="Descargar %s"><i class="fa fa-file-text-o"></i></a></div>
                                """%(x['name'],x['document_type'],x['loaded'],random_number,x['document_id'],x['name'])
                            else:
                                doc_list+="<li>%s (%s) <br> cargado %s</li>"%(x['name'],x['document_type'],x['loaded'])

                if task['resolved_date']=='01-01-1900 00:00:00':
                    resolved_date="--"
                else:
                    resolved_date=task['resolved_date']
                html="""
                    <p><b>Nombre:</b> %s <br> <b>Descripción:</b> %s <br> <b>Fecha límite:</b> %s <br> <b>Supervisa:</b> %s <br> <b>Asignado a:</b> %s <br> <b>Creada:</b> %s <br> <b>Creada por:</b> %s <br> <b>Status:</b> %s <br> <b>Fecha en que se resolvió:</b> %s <br> <b>Evidencias necesarias:</b> <ul>%s</ul></p>
                """%(task['name'],task['description'],task['deadline'],task['supervisor'],task['assignee'],task['created'],task['created_by'],task['status'],resolved_date,doc_list)
            elif data['from']=='resolve':
                html="""
                    <p><b>Nombre:</b> %s <br> <b>Descripción:</b> %s <br> <b>Fecha límite:</b> %s <br> <b>Supervisa:</b> %s <br> <b>Asignado a:</b> %s <br> <b>Status:</b> %s </p>
                """%(task['name'],task['description'],task['deadline'],task['supervisor'],task['assignee'],task['status'])

                documents=db.query("""
                    select
                        a.document_id,
                        a.name,
                        b.document_type,
                        a.description,
                        b.document_extension,
                        a.file_path,
                        to_char(a.loaded,'DD-MM-YYYY HH24:MI:SS') as loaded,
                        a.size
                    from
                        task.document_type b,
                        task.document a
                    where
                        a.task_id=%s
                    and a.document_type_id=b.document_type_id
                """%data['task_id']).dictresult()
                html_docs=[]
                if documents!=[]:
                    for d in documents:
                        doc_ext=eval(d['document_extension'])
                        str_doc_ext=','.join(e for e in doc_ext)
                        data_size=''
                        loaded_date=''
                        classes=''
                        if task['status_id']==6:
                            if d['loaded']!='01-01-1900 00:00:00':
                                loaded_date='cargado %s'%d['loaded']
                                classes='valid-file-field'
                                data_size='data-size="%s"'%d['size']
                            else:
                                classes='file-input'
                        else:
                            classes='file-input'
                            data_size='data-size="0"'

                        input="""<div><label for="input%s%s" class="file-input-label">%s (%s) %s</label><input type="file" id="input%s%s" name="file_%s" lang="es" pattern="%s" class="file-evidence %s" data-toggle="tooltip" title="%s" %s><span id="spninput%s%s" class="error-msg">Error</span><div>"""%(d['document_type'],d['document_id'],d['name'],d['document_type'],loaded_date,d['document_type'],d['document_id'],d['document_id'],str_doc_ext,classes,d['description'],data_size,d['document_type'],d['document_id'])
                        html_docs.append(input)
                response['html_docs']=html_docs
                response['comments']=task['comments']

            elif data['from']=='check':
                assignee_info=db.query("""
                    select
                        to_char(assignee_deadline,'DD-MM-YYYY HH24:MI:SS') as date,
                        comments
                    from task.task
                    where task_id=%s
                """%data['task_id']).dictresult()[0]
                html="""
                    <p><b>Nombre:</b> %s <br> <b>Descripción:</b> %s <br> <b>Fecha límite:</b> %s <br> <b>Supervisa:</b> %s <br> <b>Asignado a:</b> %s <br> <b>Fecha límite de auxiliar:</b> %s <br> <b>Fecha en que se resolvió:</b> %s <br> <b>Comentarios auxiliar:</b> %s </p>
                """%(task['name'],task['description'],task['deadline'],task['supervisor'],task['assignee'],assignee_info['date'],task['resolved_date'],assignee_info['comments'])

                documents=db.query("""
                    select name, document_id
                    from task.document
                    where task_id=%s
                """%data['task_id']).dictresult()
                buttons=""
                random_number=int(random.random()*100000)
                for d in documents:
                    buttons+="""
                        <a href="/task/downloadEvidence/%s_%s" target="_blank" role="button" class="btn btn-success" data-toggle="tooltip" title="Descargar %s">%s</a>
                    """%(random_number,d['document_id'],d['name'],d['name'])
                response['evidence']=buttons

            elif data['from']=='check_declined':
                assignee_info=db.query("""
                    select
                        to_char(assignee_deadline,'DD-MM-YYYY HH24:MI:SS') as date,
                        to_char(last_updated,'DD-MM-YYYY HH24:MI:SS') as last_updated,
                        declining_cause
                    from task.task
                    where task_id=%s
                """%data['task_id']).dictresult()[0]
                html="""
                    <p><b>Nombre:</b> %s <br> <b>Descripción:</b> %s <br> <b>Fecha límite:</b> %s <br> <b>Supervisa:</b> %s <br> <b>Asignado a:</b> %s <br> <b>Fecha límite de auxiliar:</b> %s <br> <b>Fecha en que se declinó:</b> %s <br> <b>Comentarios auxiliar:</b> %s </p>
                """%(task['name'],task['description'],task['deadline'],task['supervisor'],task['assignee'],assignee_info['date'],assignee_info['last_updated'],assignee_info['declining_cause'])

            response['data']=html
            response['success']=True
        else:
            response['success']=False
            response['msg_response']="Ocurrió un error al intentar obtener los detalles de la tarea, favor de intentarlo de nuevo."
    except:
        response['success']=False
        response['msg_response']="Ocurrió un error, favor de intentarlo de nuevo."
        exc_info=sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)

@bp.route('/getDocumentType', methods=['GET','POST'])
def getDocumentType():
    response={}
    try:
        doc_type=db.query("""
            select
                document_type_id,
                document_type
            from
                task.document_type
        """).dictresult()
        response['data']=doc_type
        response['success']=True
    except:
        response['success']=False
        response['msg_response']="Ocurrió un error, favor de intentarlo de nuevo."
        exc_info=sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)

UPLOAD_FOLDER = '%s'%cfg.task_path
ALLOWED_EXTENSIONS = set(['txt', 'pdf'])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/resolveTask', methods=['GET','POST'])
def resolveTask():
    response={}
    try:
        data=request.form.to_dict()
        files_list=eval(data['files_list'])
        frm=request.files
        ev_cont=1
        folder=db.query("""
            select task_folder from system.company where company_id=%s
        """%data['company_id']).dictresult()[0]['task_folder']
        task_folder="task_%s"%data['task_id']
        task_path='%s%s/%s/'%(cfg.task_path,folder,task_folder)
        app.logger.info("files list %s"%files_list)
        app.logger.info(frm)
        if not os.path.exists(task_path):
            #en caso de no existir la carpeta, crea una nueva
            os.makedirs(task_path)
        else:
            #elimina evidencias de la carpeta antes de guardar las nuevas
            if data['status_id']==1:
                for the_file in os.listdir(task_path):
                    file_path = os.path.join(task_path, the_file)
                    if os.path.isfile(file_path):
                        os.unlink(file_path)


        if len(files_list)>0:
            for x in files_list:
                document_id=x.split("_")[1]
                file=frm[x]
                filename = secure_filename(file.filename)
                app.logger.info("filename %s"%filename)
                if os.path.exists("%s%s"%(task_path,filename)):
                    name,ext=os.path.splitext(filename)
                    filename="%s_%s%s"%(name,ev_cont,ext)
                    ev_cont+=1

                file.save(os.path.join(task_path, filename))
                file_size=os.path.getsize(os.path.join(task_path, filename))
                size_MB='%.4f'%(float(file_size)/1024/1024)

                db.query("""
                    update task.document
                    set file_path='%s',
                    file_name='%s',
                    loaded='now',
                    size='%s'
                    where task_id=%s
                    and document_id=%s
                """%(task_path,filename,size_MB,data['task_id'],document_id))
        db.query("""
            update task.task
            set
                resolved_date='now',
                status_id=2,
                comments='%s',
                last_updated='now',
                user_last_updated=%s
            where
                task_id=%s
            and company_id=%s
        """%(data['comments'],data['user_id'],data['task_id'],data['company_id']))

        task_info=db.query("""
            select
                (select name from system.user where user_id=a.supervisor_id) as supervisor,
                a.name,
                (select name from system.user where user_id=a.assignee_id) as assignee,
                a.description,
                to_char(a.assignee_deadline,'DD-MM-YYYY HH24:MI:SS') as assignee_deadline,
                to_char(a.supervisor_deadline,'DD-MM-YYYY HH24:MI:SS') as supervisor_deadline,
                to_char(a.deadline,'DD-MM-YYYY HH24:MI:SS') as deadline,
                to_char(a.resolved_date,'DD-MM-YYYY HH24:MI:SS') as resolved_date,
                notify_admin
            from
                task.task a
            where a.task_id=%s
        """%data['task_id']).dictresult()[0]

        supervisor=db.query("""
            select email from system.user where user_id=(select supervisor_id from task.task
            where task_id=%s)
        """%data['task_id']).dictresult()[0]['email']
        message=db.query("""
            select * from template.generic_template where type_id=2
        """).dictresult()[0]

        msg=message['body'].format(**task_info)
        GF.sendMail(message['subject'],msg,supervisor)
        if task_info['notify_admin']==True: #si está indicado que se debe notificar al administrador al resolver la tarea
            admin=db.query("""
                select name,email from system.user
                where company_id=%s and user_type_id=1
            """%data['company_id']).dictresult()[0]
            task_info['admin']=admin['name']

            message_admin=db.query("""
                select * from template.generic_template where type_id=3
            """).dictresult()[0]

            msg_admin=message_admin['body'].format(**task_info)
            GF.sendMail(message_admin['subject'],msg_admin,admin['email'])

        response['success']=True
        response['msg_response']='La tarea ha sido actualizada'
    except:
        response['success']=False
        response['msg_response']='Mal'
        exc_info=sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)

@bp.route('/pauseResolveTask',methods=['GET','POST'])
def pauseResolveTask():
    response={}
    try:
        data=request.form.to_dict()
        files_list=eval(data['files_list'])
        files=request.files
        app.logger.info("len files")
        app.logger.info(len(files))
        if len(files_list)>0: #if there are files to save
            #check if folder exists
            company_folder=db.query("""
                select task_folder from system.company where company_id=%s
            """%data['company_id']).dictresult()[0]['task_folder']
            path='%s%s/task_%s/'%(cfg.task_path,company_folder,data['task_id'])
            if not os.path.exists(path): #validate if folder exists
                os.makedirs(path) #if it doesn't exists, creates one
            for f in files_list:
                ev_cont=1
                document_id=f.split("_")[1] #get document_id

                #checks if it's already loaded
                is_loaded=db.query("""
                    select
                        (loaded<>'1900-01-01 00:00:00') as is_loaded,
                        file_path,
                        file_name
                    from task.document
                    where document_id=%s
                """%document_id).dictresult()[0]
                if is_loaded['is_loaded']==True: #if it's already loaded
                    remove_file=os.path.join(is_loaded['file_path'],is_loaded['file_name']) #get file path
                    if os.path.isfile(remove_file): #checks if it's a file
                        os.unlink(remove_file) #removes file
                    save_path=is_loaded['file_path'] #path where the file will be saved
                else: #if it hasn't been loaded
                    save_path=path #sets path where files are going to be saved

                file=files[f]
                filename=secure_filename(file.filename)
                if os.path.exists("%s%s"%(save_path,filename)): #if there's already a file with the same name
                    name,ext=os.path.splitext(filename)
                    filename="%s_%s%s"%(name,ev_cont,ext)
                    ev_cont+=1
                file.save(os.path.join(save_path,filename))
                file_size=os.path.getsize(os.path.join(save_path,filename))
                size_MB='%.4f'%(float(file_size)/1024/1024)
                db.query("""
                    update task.document
                    set file_path='%s',
                    file_name='%s',
                    loaded='now',
                    size='%s'
                    where task_id=%s
                    and document_id=%s
                """%(save_path,filename,size_MB,data['task_id'],document_id))
        comments=""
        if data['comments']!="": #checks if there are comments to be saved
            comments=" comments='%s',"%data['comments']
        db.query("""
            update task.task
            set
                status_id=6, %s
                last_updated='now',
                user_last_updated=%s
            where
                task_id=%s
            and company_id=%s
        """%(comments,data['user_id'],data['task_id'],data['company_id']))

        response['success']=True
        response['msg_response']='Los cambios realizados han sido guardados.'
    except:
        response['success']=False
        response['msg_response']='Ocurrió un error, favor de intentarlo de nuevo.'
        exc_info=sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)

@bp.route('/downloadEvidence/<document_id>', methods=['GET','POST'])
@is_logged_in
def downloadEvidence(document_id):
    response={}
    try:
        app.logger.info(" document_id %s"%document_id)
        doc_id=document_id.split("_")[1]
        evidence=db.query("""
            select
                file_name,
                file_path
            from
                task.document
            where
                document_id=%s
        """%doc_id).dictresult()
        path="%s%s"%(evidence[0]['file_path'],evidence[0]['file_name'])
        name=evidence[0]['file_name']
        return send_file(path,attachment_filename=name)
    except:
        response['success']=False
        response['msg_response']='Ocurrió un error'
        exc_info=sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
        return response

@bp.route('/completeTask', methods=['GET','POST'])
def completeTask():
    response={}
    try:
        flag,data=GF.toDict(request.form,'post')
        if flag:
            db.query("""
                update task.task
                set
                    status_id=4,
                    last_updated='now',
                    user_last_updated=%s,
                    supervisor_comments='%s'
                where
                    task_id=%s
                and company_id=%s
            """%(data['user_id'],data['comments'],data['task_id'],data['company_id']))

            task_info=db.query("""
                select
                    (select name from system.user where user_id=a.supervisor_id) as supervisor,
                    a.name,
                    (select name from system.user where user_id=a.assignee_id) as assignee,
                    a.description,
                    to_char(a.assignee_deadline,'DD-MM-YYYY HH24:MI:SS') as assignee_deadline,
                    to_char(a.supervisor_deadline,'DD-MM-YYYY HH24:MI:SS') as supervisor_deadline,
                    to_char(a.deadline,'DD-MM-YYYY HH24:MI:SS') as deadline,
                    to_char(a.resolved_date,'DD-MM-YYYY HH24:MI:SS') as resolved_date,
                    supervisor_comments
                from
                    task.task a
                where a.task_id=%s
            """%data['task_id']).dictresult()[0]

            assignee=db.query("""
                select email from system.user where user_id=(select assignee_id from task.task
                where task_id=%s)
            """%data['task_id']).dictresult()[0]['email']
            message=db.query("""
                select * from template.generic_template where type_id=4
            """).dictresult()[0]

            msg=message['body'].format(**task_info)
            GF.sendMail(message['subject'],msg,assignee)

            response['success']=True
            response['msg_response']='La tarea ha sido cerrada.'
        else:
            response['success']=False
            response['msg_response']='Ocurrió un error al intentar procesar la información.'
    except:
        response['success']=False
        response['msg_response']='Ocurrió un error, favor de intentarlo de nuevo.'
        exc_info=sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)

@bp.route('/incompleteTask', methods=['GET','POST'])
def incompleteTask():
    response={}
    try:
        flag,data=GF.toDict(request.form, 'post')
        if flag:
            db.query("""
                update task.task
                set
                    status_id=1,
                    last_updated='now',
                    user_last_updated=%s,
                    supervisor_comments='%s'
                where
                    task_id=%s
                and company_id=%s
            """%(data['user_id'],data['comments'],data['task_id'],data['company_id']))
            db.query("""
                update task.document
                set loaded=default,
                file_name='',
                size=default
                where task_id=%s
            """%data['task_id'])
            task=db.query("""
                select
                    a.name as task,
                    b.name
                from
                    system.user b,
                    task.task a
                where
                    b.user_id=a.assignee_id
                and task_id=%s
            """%data['task_id']).dictresult()[0]
            response['success']=True
            response['msg_response']='La tarea %s ha sido asignada nuevamente a %s.'%(task['task'],task['name'])
            task_info=db.query("""
                select
                    (select name from system.user where user_id=a.supervisor_id) as supervisor,
                    a.name,
                    (select name from system.user where user_id=a.assignee_id) as assignee,
                    a.description,
                    to_char(a.assignee_deadline,'DD-MM-YYYY HH24:MI:SS') as assignee_deadline,
                    to_char(a.supervisor_deadline,'DD-MM-YYYY HH24:MI:SS') as supervisor_deadline,
                    to_char(a.deadline,'DD-MM-YYYY HH24:MI:SS') as deadline,
                    to_char(a.resolved_date,'DD-MM-YYYY HH24:MI:SS') as resolved_date,
                    supervisor_comments
                from
                    task.task a
                where a.task_id=%s
            """%data['task_id']).dictresult()[0]

            assignee=db.query("""
                select email from system.user where user_id=(select assignee_id from task.task
                where task_id=%s)
            """%data['task_id']).dictresult()[0]['email']
            message=db.query("""
                select * from template.generic_template where type_id=5
            """).dictresult()[0]

            msg=message['body'].format(**task_info)
            GF.sendMail(message['subject'],msg,assignee)

        else:
            response['success']=False
            response['msg_response']='Ocurrió un error al intentar procesar la información.'
    except:
        response['success']=False
        response['msg_response']='Ocurrió un error, favor de intentarlo nuevamente.'
        exc_info=sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)

@bp.route('/declineTask', methods=['GET','POST'])
def declineTask():
    response={}
    try:
        flag,data=GF.toDict(request.form,'post')
        if flag:
            db.query("""
                update task.task
                set
                    status_id=3,
                    declining_cause='%s',
                    last_updated='now',
                    user_last_updated=%s
                where
                    task_id=%s
                and company_id=%s
            """%(data['comments'],data['user_id'],data['task_id'],data['company_id']))
            recipient=db.query("""
                select a.email
                from
                    system.user a,
                    task.task b
                where
                    a.user_id=b.supervisor_id
                and b.task_id=%s
            """%data['task_id']).dictresult()[0]['email']
            task_info=db.query("""
                select
                    (select name from system.user where user_id=a.supervisor_id) as supervisor,
                    a.name,
                    (select name from system.user where user_id=a.assignee_id) as assignee,
                    a.declining_cause,
                    a.description,
                    to_char(a.assignee_deadline,'DD-MM-YYYY HH24:MI:SS') as assignee_deadline,
                    to_char(a.supervisor_deadline,'DD-MM-YYYY HH24:MI:SS') as supervisor_deadline
                from
                    task.task a
                where a.task_id=%s
            """%data['task_id']).dictresult()[0]

            message=db.query("""
                select * from template.generic_template where type_id=6
            """).dictresult()[0]

            msg=message['body'].format(**task_info)
            GF.sendMail(message['subject'],msg,recipient)
            response['success']=True
            response['msg_response']='La tarea ha sido declinada.'
        else:
            response['success']=False
            response['msg_response']='Ocurrió un error al intentar procesar la información.'
    except:
        response['success']=False
        response['msg_response']='Ocurrió un error, favor de intentarlo de nuevo.'
        exc_info=sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)

@bp.route('/updateDeclinedTask', methods=['GET','POST'])
def updateDeclinedTask():
    response={}
    try:
        flag,data=GF.toDict(request.form,'post')
        if flag:
            if data['description']=="":
                db.query("""
                    update task.task
                    set assignee_id=%s,
                    status_id=1,
                    last_updated='now',
                    user_last_updated=%s
                    where task_id=%s
                """%(data['assignee_id'],data['user_id'],data['task_id']))
            else:
                db.query("""
                    update task.task
                    set assignee_id=%s,
                    description='%s',
                    status_id=1,
                    last_updated='now',
                    user_last_updated=%s
                    where task_id=%s
                """%(data['assignee_id'],data['description'],data['user_id'],data['task_id']))
            msg_info=db.query("""
                select * from template.generic_template where type_id=10
            """).dictresult()[0]
            task_info=db.query("""
                select
                    (select a.name from system.user a where a.user_id=assignee_id) as assignee,
                    (select a.email from system.user a where a.user_id=assignee_id) as recipient,
                    (select a.name from system.user a where a.user_id=supervisor_id) as supervisor,
                    name,
                    description,
                    to_char(assignee_deadline, 'DD-MM-YYYY HH24:MI:SS') as assignee_deadline
                from
                    task.task
                where
                    task_id=%s
            """%data['task_id']).dictresult()[0]
            msg=msg_info['body'].format(**task_info)
            GF.sendMail(msg_info['subject'],msg,task_info['recipient'])
            response['success']=True
            response['msg_response']='La tarea ha sido reasignada.'
        else:
            response['success']=False
            response['msg_response']='Ocurrió un error al intentar obtener la información.'
    except:
        response['success']=False
        response['msg_response']='Ocurrió un error, favor de intentarlo de nuevo.'
        exc_info=sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)

@bp.route('/cancelTask', methods=['GET','POST'])
def cancelTask():
    response={}
    try:
        flag,data=GF.toDict(request.form,'post')
        if flag:
            db.query("""
                update task.task
                set status_id=5,
                last_updated='now',
                user_last_updated=%s
                where task_id=%s
            """%(data['user_id'],data['task_id']))

            message_info=db.query("""
                select * from template.generic_template where type_id=11
            """).dictresult()[0]

            task_info=db.query("""
                select
                    (select a.name from system.user a where a.user_id=assignee_id) as assignee,
                    (select a.name from system.user a where a.user_id=supervisor_id) as supervisor,
                    name,
                    description,
                    to_char(assignee_deadline,'DD-MM-YYYY HH24:MI:SS') as assignee_deadline,
                    (select a.email from system.user a where a.user_id=assignee_id) as recipient
                from
                    task.task
                where
                    task_id=%s
            """%data['task_id']).dictresult()[0]
            msg=message_info['body'].format(**task_info)
            GF.sendMail(message_info['subject'],msg,task_info['recipient'])
            response['success']=True
            response['msg_response']="La tarea ha sido cancelada."
        else:
            response['success']=False
            response['msg_response']="Ocurrió un error al intentar obtener la información."
    except:
        response['success']=False
        response['msg_response']="Ocurrió un error, favor de intentarlo de nuevo."
        exc_info=sys.exc_info()
        app.logger.info(traceback.format_exc(exc_info))
    return json.dumps(response)
