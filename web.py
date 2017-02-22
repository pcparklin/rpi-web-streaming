#!/usr/bin/python
# coding: utf-8
import os
import time
from subprocess import call, check_output, PIPE

import sqlite3
from flask import Flask, render_template, url_for, redirect, request, g, jsonify
from flask_wtf.csrf import CsrfProtect
from lxml.html import fromstring
from urllib2 import urlopen

app = Flask(__name__)
app.secret_key = os.urandom(24)
CsrfProtect(app)

DATABASE = '/dev/shm/web.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    return render_template('streaming.html')

@app.route('/youtube')
def youtube():
    try:
        pid = check_output(['pgrep', 'ffmpeg'])
    except Exception:
        return render_template('youtube.html')
    else:
        # return render_template('youtube.html', pid=pid)
        return redirect(url_for('overlay', platform='youtube'))

@app.route('/facebook')
def facebook():
    try:
        pid = check_output(['pgrep', 'ffmpeg'])
    except Exception:
        return render_template('facebook.html')
    else:
        # return render_template('facebook.html', pid=pid)
        return redirect(url_for('overlay', platform='facebook'))

@app.route('/connect', methods=['POST'])
def connect():
    if request.form['url'] != '':
        get_db().execute("update OVERLAY set URL=? where ID=1;", (request.form['url'],))
        get_db().commit()

    if request.form['server'] != '' and request.form['key'] != '':
        sound_device = 'hw:1,0'
        destination = '%s/%s' % (request.form['server'], request.form['key'])
        call(['sh', 'reconnect', sound_device, destination], stdout=PIPE, stderr=PIPE)

    if request.form['platform'] in ['youtube', 'facebook']:
        return redirect(url_for(request.form['platform']))
    else:
        return redirect(url_for('index'))

@app.route('/disconnect', methods=['GET'])
def disconnect():
    try:
        call(['sudo', 'killall', 'mmal_video_record', 'ffmpeg'], stdout=PIPE, stderr=PIPE)
    except Exception, e:
        raise e
    else:
        return redirect(url_for(request.args.get('platform')))

def rgb2yuv(rgb):
    r = int(rgb[:2], 16)
    g = int(rgb[2:4], 16)
    b = int(rgb[4:6], 16)

    return (
        int(r * .299000 + g * .587000 + b * .114000),
        int(r * -.168736 + g * -.331264 + b * .500000 + 128),
        int(r * .500000 + g * -.418688 + b * -.081312 + 128)
    )

@app.route('/_update_overlay', methods=['POST'])
def update_overlay():
    try:
        x = int(request.form['x'])
        y = int(request.form['y'])
        text = request.form['text']
        color = request.form['color']
        if x >= 0 and y >= 0:
            yuv = rgb2yuv(color)
            now = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
            get_db().execute("update OVERLAY set X=?, Y=?, TEXT=?, COLOR=?, PY=?, PU=?, PV=?, MODIFIED=? where ID=1;",
                (x, y, text, color, yuv[0], yuv[1], yuv[2], now))
            get_db().commit()
            return jsonify({'msg':'Update Succeed!', 'modified': now});
        else:
            return jsonify({'msg':'invalid x, y input'});
    except:
        return jsonify({'msg':'invalid input'});

@app.route('/overlay', methods=['GET'])
def overlay():
    try:
        overlay = query_db('select * from OVERLAY limit 1;', one=True)
        if overlay is None:
            return 'No such setting'
        else:
            tree = fromstring(urlopen(overlay[8]).read())
            videoId = tree.xpath(".//meta[@itemprop='videoId']/@content")[0]
            return render_template('overlay.html', overlay={
                'x': overlay[1], 'y': overlay[2], 'text': overlay[3], 'color': overlay[4],
                'videoId': videoId, 'modified': overlay[9], 'platform': request.args.get('platform')
            })
    except:
        return 'Something wrong...'

if __name__ == '__main__':
    app.run(passthrough_errors=False, host='0.0.0.0')