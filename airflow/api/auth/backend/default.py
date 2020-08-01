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
        update_views = {
            'trigger_dag': [('can_trigger', 'Airflow')],
            'delete_dag': [('can_delete', 'Airflow'), ('can_dag_edit', request.args.get('dag_id'))],
            'dag_paused': [('can_paused', 'Airflow'), ('can_dag_edit', request.args.get('dag_id'))],
            'create_pool': [('can_add', 'PoolModelView')],
            'delete_pool': [('can_delete', 'PoolModelView')],
        }
        permissions = update_views.get(function.__name__, [])
        logger.log.error(f"Permissions for request {permissions}")
        for permission in permissions:
            if not appbuilder.sm.has_access(*permission):
                logger.log.error(f"NOT permissioned {permission}")
                return Response("Forbidden", 403)
            else:
                logger.log.error(f"Has permission {permission}")


        # for role in current_user.roles:
        # logger.log.error(f"Role object {appbuilder.sm.has_access('set_running', 'DagRunModelView')}")

        # logger.log.error(f"Function {function.__name__}")

        return function(*args, **kwargs)

    return decorated
