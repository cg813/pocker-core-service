import requests
import base64
import hashlib
import json
import hmac

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Hash import SHA256

from accounts.models import UserAccount, Rate, Currency
from payments.models import PaymentMethod
from payments.services.utils import get_currency

from datetime import datetime




def get_certus_redirect_url(user: UserAccount, provider: PaymentMethod, transaction_id: str, currency: Currency,
                            amount: float) -> str:

    if provider.testing:
        print("come in testing")
        sign_key = provider.test_sign_key
        merchant_number = provider.test_merchant_number
    else:
        merchant_number = provider.merchant_number
        sign_key = provider.prod_sign_key

    print("sign key is ", sign_key)
    requestTime = datetime.now().replace(microsecond=0)

    MId = base64.b64encode(hashlib.sha256(str(provider.gateway_number).encode('utf-8')).digest()).decode('utf-8')
    maId = base64.b64encode(hashlib.sha256(str(merchant_number).encode('utf-8')).digest()).decode('utf-8')

    data = {
        "requestTime": str(requestTime),
        "mId": MId,
        "maId": maId,

        "userName": "igK7XzaTBrusPc3q5OEOQg==",
        "password": "igK7XzaTBrusPc3q5OEOQg==",

        "txDetails": {
            "apiVersion": "1.0.1",
            "requestId": transaction_id,
            "perform3DS": "1",
            "orderData": {
                "orderId": transaction_id,
                "orderDescription": "test order",
                "amount": str(amount),
                "currencyCode": currency,
                "billingAddress": {
                    "firstName": str(user.username),
                    "lastName": str(user.last_name),
                    "address1": "112",
                    "address2": "Bonadie Street",
                    "city": "Kingstown",
                    "zipcode": "P.O Box 613",
                    "stateCode": "N3",
                    "countryCode": "VC",
                    "mobile": str(user.phone_number),
                    "phone": str(user.phone_number),
                    "email": user.email,
                    "fax": "+16362323828"
                },
                "shippingAddress": {
                    "firstName": str(user.username),
                    "lastName": str(user.last_name),
                    "address1": "112",
                    "address2": "Bonadie Street",
                    "city": "Kingstown",
                    "zipcode": "P.O Box 613",
                    "stateCode": "N3",
                    "countryCode": "VC",
                    "mobile": str(user.phone_number),
                    "phone": str(user.phone_number),
                    "email": user.email,
                    "fax": "+16362323828"
                },
                "personalAddress": {
                    "firstName": str(user.username),
                    "lastName": str(user.last_name),
                    "address1": "112",
                    "address2": "Bonadie Street",
                    "city": "Kingstown",
                    "zipcode": "P.O Box 613",
                    "stateCode": "N3",
                    "countryCode": "VC",
                    "mobile": str(user.phone_number),
                    "phone": str(user.phone_number),
                    "email": user.email,
                    "fax": "+16362323828"
                },

            },
            "statement": "",
            "cancelUrl":  "https://dev.mima-poker.cc/statuses?",
            "returnUrl": "https://dev.mima-poker.cc/statuses?",
            "notificationUrl": provider.test_endpoint + "/api/payment/certus/callback/"
        }
    }

    print("before signature, json is ", json.dumps(data))
    resultdata = ""

    for value in data.values():
        print("key ", value)
        if type(value) is dict:
            for v in value.values():
                if type(v) is dict:
                    for i in v.values():
                        if type(i) is dict:
                            for j in i.values():
                                resultdata = resultdata+str(j).rstrip()
                        elif i != None:
                            resultdata = resultdata+str(i).rstrip()
                else:
                    if v!=None:
                        resultdata = resultdata+str(v).rstrip()
        else:
            if value!=None:
                resultdata = resultdata+str(value).rstrip()


    print("result data   ", resultdata)
    signature = createSignature(resultdata, sign_key)
    print("signature is ", signature)
    data["signature"] = signature
    data["lang"] = "en"
    data["metaData"] = {"merchantUserId": transaction_id}
    resultdata = json.dumps(data)
    print("data is ", resultdata)

    result = base64.b64encode(str(resultdata).encode('utf-8')).decode('utf-8')

    print(result)
    return result


def createSignature(data, raw_key):
    try:
        print("raw key ", raw_key)
        cipher = AES.new(raw_key.encode('utf-8'), AES.MODE_ECB)
        pad_pkcs7 = pad(data.encode('utf-8'), AES.block_size ,style='pkcs7')
        encrypt_aes = cipher.encrypt(pad_pkcs7)
        hash_string = SHA256.new(encrypt_aes).digest();
        signature = base64.b64encode(hash_string).decode()
        return signature
    except:
        print("Please validate your data.")
