import base64
import hashlib
import json
import hmac

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Hash import SHA256



from rest_framework.permissions import BasePermission

from .models import PaymentProvider


class WonderlandPayCallbackPermission(BasePermission):
    def has_permission(self, request, view):
        try:
            provider = PaymentProvider.objects.get(
                name='wonderlandpay'
            )

            if provider.testing:
                sign_key = provider.test_sign_key
            else:
                sign_key = provider.prod_sign_key

            sign_data = request.data.get('merNo') + \
                request.data.get('gatewayNo') + \
                request.data.get('tradeNo') + \
                request.data.get('orderNo') + \
                request.data.get('orderCurrency') + \
                request.data.get('orderAmount') + \
                request.data.get('orderStatus') + \
                request.data.get('orderInfo') + \
                sign_key
            sign_data_binary = sign_data.encode('utf-8')
            sign_info = hashlib.sha256(sign_data_binary).hexdigest().upper()

            if sign_info == request.data.get('signInfo'):
                return True
        except Exception as e:
            print(e)
            return False


class DixonPayCallbackPermission(BasePermission):
    def has_permission(self, request, view):
        try:
            provider = PaymentProvider.objects.get(
                name='dixonpay'
            )

            if provider.testing:
                sign_key = provider.test_sign_key
            else:
                sign_key = provider.prod_sign_key

            sign_data = request.data.get('merNo') + \
                request.data.get('terminalNo') + \
                request.data.get('tradeNo') + \
                request.data.get('orderNo') + \
                request.data.get('orderCurrency') + \
                request.data.get('orderAmount') + \
                request.data.get('orderStatus') + \
                request.data.get('orderInfo') + \
                sign_key
            sign_data_binary = sign_data.encode('utf-8')
            encryption = hashlib.sha256(sign_data_binary).hexdigest().upper()

            if encryption == request.data.get('encryption'):
                return True
            else:
                return False
        except Exception as e:
            print(e)
            return False


class InterkassaCallbackPermission(BasePermission):
    def has_permission(self, request, view):
        try:
            provider = PaymentProvider.objects.get(
                name='interkassa'
            )

            if provider.testing:
                sign_key = provider.test_sign_key
            else:
                sign_key = provider.prod_sign_key

            # GET SORTED ELEMENTS FROM DATA
            data = [x[-1] for x in sorted(request.data.items()) if x[0] != 'ik_sign']

            # ADD SECRET KEY
            data.append(sign_key)

            # COMBINE ALL LIST DATA:
            data_string = ':'.join(data)

            # PREPARE MD5
            m = hashlib.md5()
            m.update(data_string.encode('utf-8'))

            # CODARRAY in BASE64
            result = base64.b64encode(m.digest())

            if request.data.get('ik_sign') == result.decode('utf-8'):
                # REQUEST WAS CORRECTLY SIGNED
                return True
            return False
        except Exception as e:
            print(e)
            return False


class AlphaPoCallbackPermission(BasePermission):
    def has_permission(self, request, view):
        try:
            x_processing_key = request.headers.get('X-Processing-Key')
            x_processing_signature = request.headers.get('X-Processing-Signature')

            provider = PaymentProvider.objects.get(
                name='alphapo'
            )

            if provider.testing:
                merchant_number = provider.merchant_number
                sign_key = provider.test_sign_key.encode('utf-8')
            else:
                merchant_number = provider.gateway_number
                sign_key = provider.prod_sign_key.encode('utf-8')

            # GET SORTED ELEMENTS FROM DATA
            encoded_data = json.dumps(request.data, separators=(',', ':')).encode('utf-8')

            signature = hmac.new(
                sign_key,
                msg=encoded_data,
                digestmod=hashlib.sha512
            ).hexdigest()

            if signature == x_processing_signature:
                if x_processing_key == merchant_number:
                    # REQUEST WAS CORRECTLY SIGNED
                    return True
            return False
        except Exception as e:
            print(e)
            return False


