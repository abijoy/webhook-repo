from collections import defaultdict
from flask import Blueprint, json, request, render_template, jsonify
from bson.json_util import dumps, loads
from bson.objectid import ObjectId
import datetime
import ast
# from pymongo import json_util 

from flask.wrappers import Request
import pymongo
from pymongo.message import update
from app.extensions import db

webhook = Blueprint('Webhook', __name__, url_prefix='/webhook')

tasks = db.tasks 
cache_tasks = {}
cursor = tasks.find().sort('timestamp', pymongo.DESCENDING)
list_cur = list(cursor)
cache_tasks['task'] = list_cur
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
    return datetime.datetime(*date, *time)


@webhook.route('/get/update')
def get_update():
    cursor = tasks.find().sort('timestamp', pymongo.DESCENDING)
    list_cur = list(cursor)
    if cache_tasks.get('task'):
        print("CACHED!!!")
        if list_cur == cache_tasks['task']:
            # print(list_cur)
            print("NO CHANGES!!")
            return {}
        else:
            # print(list_cur)
            print("UPDATES AVAILABLE")

            _list_cur = list(map(lambda x: str(x), list_cur))
            _list_tasks = list(map(lambda x: str(x), cache_tasks['task']))
            _diff = set(_list_cur).symmetric_difference(set(_list_tasks))
            diff = list(map(lambda x: eval(x), _diff))
            print(diff)

            cache_tasks['task'] = list_cur
            # diff = list(map(lambda x: eval(x), _diff))
            # print(diff)
            # diff = list(map(lambda x: ast.literal_eval(x), _diff))
            return dumps(diff)
    # else:
    #     cache_tasks['task'] = list_cur
    tasks_json = dumps(list_cur)
    return tasks_json


@webhook.route('/')
def api_root():
    return render_template('webhook.html', tasks=list_cur)

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

            timestamp = datetime.datetime.utcfromtimestamp(post_info['repository']['pushed_at'])
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
            
            if post_info['action'] == 'synchronize':
                return {}, 200
            
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
