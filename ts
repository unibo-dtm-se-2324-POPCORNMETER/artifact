[1mdiff --git a/popcorn_meter/ui/streamlit_app.py b/popcorn_meter/ui/streamlit_app.py[m
[1mindex aa189d4..7c7287f 100644[m
[1m--- a/popcorn_meter/ui/streamlit_app.py[m
[1m+++ b/popcorn_meter/ui/streamlit_app.py[m
[36m@@ -99,8 +99,9 @@[m [mdef movie_card(title: str, meta: str = ""):[m
 [m
 # Repo + app service[m
 repo = SqliteRepo("popcorn_meter.db")[m
[31m-app = AppService(repo)[m
 omdb = OmdbClient()[m
[32m+[m[32mapp = AppService(repo,omdb)[m
[32m+[m
 [m
 # Session[m
 if "session_user" not in st.session_state:[m
[1mdiff --git a/tests/__init__.py b/tests/__init__.py[m
[1mindex fffe191..e69de29 100644[m
[1m--- a/tests/__init__.py[m
[1m+++ b/tests/__init__.py[m
[36m@@ -1,9 +0,0 @@[m
[31m-import unittest[m
[31m-from artifact import MyClass[m
[31m-[m
[31m-[m
[31m-class TestMyClass(unittest.TestCase):[m
[31m-    # test methods' names should begin with `test_`[m
[31m-    def test_my_method(self):[m
[31m-        x = MyClass().my_method()[m
[31m-        self.assertEqual("Hello World", x)[m
