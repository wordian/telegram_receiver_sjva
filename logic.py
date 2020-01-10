# -*- coding: utf-8 -*-
#########################################################
# python
import os
import sys
import traceback
import logging
import json

# third-party
import telepot
from telepot import Bot, glance
from telepot.loop import MessageLoop

# sjva 공용
from framework import app, path_app_root, db, scheduler
from framework.job import Job
from framework.logger import get_logger
from framework.util import Util

# 패키지
from .plugin import package_name, logger
from .model import ModelSetting

#########################################################

class Logic(object):
    db_default = {
        'auto_start' : 'False',
        'bot_token' : '',
        'chat_id_receive' : '',
        'chat_id_send' : '',
    }

    mysql_process = None
    current_process = None

    @staticmethod
    def db_init():
        try:
            for key, value in Logic.db_default.items():
                if db.session.query(ModelSetting).filter_by(key=key).count() == 0:
                    db.session.add(ModelSetting(key, value))
            db.session.commit()
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


    @staticmethod
    def plugin_load():
        try:
            logger.debug('%s plugin_load', package_name)
            # DB 초기화 
            Logic.db_init()

            # 편의를 위해 json 파일 생성
            from plugin import plugin_info
            Util.save_from_dict_to_json(plugin_info, os.path.join(os.path.dirname(__file__), 'info.json'))

            # 자동시작 옵션이 있으면 보통 여기서 
            if ModelSetting.query.filter_by(key='auto_start').first().value == 'True':
                Logic.scheduler_start()
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


    @staticmethod
    def plugin_unload():
        try:
            Logic.scheduler_stop()
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


    @staticmethod
    def scheduler_start():
        try:
            if not scheduler.is_include(package_name):
                interval = 60*24
                job = Job(package_name, package_name, interval, Logic.scheduler_function, [u'Telegram Receiver'], False)
                scheduler.add_job_instance(job)
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


    @staticmethod
    def scheduler_stop():
        try:
            pass
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


    @staticmethod
    def setting_save(req):
        try:
            for key, value in req.form.items():
                logger.debug('Key:%s Value:%s', key, value)
                entity = db.session.query(ModelSetting).filter_by(key=key).with_for_update().first()
                entity.value = value
            db.session.commit()
            return True                  
        except Exception as e: 
            logger.error('Exception:%s %s', key)
            logger.error(traceback.format_exc())
            return False


    @staticmethod
    def get_setting_value(key):
        try:
            return db.session.query(ModelSetting).filter_by(key=key).first().value
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


    @staticmethod
    def scheduler_function():
        try:
            logger.debug('scheduler_function')
            Logic.start_wait()
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
    

    # 기본 구조 End
    ##################################################################
    message_loop = None
    bot = None


    @staticmethod
    def start_wait():
        try:
            if Logic.message_loop is None:
                bot_token = ModelSetting.get('bot_token')
                Logic.bot = telepot.Bot(bot_token)
                Logic.message_loop = MessageLoop(Logic.bot, Logic.receive_callback)
                Logic.message_loop.run_as_thread()
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc()) 
    
    @staticmethod
    def receive_callback(msg):
        try:
            content_type, chat_type, chat_id = glance(msg)
            chat_id = str(chat_id)
            if content_type == 'text':
                if msg['text'] == '/bot2':
                    text = json.dumps(Logic.bot.getMe(), indent=2)
                    Logic.send_message(text, [chat_id])
                elif msg['text'] == '/me2':
                    text = json.dumps(msg, indent=2)
                    Logic.send_message(text, [chat_id])
                else:
                    chat_id_receive = ModelSetting.get('chat_id_receive')
                    receive_list = chat_id_receive.split('|')
                    index = -1
                    if chat_id_receive == '':
                        index = 0
                    else:
                        for idx, tmp in enumerate(receive_list):
                            if tmp == chat_id:
                                index = idx
                                break
                    if index != -1:
                        chat_id_send = ModelSetting.get('chat_id_send')
                        tmp = chat_id_send.split('|')[index].split(',')
                        Logic.send_message(msg['text'], tmp)
                
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc()) 

    @staticmethod
    def send_message(text, chat_id_list):
        try:
            #logger.debug('TEXT:%s', text)
            for tmp in chat_id_list:
                #logger.debug('chat id : %s', tmp)
                if tmp != '':
                    Logic.bot.sendMessage(tmp, text, disable_web_page_preview=True)
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc()) 
            logger.debug('Chatid:%s', chat_id_list)