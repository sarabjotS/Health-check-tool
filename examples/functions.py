import requests

def askLLM(*questions):
    data = {'instances': questions}
            # 'temperature': 1.0,
            # 'top_k': 100}
    response = requests.post('http://130.211.213.132/predict', json=data)

    return response.json()['predictions'][0]



def runHealthCheck(environment:str):

    if(environment[:3]=='tsc'):

        environment = environment[3:]

    response = requests.get(f'https://tenant1-{environment}-tsc.dev.mykronos.com/telestaff/healthCheck/advanced')

    serviceStatus = response.json()['services']
    applicationStatus = serviceStatus['applicationUp']
    tenantStatus = response.json()['tenants']
    serviceStatus.pop('applicationUp')

    applicationStatus['telestaffUp']=False
    # print(response.json())
    print(f'servicesStatus: {serviceStatus}')
    print(f'applicationStatus: {applicationStatus}')
    print(f'tenantStatus: {tenantStatus}')


    print( askLLM(f"is anything not up in this data: {applicationStatus}, {serviceStatus}"))


runHealthCheck('s1')
# print(summarize(applicationStatus, serviceStatus))

# print(askLLM("What is the environment name in: run health check on s2"))

# servicesStatus= dict()



# q1="For coming questions, remember, wfr is a computer"
# q2="Look at my data and 

# q3="How to turn on a computer?"
# q4="How to turn on wfr?"


# print(askLLM(q1, q2, q3, q4))


# print(askLLM("Look at my data and answer, is telestaff up?"+str(applicationStatus)))

