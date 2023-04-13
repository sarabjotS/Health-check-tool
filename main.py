import requests
from enum import Enum

appName = "DiagnoBuddy"
openingGreeting = f"Hi, I am {appName}. How may I help you?"
closingGreeting = 'Bye, have a nice day'
closingWords = { 'close', 'stop', 'bye', 'exit', 'end', 'shut down', 'shutdown'}
positiveResponseSet = {'yes', 'yeah', 'yep', 'true', True}
negativeResponseSet = {'no', 'false', 'negative', 'nopes', 'nope', False}
validEnvironments = { "s"+str(i) for i in range(1,16) }
validEnvironments.update( { "m"+str(i) for i in range(1,6) } )
validEnvironments.update( { "l"+str(i) for i in range(1,3) } )
runHealthCheckWordsList = ('health',)

SOPMapping = {
    'telestaffUp': "https://engconf.int.kronos.com/x/S9A6GQ",
    'workflowUp': "https://engconf.int.kronos.com/x/S9A6GQ",
    'biddingUp': "https://engconf.int.kronos.com/x/S9A6GQ"
}

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
    
def getURL(environment):
    KRONOS_DOT_COM = "kronos.com"
    healthCheckUrl = str()
    environment = environment.lower()
    
    if KRONOS_DOT_COM not in environment:
        if(len(environment) > 2 and environment[:3]=='tsc'):
            environment = environment[4:] if(len(environment)>3 and environment[3] == '-') else environment[3:]
        return f'https://tenant1-{environment}-tsc.dev.mykronos.com/telestaff/healthCheck/advanced'
        
    else:
        indexOfKronosDotCom = environment.index(KRONOS_DOT_COM)
        healthCheckUrl = environment[ : indexOfKronosDotCom+len(KRONOS_DOT_COM) ]
        healthCheckUrl = healthCheckUrl[healthCheckUrl.rindex(" ")+1: ]
        if("http" in healthCheckUrl):
            return healthCheckUrl[healthCheckUrl.rindex("http"): ]
        else:
            return f'https://{healthCheckUrl}/telestaff/healthCheck/advanced'
    
def runHealthCheck(healthCheckUrl:str):
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

def checkHealth(message):
    environment = getEnvironmentName(message)
    if(environment not in validEnvironments):
        message = input('''\nI could not figure out your environment from your message.\nCould you give me the name of the environment? Or you could even give me its url\n\n''')
        if(message.lower() not in negativeResponseSet):
            environment = message
    healthCheckUrl = getURL(environment)
    return healthCheckUrl, *runHealthCheck(healthCheckUrl)
        
        

def main():
    closeConversation = False
    outputMessage = openingGreeting

    while(not closeConversation):
        
        print(outputMessage, end="\n\n")
        userMessage = input()
        if(closeConversation or (userMessage.lower() in closingWords)):
            closeConversation = False
            print(closingGreeting)
            break
        
        # if(areTheseSame(userMessage, 'run health check')):
        if all([ word in userMessage for word in runHealthCheckWordsList]):
            url, serviceStatus, applicationStatus, tenantStatus = str(), dict(),dict(),dict()
            try:
                url, serviceStatus, applicationStatus, tenantStatus = checkHealth(userMessage)
            except:
                print("\nThis application environment is unreachable")
                outputMessage = "\nDo you want me to help you with something else?\n\n"
                
                
            if False not in applicationStatus.values():
                userMessage = input("\nApplication is healthy\nDo you want me to give you its URL?\n\n")
                if(userMessage in positiveResponseSet):
                    # print("\nURL:" + getURL(environment))
                    print("\nURL:" + url)
            else:
                userMessage = input("\nApplication is not healthy!\nDo you want me to show you what fails?\n\n")
                if(userMessage not in negativeResponseSet):
                    # closeConversation = True
                    # continue
                    print(f'''URL = {getURL(environment)}\n{formatStatus(("Application Status", applicationStatus))}''')
                    userMessage = input("\nDo you want me provide you with some SOPs?\n\n")
                    if(userMessage not in negativeResponseSet):
                        suggestedLinks = { app:SOPMapping[app]  }
                        
                        print("\nThe following link(s) might help:")
                        for app in applicationStatus:
                            if not applicationStatus[app]:
                                print(f"\t{app[:-2]} : {suggestedLinks[app]}")
            
        
        userMessage = input("\nDo you want me to do anything else?\n\n")
        if(userMessage.lower() in negativeResponseSet):
            closeConversation = True
            print(closingGreeting)
        elif(userMessage.lower() in positiveResponseSet):
            userMessage = input("\nHow may I help you?\n\n")
            
            
    
    
if __name__ == "__main__":
    main()




