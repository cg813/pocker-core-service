import requests


def take_user_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_iso_of_user(ip):
    response = requests.get(f'https://geolocation-db.com/json/{ip}&position=true').json()

    if response['country_code'] == 'Not found':
        return 'GE'
    return response['country_code']


def get_currency(amount, currency):
    url = 'https://api.exchangerate.host/convert?from=USD&to=' + currency
    response = requests.get(url)
    data = response.json()
    print(data)
    if response.status_code == 200:
        response = response.json()
        if response['success'] == True:
            rate = response['info']['rate']
            return str(round(rate * amount, 2))
        else:
            return -1
    else:
        return -1
