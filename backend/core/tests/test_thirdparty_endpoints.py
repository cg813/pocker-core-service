from payments.services.utils import get_iso_of_user


# def test_improper_ip():
#     """
#     GIVEN: we have a function that takes ip and returns ISO of country
#     WHEN: we pass an improper ip
#     THEN: by default GE should be returned as ISO
#     """
#     iso = get_iso_of_user('172.18.0.1')

#     assert iso == 'GE'


# def test_proper_ip():
#     """
#     GIVEN: we have a function that takes ip and returns ISO of country
#     WHEN: we pass a proper ip of US
#     THEN: returned ISO should be US
#     """

#     iso = get_iso_of_user('192.158.1.38')

#     assert iso == 'US'
