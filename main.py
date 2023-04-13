import requests

from enum import Enum

# serviceStatus = dict()

# applicationStatus = dict()

# tenantStatus = dict()

openingGreeting = "Hi, how may I help you?"
closingGreeting = 'Bye, have a nice day'
closingWords = { 'close', 'stop', 'bye', 'exit', 'end', 'shut down', 'shutdown'}
positiveResponseSet = {'yes', 'true', True}
negativeResponseSet = {'no', 'false', 'negative', 'nopes', 'nope', False}
validEnvironments = { "s"+str(i) for i in range(1,16) }
validEnvironments.update( { "m"+str(i) for i in range(1,6) } )
validEnvironments.update( { "l"+str(i) for i in range(1,3) } )
'''
stage defines stage what user asked for in last message
0 = new request
1 = run health check
2 = 1
'''
stage = 0

# class Stage(Enum):
    

def askLLM(*questions):
    data = {'instances': questions,
            'temperature': 1,
            'top_k': 100}
    try:
        response = requests.post('http://130.211.213.132/predict', json=data)
    except(error):
        print(error)
    return response.json()


def areTheseSame(usermessage, templateMessage) -> bool:
    response = askLLM(f'''Do these mean the same thing?
           A:{usermessage}
           B:{templateMessage}''')
    
    return (response['predictions'][0] in positiveResponseSet)


def getEnvironmentName(message) -> str:
    response = askLLM(f"What is the environment name in: {message}")
    return response['predictions'][0]
    
    
def runHealthCheck(environment:str):
    KRONOS_DOT_COM = "kronos.com"
    healthCheckUrl = str()
    environment = environment.lower()
    
    if KRONOS_DOT_COM not in environment:
        if(len(environment) > 2 and environment[:3]=='tsc'):
            environment = environment[4:] if(len(environment)>3 and environment[3] == '-') else environment[3:]
        healthCheckUrl = f'https://tenant1-{environment}-tsc.dev.mykronos.com/telestaff/healthCheck/advanced'
        
    else:
        indexOfKronosDotCom = environment.index(KRONOS_DOT_COM)
        healthCheckUrl = environment[ : indexOfKronosDotCom+len(KRONOS_DOT_COM) ]
        healthCheckUrl = healthCheckUrl[healthCheckUrl.rindex(" ")+1: ]
        if("http" in healthCheckUrl):
            healthCheckUrl = healthCheckUrl[healthCheckUrl.rindex("http"): ]
        else:
            healthCheckUrl = f'https://{healthCheckUrl}/telestaff/healthCheck/advanced'
        
        
    response = requests.get(healthCheckUrl)

    serviceStatus = response.json()['services']
    applicationStatus = serviceStatus['applicationUp']
    tenantStatus = response.json()['tenants']
    serviceStatus.pop('applicationUp')

    return serviceStatus, applicationStatus, tenantStatus


def summarize(applicationStatus, serviceStatus) -> str:
    return askLLM(f"What is not up in this data: {applicationStatus}, {serviceStatus}")['predictions'][0]

def formatStatus(*nameStatusTuples):
    output = ""
    for name, status in nameStatusTuples:
        output += name + ''':\n'''
        for key, value in status:
            output += f"\t{key[:-2]} is {'not ' if not value else ''}running"
    return output


# healthCheck(userMessage):



def main():
    closeConversation = False
    outputMessage = openingGreeting
    print(outputMessage, end="\n\n")
    userMessage = input()

    while(not closeConversation):
        
        if(closeConversation or (userMessage.lower() in closingWords)):
            closeConversation = False
            print(closingGreeting)
            break
        
        healthCheck(userMessage)
        runHealthCheckWordsList = ('run', 'health', 'check')
        # if(areTheseSame(userMessage, 'run health check')):
        if all([ word in userMessage for word in runHealthCheckWordsList]):
            environment = getEnvironmentName(userMessage)
            if(environment not in validEnvironments):
                userMessage = input('''Sorry, I could not recognise the environment you were looking for, or it might not be invalid.
                \n Could repeat the name of the environment? You could even give me its url''')
                if(userMessage.lower() in negativeResponseSet):
                    closeConversation = True
                else:
                    environment = userMessage
            serviceStatus, applicationStatus, tenantStatus = runHealthCheck(environment)
            outputMessage = formatStatus(("Application Status", applicationStatus), ("Service Status", serviceStatus)) + "\n\nDo you want me to do anything else?"
        
        print("\n"+outputMessage, end="\n\n")
        userMessage = input()
        if(userMessage.lower() == 'no'):
            closeConversation = True
    
    
if __name__ == "__main__":
    main()




