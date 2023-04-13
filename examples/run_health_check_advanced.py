import requests


# serviceStatus = dict()

# applicationStatus = dict()

# tenantStatus = dict()

def healthCheck(environment:str):

    if(environment[:3]=='tsc'):

        environment = environment[3:]

    response = requests.get(f'https://tenant1-{environment}-tsc.dev.mykronos.com/telestaff/healthCheck/advanced')

    serviceStatus = response.json()['services']
    applicationStatus = serviceStatus['applicationUp']
    tenantStatus = response.json()['tenants']
    serviceStatus.pop('applicationUp')

    # applicationStatus['telestaffUp']=False

    print(response.json())

    print(f'servicesStatus: {serviceStatus}')

    print(f'applicationStatus: {applicationStatus}')

    print(f'tenantStatus: {tenantStatus}')


def summarize(applicationStatus, serviceStatus) -> str:
    return askLLM(f"What is not up in this data: {applicationStatus}, {serviceStatus}")['predictions'][0]

# servicesStatus= dict()

healthCheck('s1')
print(summarize(applicationStatus, serviceStatus))


