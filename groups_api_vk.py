import requests
import json
import os

N = 0

TOKEN = os.getenv('VK_TOKEN')
EXECUTE_URL, EXECUTE_VERSION = 'https://api.vk.com/method/execute', 5.8
USER_ID = '392477722'


class TimeoutError(Exception):
    def __init__(self, text):
        self.txt = text


def run_vk_api_execute(method, arguments):
    response_result = []
    code = ''
    counter = 0
    total = len(arguments)

    for argument in arguments:

        if code: code += ','

        argument_str = ','.join('\'{}\': \'{}\''.format(k, v) for k, v in argument.items())
        code += f'API.{method}({{{argument_str}}})'

        counter += 1

        if not (counter % 25) or counter < total:
            continue

        code = f'return [{code}];'
        try:
            response = requests.post(url=EXECUTE_URL,
                                     data={
                                         "code": code,
                                         "access_token": TOKEN,
                                         "v": EXECUTE_VERSION
                                     },
                                     #  timeout=0.05
                                     )
            'accumulating query results'
            response_result += response.json()['response']
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout):
            raise TimeoutError('Response timeout exceeded, check the connection')
        code = ''

    return response_result


def get_valid_user_id(user_id):
    data = run_vk_api_execute(
        'users.get',
        [{'user_ids': user_id}]
    )

    if data and not data[0]:
        return
    else:
        return data[0][0]['id']


class User(object):

    def __init__(self, user_id):
        self.user_id = user_id

    @property
    def groups_ids(self):

        data = run_vk_api_execute(
            'groups.get',
            [{
                'user_id': user_id,
                'extended': '0',
                'count': 1000,
            }]
        )

        if data and not data[0]:
            return
        else:
            return data[0]['items']


def main(user_id):
    ''' The main algorithm of the problem

    '''

    user = User(user_id)
    result = set()

    print('Step 1 of 4: Getting a list of user groups...', end='')
    groups = user.groups_ids
    print('OK')

    print('Step 2 of 4: Filter groups by the number of shared friends ',
          f'({N} or less)...', end='')
    data = run_vk_api_execute(
        'groups.getMembers',
        [{'group_id': group, 'filter': 'friends'} for group in groups]
    )

    for group, item in zip(groups, data):
        if not isinstance(item, bool):
            if item['count'] <= N:
                result.add(group)
    print('OK')

    print('Step 3 of 4: Getting information about the selected groups...', end='')
    group_info = run_vk_api_execute(
        'groups.getById',
        [{'group_id': group, 'fields': 'name,members_count'} for group in result]
    )
    print('OK')

    print('Step 4 of 4: Putting the results in the file output.json...', end='')
    data = []
    with open('output.json', 'w') as file:
        for foo in group_info:
            data.append({
                'name': foo[0]['name'],
                'gid': foo[0]['id'],
                'members_count': foo[0]['members_count']
            })
        json.dump(data, file, ensure_ascii=False, indent=4)
    print('OK')
    return result


if __name__ == '__main__':

    input_id = input(f'Please enter user ID (Enter - {USER_ID}): ').strip()
    # input_id = input_id or USER_ID
    input_id = input_id if input_id else USER_ID
    user_id = get_valid_user_id(input_id)

    if user_id:

        try:

            groups_set = main(user_id)
            if not groups_set:
                print('The user has no secrets from their friends :-)')

        except TimeoutError as Error:
            print(Error)

    else:
        print(f'{input_id} is not valid user id. The program was interrupted.')