class EnsopayCallbackPermission(BasePermission):
    def has_permission(self, request, view):
        try:
            provider = PaymentProvider.objects.get(
                name='ensopay'
            )
            if provider.testing:

                sign_key = provider.test_sign_key
            else:
                sign_key = provider.prod_sign_key

            # GET SORTED ELEMENTS FROM DATA
            data = [x[-1] for x in sorted(request.data.items()) if x[0] != 'sign']
            # ADD SECRET KEY
            data.append(sign_key)
            if None in data:
                index = data.index(None)
                data[index] = ''
            # COMBINE ALL LIST DATA:
            data_string = ':'.join(data)
            print('data _ string   ' + data_string)
            result = base64.b64encode(hashlib.md5(data_string.encode('utf-8')).hexdigest().encode('utf-8'))

            print("request data sign in   " + str(request.data.get('sign')))
            print("result what I received     " + str(result.decode('utf-8')))

            if request.data.get('sign') == result.decode('utf-8'):
                if request.data.get('cashbox_id') == provider.merchant_number:
                    # REQUEST WAS CORRECTLY SIGNED
                    return True

            return False
        except Exception as e:
            print(e)
            return False


class OdeonpayCallbackPermission(BasePermission):

    def has_permission(self, request, view):
        print(request.data)
        try:
            provider = PaymentProvider.objects.get(
                name='odeonpay'
            )

            if provider.testing:
                sign_key = provider.test_sign_key
            else:
                sign_key = provider.prod_sign_key

            Hmac= request.headers.get('Content-HMAC')
            decode_message = request.body.decode("utf-8")
            message = bytes(decode_message, 'utf-8')
            secret = bytes(sign_key, 'utf-8')
            result = base64.b64encode(hmac.new(secret, message, digestmod=hashlib.sha256).hexdigest().encode())
            print('Hmac is   ' + str(Hmac))
            print("result what I received     " + str(result.decode('utf-8')))

            if Hmac == result.decode('utf-8'):
                    # REQUEST WAS CORRECTLY SIGNED
                    return True

            return False
        except Exception as e:
            print(e)
            return False


class SyspayCallbackPermission(BasePermission):

    def has_permission(self, request, view):

        try:

            allowedIps = ['128.199.199.39', '128.199.106.36', '104.248.99.154', '159.89.211.72']
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                Ip = x_forwarded_for.split(',')[0]
            else:
                Ip = request.META.get('REMOTE_ADDR')
            print("about header is   " + str(Ip))

            if str(Ip) in allowedIps:
                # REQUEST WAS CORRECTLY SIGNED
                return True
            else:
                return False
        except Exception as e:
            print('come hereeee', e)
            return False


class FintechCashierCallbackPermission(BasePermission):

    def has_permission(self, request, view):

        try:
            provider = PaymentProvider.objects.get(
                name='fintech_cashier'
            )

            if provider.testing:
                sign_key = provider.test_sign_key
            else:
                sign_key = provider.prod_sign_key

            data = (request.data.get('trans_id') + request.data.get('trans_order')
                    + request.data.get('reply_code') + request.data.get('trans_amount')
                    + request.data.get('trans_currency') + sign_key).encode('utf-8')

            signature = base64.b64encode(hashlib.sha256(data).digest()).decode('utf-8')

            if request.data.get('signature') == signature:
                return True

        except Exception as e:
            print(e)
            return False

class CertusCallbackPermission(BasePermission):

    def has_permission(self, request, view):
        try:
            print("request data ", request.data)
            provider = PaymentProvider.objects.get(
                name='certus'
            )
            if provider.testing:
                sign_key = provider.test_sign_key
            else:
                sign_key = provider.prod_sign_key

            signature = request.data.get('signature')
            data = request.data
            resultdata = str(data['responseTime']) + str(data['txId']) + str(data['txTypeId']) + str(data['recurrentTypeId']) \
                        + str(data['requestId']) + str(data['orderId']) + str(data['sourceAmount']['amount']) + str(data['sourceAmount']['currencyCode']) \
                        + str(data['amount']['amount']) + str(data['amount']['currencyCode']) + str(data['result']['resultCode']) \
                        + str(data['result']['reasonCode']) + str(data['ccNumber']) + str(data['cardId'])

            if "None" in resultdata:
                result = resultdata.replace('None', '')

            print("data is   ", result)

            cipher = AES.new(sign_key.encode('utf-8'), AES.MODE_ECB)
            pad_pkcs7 = pad(result.encode('utf-8'), AES.block_size, style='pkcs7')
            encrypt_aes = cipher.encrypt(pad_pkcs7)
            hash_string = SHA256.new(encrypt_aes).digest()
            result_signature = base64.b64encode(hash_string).decode()

            print("result string is  ", result_signature)
            print("signature is ", signature)

            if result_signature == signature:
                return True

            return False
        except Exception as e:
            print(e)
            return False

