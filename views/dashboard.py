#--*-- coding: utf-8 --*--
from flask import Flask, render_template, flash, redirect, url_for, session, request, logging, Blueprint, g
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash
from .db_connection import getDB
import logging
db = getDB()
from .auth import is_logged_in
import json


bp = Blueprint('dashboard', __name__ )

# def is_logged_in(f):
#     @wraps(f)
#     def wrap(*args, **kwargs):
#         if 'logged_in' in session:
#             return f(*args, **kwargs)
#         else:
#             flash('Unauthorized, Please login', 'danger')
#             return redirect(url_for('auth.login'))
#     return wrap

@bp.route('/home')
@is_logged_in
def index():
    user_info={
        'user_id':session['user_id'],
        'session_id':session['session_id']
    }
    user_type=db.query("""
        select user_type_id,company_id,login from system.user where
        user_id=%s
    """%session['user_id']).dictresult()
    if user_type!=[]:
        user_info['user_type_id']=user_type[0]['user_type_id']
        user_info['company_id']=user_type[0]['company_id']
    else:
        user_info['user_type_id']=-1
        user_info['company_id']=-1
    g.user_info=json.dumps(user_info)
    g.template_user_info=user_info
    return render_template('home.html')

@bp.route('/')
@is_logged_in
def index2():
    #checks if is logged in, in case it is, redirects to home, if it's not, redirects to auth.login
    return render_template('home.html')

# @bp.route('')
# @is_logged_in
# def index3():
#     return render_template('home.html')
