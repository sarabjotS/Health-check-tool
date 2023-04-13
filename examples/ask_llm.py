import requests

data = {'instances': ["Is this a positive response: negative",
                      "Is this a positive response: no",
                      "Is this a positive response: false",
                      "Is this a positive response: please no",
                      ]}
response = requests.post('http://130.211.213.132/predict', json=data)

print(response.json())

# print(response.json()['predictions'][0])