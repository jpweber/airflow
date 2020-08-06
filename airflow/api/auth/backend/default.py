# -*- coding: utf-8 -*-
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
"""Default authentication backend - everything is allowed"""
from functools import wraps
from flask import Response, request
from flask_login import current_user
from airflow.www_rbac.app import cached_appbuilder
CLIENT_AUTH = None


def init_app(_):
    """Initializes authentication backend"""


def requires_authentication(function):
    """Decorator for functions that require authentication"""
    
    @wraps(function)
    def decorated(*args, **kwargs):
        from airflow.utils.log.logging_mixin import LoggingMixin
        logger = LoggingMixin()
        appbuilder = cached_appbuilder()
        logger.log.error(f"Security manager {appbuilder.sm}")
        logger.log.error(f"Current user {current_user.__dict__}")
        logger.log.error(f"Roles {current_user.roles}")
        logger.log.error(f"Locals {locals()}")
        logger.log.error(f"Args {args}")
        logger.log.error(f"Kwargs {kwargs}")
        logger.log.error(f"Request {request}")
        # logger.log.error(f"Request.args {request.args.iterlists()}")
        view_permissions = {
            'trigger_dag': [('can_trigger', 'Airflow')],
            'delete_dag': [('can_delete', 'Airflow')],
            'dag_paused': [('can_paused', 'Airflow')],
            'create_pool': [('can_add', 'PoolModelView')],
            'delete_pool': [('can_delete', 'PoolModelView')],
        }

        dag_permissions = {
            'delete_dag': [('can_dag_edit', 'all_dags'), ('can_dag_edit', kwargs.get('dag_id'))],
            'dag_paused': [('can_dag_edit', 'all_dags'), ('can_dag_edit', kwargs.get('dag_id'))],
        }

        permissions = view_permissions.get(function.__name__, [])
        logger.log.error(f"View permissions for request {permissions}")
        func_name = function.__name__
        for permission in view_permissions.get(func_name, []):
            if not appbuilder.sm.has_access(*permission):
                logger.log.error(f"NOT permissioned {permission}")
                return Response("Forbidden", 403)
            else:
                logger.log.error(f"Has permission {permission}")

        if func_name in dag_permissions:
            if any(appbuilder.sm.has_access(*permission) for permission in dag_permissions[func_name]):
                logger.log.error(f"Has func permission {dag_permissions[func_name]}")
            else:
                logger.log.error(f"NOT func permission {dag_permissions[func_name]}")
                return Response("Forbidden", 403)



        # for role in current_user.roles:
        # logger.log.error(f"Role object {appbuilder.sm.has_access('set_running', 'DagRunModelView')}")

        logger.log.error(f"Function {function.__name__}")

        return function(*args, **kwargs)

    return decorated
