import unittest
from coco_app import app

class FlaskTestCase(unittest.TestCase):


    # Ensure that flask was set up correctly
    def test_index(self):
        tester = app.test_client(self)
        response = tester.get('/index', content_type='html')
        self.assertEqual(response.status_code, 200)

    # Ensure that flask was set up correctly
    def test_register_page(self):
        tester = app.test_client(self)
        response = tester.get('/reg', content_type='html')
        self.assertEqual(response.status_code, 200)

     # Ensure registeration behaves correctly with correct credentials
    def test_registration(self):
        tester = app.test_client()
        response = tester.post(
            '/register',
            data=dict(title="mr", name="abac", username="aba", email="abcdeff@gmail.com", password="admin", confirmpass="admin", type="1"),
            follow_redirects=True
        )
        self.assertIn(b'Registration successful', response.data)

     # Ensure login behaves correctly with correct credentials
    def test_login(self):
        tester = app.test_client()
        response = tester.post(
            '/login',
            data=dict(username="doe",  password="default"),
            follow_redirects=True
        )
        self.assertIn(b'You are logged in', response.data)

    # Ensure Lecturers can add preferences
    def test_lecturer(self):
        tester = app.test_client()
        with tester:
            tester.post(
                '/login',
                data=dict(username="doe",  password="default"),
                follow_redirects=True
            )
            with app.test_client() as c:
                with c.session_transaction() as sess:
                     sess['user_id'] = 1
                     sess['current_semester'] = 1
                     sess['logged_in'] = True
            datax = {}
            datax['courses']= "1"
            datax["hours"]= "2 hrs"
            for i in range(1, 6): #  timeslot
                for j in range(1, 6): # week_day
                    x = str(i) + str(j)
                    datax[x] = "1"
            datax["11"]= "3"
            response = tester.post(
                '/get-prefs',
                data=datax,
                follow_redirects=True
            )
            self.assertIn(b'Preferences saved', response.data)



if __name__ == '__main__':
    unittest.main()
