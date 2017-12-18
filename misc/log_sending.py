import requests
import os


def send_truncate_file(path, tag='quiz_errors'):
    if not os.path.exists(path):
        return
    f = open(path, mode='rw+')
    data = {'data': f.read()}
    if len(data['data']) == 0:
        return
    res = requests.post(url='https://logs-01.loggly.com/inputs/8933229a-dbf7-4766-8234-8dbf752ebdda/tag/'+tag,
                  data=data, timeout=5)
    f.truncate(0)
    f.close()
    return res


if __name__ == '__main__':
    if os.environ.get("PROD"):
        send_truncate_file('/var/log/g_errors.log')
    else:
        send_truncate_file('/var/log/g_errors.log', tag='quiz_test_errors')
