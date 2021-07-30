from collections import defaultdict
from flask import Blueprint, json, request, render_template, jsonify
from bson.json_util import dumps

from datetime import datetime
# from pymongo import json_util 

from flask.wrappers import Request
import pymongo
from pymongo.message import update
from app.extensions import db

webhook = Blueprint('Webhook', __name__, url_prefix='/webhook')
tasks = db.tasks 
# mongo = extensions.mongo
# print(webhook)

# @webhook.route('/')
# def api_root():
#     # print(db)
#     return 'Welcome guys'

def datetime_utc_convert(dateTime: str):
    # print(f"#####{dateTime}####")
    _date, _time = dateTime[:-1].split('T')
    _date = _date.split('-')
    _time = _time.split(':')
    print(_date, _time)
    date = list(map(lambda x: int(x), _date))
    time = list(map(lambda x: int(x), _time))
    return datetime(*date, *time)


@webhook.route('/get/update')
def get_update():
    cursor = tasks.find().sort('timestamp', pymongo.DESCENDING)
    list_cur = list(cursor)
    tasks_json = dumps(list_cur)
    return tasks_json


@webhook.route('/')
def api_root():
    return render_template('webhook.html')

@webhook.route('/receiver', methods=["POST"])
def receiver():
    if request.headers['Content-Type'] == 'application/json':

        task = {}

        post_info = json.dumps(request.json, indent=4)
        post_info = request.json
        event = dict(request.headers)['X-Github-Event']
        if event == 'push':
            request_id = post_info['after']
            task['request_id'] = request_id

            author = post_info['pusher']['name']
            task['author'] = author
            
            task['action'] = 'PUSH'

            to_branch = post_info['ref'].split("/")[-1]
            task['from_branch'] = to_branch
            task['to_branch'] = to_branch

            timestamp = datetime.utcfromtimestamp(post_info['repository']['pushed_at'])
            task['timestamp'] = timestamp

            print(f'"{author}" pushed to {to_branch} on {timestamp}')
        if event == "pull_request":
            request_id = post_info['pull_request']['id']
            task['request_id'] = request_id
            
            from_branch = post_info['pull_request']['head']['ref']
            to_branch = post_info['pull_request']['base']['ref']
            author = ""
            action = "PULL_REQUEST"
            timestamp = None
            if post_info['action'] == 'opened':
                author = post_info['pull_request']['user']['login']
                created_at = post_info['pull_request']['created_at']
                timestamp = datetime_utc_convert(created_at)
                print(f'{author} submitted a pull request from {from_branch} to {to_branch} on {created_at}')
            if post_info['action'] == 'closed':
                action = "MERGE"
                author = post_info['pull_request']['merged_by']['login']
                merged_at = post_info['pull_request']['merged_at']
                timestamp = datetime_utc_convert(merged_at)
                print(f'{author} merged branch {from_branch} to {to_branch} on {merged_at}')
            
            task['author'] = author
            task['action'] = action
            task['from_branch'] = from_branch
            task['to_branch'] = to_branch
            task['timestamp'] = timestamp
            
        print(task)
        tasks.insert_one(task)
        # print(f' by ')
        # print(type(post_info))
        return post_info
    return {}, 200
