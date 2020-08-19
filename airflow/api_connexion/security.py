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

from functools import wraps
from typing import Callable, Sequence, Tuple, TypeVar, cast

from flask import Response, current_app

from airflow.api_connexion.exceptions import Unauthenticated

T = TypeVar("T", bound=Callable)  # pylint: disable=invalid-name


def requires_authentication(function: T):
    """Decorator for functions that require authentication"""

    @wraps(function)
    def decorated(*args, **kwargs):
        response = current_app.api_auth.requires_authentication(Response)()
        if response.status_code != 200:
            # since this handler only checks authentication, not authorization,
            # we should always return 401
            raise Unauthenticated(headers=response.headers)
        return function(*args, **kwargs)

    return cast(T, decorated)


def requires_access(permissions: Sequence[Tuple[str, str]]) -> Callable[[T], T]:
    """
    Factory for decorator that checks current user's permissions against required permissions.
    """

    def requires_access_decorator(func: T):
        @wraps(func)
        def wrapped_function(*args, **kwargs):
            appbuilder = current_app.appbuilder
            for permission in permissions:
                if not appbuilder.sm.has_access(*permission):
                    raise PermissionDenied("Forbidden", 403)

            return func(*args, **kwargs)

        return cast(T, wrapped_function)

    return requires_access_decorator
