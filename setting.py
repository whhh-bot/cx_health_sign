# -*- coding: utf8 -*-
import os
import yaml


class Setting(object):
    def __init__(self):
        self._abs_path = os.path.split(os.path.realpath(__file__))[0]
        self.setting_path = self._abs_path + "/setting.yaml"
        self.setting: dict = {}
        self._load_setting()
        self._users: dict = {}
        self._check_users()
        self.user_list: list = []
        global_api: dict = self.setting.get('global_send', {})
        self.global_api: dict = {} if global_api is None else global_api

    def _load_setting(self):
        if not os.path.exists(self.setting_path):
            with open(self.setting_path, 'w') as f:
                config = dict(global_send={}, users={})
                yaml.dump(config, f)
        with open(self.setting_path, 'r', encoding='utf-8') as f:
            setting = yaml.load(f, Loader=yaml.FullLoader)
        self.setting = setting

    def _save_setting(self) -> bool:
        with open(self.setting_path, 'w') as f:
            yaml.dump(self.setting, f)
            return True

    def _check_users(self):
        users = self.setting.get('users')
        users = {} if users is None else users
        save_requite = False
        for user in list(users.keys()):
            if 'username_' in user:
                users.pop(user)
                save_requite = True
        self._users: dict = users
        if save_requite:
            self.setting['users'] = users
            self._save_setting()

    def get_users(self, post_type=None) -> list:
        self._check_users()
        users = self._users
        user_list = []
        for username in list(users.keys()):
            if users[username]['post_type'] == post_type or post_type is None:
                user = {
                    'username': username,
                    'password': users[username]['password'],
                    'post_type': users[username]['post_type'].split('|'),
                    'school_id': users[username].get('school_id', ''),
                    'api_type': users[username].get('api_type', 0),
                    'api_key': users[username].get('api_key', '')
                }
                user_list.append(user)
        self.user_list = user_list
        return self.user_list

    def add_user(self, username: str, password: str, post_type: list, school_id='', api_type=0, api_key='') -> bool:
        post_type = '|'.join(post_type)
        user_info = dict(
            password=password, post_type=post_type, school_id=school_id,
            api_type=api_type, api_key=api_key
        )
        user = {username: user_info}
        self._users.update(user)
        self.setting['users'] = self._users
        save_result = self._save_setting()
        if save_result:
            self._load_setting()
            self._check_users()
        return save_result

    def set_global_send(self, api_type, api_key):
        global_api = dict(api_type=api_type, api_key=api_key)
        global_send = {
            'global_send': global_api
        }
        self.setting.update(global_send)
        save_result = self._save_setting()
        if save_result:
            self._load_setting()
            self.global_api: dict = self.setting['global_send']
        return save_result


class GitHub(object):
    """
    用于 GitHub Actions
    """

    def __init__(self):
        self._new_users_raw = os.environ.get('new_users', '')
        self._new_users_raw = self._new_users_raw.replace('；', ';')
        self._new_users_raw = self._new_users_raw.replace('，', ',')
        self._new_users_raw = self._new_users_raw.split(';')
        self._new_global_api_raw = os.environ.get('new_send', '')
        self._new_global_api_raw = self._new_global_api_raw.replace('，', ',')
        self._new_global_api_raw = self._new_global_api_raw.split(',')

        self._users_raw = os.environ.get('users', '').split(';')
        self._global_api_raw = os.environ.get('send', '').split(',')

        self._new_users: list = []
        self._check_new_users()
        self._users: list = []
        self._check_users()
        if self._new_users:
            self._users: list = self._new_users

        self.user_list: list = []

        self.global_api: dict = {}
        self._check_global_api()

   def _check_new_users(self):
    _new_users = []
    for index, new_user_info_raw in enumerate(self._new_users_raw, 1):
        key_map = {
            'un': 'username',
            'pw': 'password',
            'pt': 'post_type',
            'si': 'school_id',
            'at': 'api_type',
            'ak': 'api_key'
        }
        
        # 用户配置位置标识
        config_location = f"第 {index} 个用户配置: '{new_user_info_raw}'"
        new_user_info = new_user_info_raw.split(',')
        new_user = {}
        
        for item in new_user_info:
            if '=' not in item:
                print(f"::warning::忽略无效配置项 '{item}' ({config_location})")
                continue
            
            raw_key, raw_value = item.split('=', 1)
            key = key_map.get(raw_key.strip())
            
            if not key:
                print(f"::warning::忽略未知键 '{raw_key}' ({config_location})")
                continue
            
            value = raw_value.strip()
            
            # 处理 api_type 类型转换
            if key == 'api_type':
                try:
                    value = int(value)
                except ValueError:
                    raise ValueError(
                        f"配置错误 ({config_location})\n"
                        f"API类型(api_type)必须是整数，但收到: '{raw_value}'"
                    )
            # 处理 post_type 分割
            elif key == 'post_type':
                value = [v.strip() for v in value.split('|') if v.strip()]
            
            new_user[key] = value
        
        # 必需字段验证
        required_fields = ['username', 'password', 'api_type']
        for field in required_fields:
            if field not in new_user:
                raise ValueError(
                    f"配置缺失 ({config_location})\n"
                    f"缺少必需字段: '{field}'"
                )
        
        _new_users.append(new_user)
    
    # 过滤空配置
    self._new_users = [user for user in _new_users if user]
    def _check_users(self):
        _users = []
        for user_info_raw in self._users_raw:
            user_info = user_info_raw.split(',')
            if len(user_info) == 3:
                user = dict(username=user_info[0], password=user_info[1], post_type=user_info[2].split('|'),
                            school_id='', api_type=0, api_key='')
            elif len(user_info) == 4:
                user = dict(username=user_info[0], password=user_info[1], post_type=user_info[2].split('|'),
                            school_id=user_info[3], api_type=0, api_key='')
            elif len(user_info) == 5:
                user = dict(username=user_info[0], password=user_info[1], post_type=user_info[2].split('|'),
                            school_id='', api_type=int(user_info[3]), api_key=user_info[4])
            elif len(user_info) == 6:
                user = dict(username=user_info[0], password=user_info[1], post_type=user_info[2].split('|'),
                            school_id=user_info[3], api_type=int(user_info[4]), api_key=user_info[5])
            else:
                continue
            _users.append(user)
        self._users = _users

    def get_users(self, post_type=None) -> list:
        if not post_type:
            self.user_list = self._users
        else:
            user_list = []
            for user in self._users:
                if user['post_type'] == post_type:
                    user_list.append(user)
            self.user_list = user_list
        return self.user_list

    def _check_global_api(self):
        if self._new_global_api_raw:
            global_api_raw = self._new_global_api_raw
            new = True
        else:
            global_api_raw = self._global_api_raw
            new = False
        if len(global_api_raw) == 2:
            if new:
                # at=1,ak=5
                key_map = {'at': 'api_type', 'ak': 'api_key'}
                global_api = {}
                for global_api_item in global_api_raw:
                    if '=' not in global_api_item:
                        continue
                    key, value = global_api_item.split('=')
                    key = key_map.get(key, '')
                    value = int(value) if key == 'api_type' else value
                    if key != '':
                        global_api[key] = value
                self.global_api = global_api
            else:
                self.global_api = dict(
                    api_type=int(global_api_raw[0]),
                    api_key=global_api_raw[1]
                )
        else:
            self.global_api = dict(api_type=0, api_key='')
