# 'python' run this script in the 'anchor-client' container.

import json
import os
import requests

# To run on localhost, need to start API server using
#   anchor-serve-local
#
# If login hangs, maybe need to do this first:
#   sudo ifconfig lo:0 10.254.254.254
API_URL = 'http://localhost:8000'

grid = {'from': 0.5, 'by': 1, 'len': 10}
field_value_range = [-1, 1]
data_forward = [1, 2, 3, 3.2, 5, 8.7]
n_forward = len(data_forward)
data_linear = [{
    'points': 3,
    'value': 1.2
}, {
    'points': [1, 4],
    'weights': [0.8, -0.3],
    'value': .8
}]


class Session(requests.Session):
    # This customization should not have been needed because
    # requests.Session is supposed to handle cookies automatically,
    # but somehow it's not working automatically.
    def request(self, method, url, **kwargs):
        url = API_URL + url
        if kwargs.get('cookies', None) is None:
            kwargs['cookies'] = dict(self.cookies)
        z = super().request(method, url, **kwargs)
        if z.status_code != 200:
            raise Exception('Something went wrong!',
                            'status_code %s' % z.status_code, z.content)
        return z

    def get(self, url, **kwargs):
        z = super().get(url, **kwargs)
        try:
            return json.loads(z.json())
        except:
            return z.content

    def post(self, url, **kwargs):
        z = super().post(url, json=kwargs)
        try:
            return json.loads(z.json())
        except:
            return z.content


sess = Session()

# Log in and start a session.
# No need to log in again until log-out or shut-down.
print('logging in...')
user_id = os.environ['DEMO_USER_ID']
user_email = os.environ['DEMO_USER_EMAIL']
sess.post('/login', user_id=user_id, user_email=user_email)

# In practice, we know the project_id and specify it directly.
# Here for demo, we randomly grab a project.
print('getting a project to work on...')
project_ids = sess.get('/user/projects')
project_id = project_ids[0]
print('    project_id:', project_id)

print('setting project ID...')
# No need to specify project until re-set or log-out or shut-down.
sess.post('/user/set_project', project_id=project_id)

print('clearing existing content of project...')
sess.post('/user/project/models/clear')

print('initializing model...')
sess.post(
    '/user/project/models/init',
    grid=grid,
    field_value_range=field_value_range,
    data_forward=data_forward,
    data_linear=data_linear)

print('simulating fields...')
simulations = sess.get('/user/project/request_fields', params=dict(n=8))
print('    simulations:', len(simulations), 'x', len(simulations[1]))

print('requesting fields...')
fields = sess.post('/user/project/models/request_fields', n=101)
print('    fields:', len(fields), 'x', len(fields[1]))

# Running forward model on fields to get forward data.
# In current testing, just make up forward data of current dimensions.
forwards = [list(range(i, i + n_forward)) for i in range(len(fields))]
print('submitting forward values...')
sess.post('/user/project/models/submit_forwards', forward_values=forwards)

print('updating model...')
sess.post('/user/project/models/update')

print('simulating fields using updated model...')
simulations = sess.get('/user/project/request_fields', params=dict(n=8))
print('    simulations:', len(simulations), 'x', len(simulations[1]))

print('summarizing project...')
summary = sess.get('/user/project/summary')
print('    ' + str(summary))

print('logging out...')
sess.post('/logout')
