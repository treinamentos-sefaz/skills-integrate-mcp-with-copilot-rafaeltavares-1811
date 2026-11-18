import json
import tempfile
import time
import unittest
from http.cookies import SimpleCookie
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException, Response
from starlette.requests import Request

from src import app as app_module
from src import auth


class TeacherAuthTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.credentials_file = Path(self.temp_dir.name) / "teachers.json"
        self.credentials_patch = patch.object(auth, "CREDENTIALS_FILE", self.credentials_file)
        self.credentials_patch.start()
        self.credentials_file.write_text(
            json.dumps(
                {
                    "teachers": [
                        {
                            "username": "teacher1",
                            **auth.create_password_record("teacher-password-123"),
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        self.sessions_patch = patch.dict(
            app_module.active_teacher_sessions, {}, clear=True
        )
        self.sessions_patch.start()

    def tearDown(self):
        self.sessions_patch.stop()
        self.credentials_patch.stop()
        self.temp_dir.cleanup()

    @staticmethod
    def make_request(cookie_value=None):
        headers = []
        if cookie_value is not None:
            headers.append(
                (
                    b"cookie",
                    f"{app_module.TEACHER_SESSION_COOKIE}={cookie_value}".encode(),
                )
            )
        return Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/",
                "headers": headers,
                "query_string": b"",
                "server": ("testserver", 80),
                "client": ("testclient", 12345),
                "scheme": "http",
            }
        )

    def test_password_is_verified_against_teacher_file(self):
        self.assertTrue(
            auth.verify_teacher_credentials("teacher1", "teacher-password-123")
        )
        self.assertFalse(
            auth.verify_teacher_credentials("teacher1", "wrong-password")
        )
        self.assertFalse(
            auth.verify_teacher_credentials("unknown", "teacher-password-123")
        )

    def test_login_creates_session_and_logout_revokes_it(self):
        response = Response()
        app_module.login(
            app_module.TeacherLogin(
                username="teacher1", password="teacher-password-123"
            ),
            response,
        )

        cookie = SimpleCookie()
        cookie.load(response.headers["set-cookie"])
        session_id = cookie[app_module.TEACHER_SESSION_COOKIE].value
        request = self.make_request(session_id)
        self.assertEqual(app_module.require_teacher(request), "teacher1")

        app_module.logout(request, Response())
        with self.assertRaises(HTTPException) as error:
            app_module.require_teacher(request)
        self.assertEqual(error.exception.status_code, 401)

    def test_invalid_password_does_not_create_a_session(self):
        response = Response()
        with self.assertRaises(HTTPException) as error:
            app_module.login(
                app_module.TeacherLogin(
                    username="teacher1", password="incorrect-password"
                ),
                response,
            )

        self.assertEqual(error.exception.status_code, 401)
        self.assertEqual(app_module.active_teacher_sessions, {})
        self.assertNotIn("set-cookie", response.headers)

    def test_activity_mutations_require_teacher_dependency(self):
        protected_routes = {
            ("/activities/{activity_name}/signup", "POST"),
            ("/activities/{activity_name}/unregister", "DELETE"),
        }
        for route in app_module.app.routes:
            if not hasattr(route, "dependant"):
                continue
            for method in route.methods or set():
                route_key = (route.path, method)
                if route_key not in protected_routes:
                    continue
                self.assertTrue(
                    any(
                        dependency.call is app_module.require_teacher
                        for dependency in route.dependant.dependencies
                    )
                )
                protected_routes.remove(route_key)

        self.assertEqual(protected_routes, set())

    def test_expired_session_is_rejected(self):
        session_id = "expired-session"
        app_module.active_teacher_sessions[session_id] = (
            "teacher1",
            time.time() - 1,
        )

        with self.assertRaises(HTTPException) as error:
            app_module.require_teacher(self.make_request(session_id))
        self.assertEqual(error.exception.status_code, 401)


if __name__ == "__main__":
    unittest.main()
