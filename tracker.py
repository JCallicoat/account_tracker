#!/usr/bin/env python

import os
import sys
import sqlite3
import time
import re
import markdown
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, make_response, json
from contextlib import closing


__version__ = 0.5

DATABASE = 'tracker.db'
DEBUG = True
SECRET_KEY = 'abcdefg'
USERNAME = 'admin'
PASSWORD = 'default'


app = Flask(__name__)
app.config.from_object(__name__)
# app.config.from_envvar('app.config', silent=True)
app.config['version'] = __version__

md = markdown.Markdown(safe_mode=False)


def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('tracker.sql') as f:
            db.cursor().executescript(f.read())
        db.commit()


def connect_db():
    return sqlite3.connect(app.config['DATABASE'])


def query_db(query, args=(), one=False):
    cur = g.db.execute(query, args)
    if one:
        rows = (cur.fetchone(),)
    else:
        rows = cur.fetchall()
    if not rows:
        return []
    rv = [dict((cur.description[idx][0], value)
          for idx, value in enumerate(row)) for row in rows if row]
    return (rv[0] if rv else None) if one else rv


@app.before_request
def before_request():
    g.db = connect_db()


@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()


@app.route('/')
def show_entries():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    entries = query_db('''select * from customers where deleted=0
                          order by id asc''')
    if request.content_type == 'application/json':
        return json.dumps(entries)
    else:
        return render_template('show_entries.html', entries=entries)


@app.route('/<int:account_id>')
def show_account(account_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    account = query_db('select * from customers where deleted=0 and id=?',
                       (account_id,), one=True)
    if request.content_type == 'application/json':
        if not account:
            return '{"Error": "Account not found"}', 404
        else:
            return json.dumps(account)
    else:
        if not account:
            return render_template('show_account.html', account=account), 404
        else:
            account['created_at'] = (time.ctime(account['created_at'])
                                    + ' (UTC)')
            account['updated_at'] = (time.ctime(account['updated_at'])
                                    + ' (UTC)')
            return render_template('show_account.html', account=account, md=md)


@app.route('/add_account', methods=['GET', 'POST'])
def add_account():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if request.method == 'GET':
        return render_template('add_account.html')
    else:
        timestamp = time.time()
        g.db.execute('''insert into customers
            (account_name, account_number, controller_ip, controller_id,
             admin_user, admin_pass, notes, created_at, updated_at, deleted)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)''',
            (request.form['account_name'], request.form['account_number'],
             request.form['controller_ip'], request.form['controller_id'],
             request.form['admin_user'], request.form['admin_pass'],
             request.form['notes'], timestamp, timestamp))
        g.db.commit()
        flash('New account was successfully posted')
        return redirect(url_for('show_entries'))


@app.route('/<int:account_id>/edit', methods=['GET', 'POST'])
def edit_account(account_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    account = query_db('select * from customers where deleted=0 and id=?',
                       (account_id,), one=True)
    if request.method == 'GET':
        if request.content_type == 'application/json':
            if not account:
                return '{"Error": "Account not found"}', 404
            else:
                return json.dumps(account)
        else:
            if not account:
                return redirect(url_for('show_account', account_id=account_id))
            else:
                return render_template('edit_account.html', account=account)
    else:
        if request.content_type == 'application/json':
            pass
        else:
            timestamp = time.time()
            g.db.execute('''insert or replace into customers
                (id, account_name, account_number, controller_ip,
                 controller_id, admin_user, admin_pass, notes, created_at,
                 updated_at, deleted)
                values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)''',
                (account_id, request.form['account_name'],
                 request.form['account_number'], request.form['controller_ip'],
                 request.form['controller_id'], request.form['admin_user'],
                 request.form['admin_pass'], request.form['notes'],
                 account['created_at'], timestamp))
            g.db.commit()
            flash('Account was successfully edited')
            return redirect(url_for('show_account', account_id=account_id))


@app.route('/search', methods=['GET', 'POST'])
def search():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if request.method == 'GET':
        return render_template('search.html')
    else:
        search_by = request.form.get('search_by')
        search_text = request.form.get('search_text')
        if request.content_type == 'application/json':
            search_by = request.json.get('search_by')
            search_text = request.json.get('search_text')
        print(search_by, search_text)
        search_regexp = re.compile(search_text)
        entries = query_db('''select * from customers where deleted=0
                              order by id asc''')
        entries = [entry for entry in entries
                   if search_regexp.search(str(entry[search_by]))]
        if request.content_type == 'application/json':
            return json.dumps(entries)
        else:
            return render_template('show_entries.html', entries=entries)


def _format_error(request, error):
    if request.content_type == 'application/json':
        return make_response('{"Error": "%s"}' % error, 401)
    else:
        return render_template('login.html', error=error), 401


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if request.content_type == 'application/json':
            auth = request.json.get('auth')
            if auth:
                username = auth.get('username')
                password = auth.get('password')
            else:
                return _format_error(request, 'Invalid JSON')

        if username != app.config['USERNAME']:
            return _format_error(request, 'Invalid username')

        elif password != app.config['PASSWORD']:
            return _format_error(request, 'Invalid password')

        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))

    return render_template('login.html', error=None, hide_login=True), 401


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))


if __name__ == '__main__':
    if '-c' in sys.argv:
        init_db()
    else:
        app.run()
