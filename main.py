import requests
from enum import Enum

appName = "DiagnoBuddy"
openingGreeting = f"Hi, I am {appName}. How may I help you?"
closingGreeting = 'Bye, have a nice day'
closingWords = { 'close', 'stop', 'bye', 'exit', 'end', 'shut down', 'shutdown'}
positiveResponseSet = {'yes', 'yeah', 'yep', 'true', True, 'ofcourse', 'of course'}
negativeResponseSet = {'no', 'false', 'negative', 'nopes', 'nope', False}
validEnvironments = { "s"+str(i) for i in range(1,16) }
validEnvironments.update( { "m"+str(i) for i in range(1,6) } )
validEnvironments.update( { "l"+str(i) for i in range(1,3) } )

triggerHealthCheckWords = ('health', 'running')

SOPMapping = {
    'telestaffUp': "https://engconf.int.kronos.com/x/lzWJGg",
    'workflowUp': "https://engconf.int.kronos.com/x/Ky94Gg",
    'biddingUp': "https://engconf.int.kronos.com/x/S9A6GQ"
}
parentSOPLink = "https://engconf.int.kronos.com/x/OdA6GQ"

def askLLM(*questions):
    data = {'instances': questions,
            'temperature': 1,
            'top_k': 100}
    try:
        response = requests.post('http://130.211.213.132/predict', json=data)
    except(error):
        print("Sorry! application is unreachable")
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
        return f'https://tenant1-{environment}-tsc.dev.mykronos.com/telestaff/'
        
    else:
        indexOfKronosDotCom = environment.index(KRONOS_DOT_COM)
        healthCheckUrl = environment[ : indexOfKronosDotCom+len(KRONOS_DOT_COM) ]
        healthCheckUrl = healthCheckUrl[healthCheckUrl.rindex(" ")+1: ]
        if("http" in healthCheckUrl):
            return healthCheckUrl[healthCheckUrl.rindex("http"): ] + "/telestaff/"
        else:
            return f'https://{healthCheckUrl}/telestaff/'
    
def runHealthCheck(healthCheckUrl:str):
    response = requests.get(healthCheckUrl)

    serviceStatus = response.json()['services']
    applicationStatus = serviceStatus['applicationUp']
    tenantStatus = response.json()['tenants']
    serviceStatus.pop('applicationUp')

    return serviceStatus, applicationStatus, tenantStatus


def summarize(applicationStatus, serviceStatus) -> str:
    return askLLM(f"What is not up in this data: {applicationStatus}, {serviceStatus}")['predictions'][0]


def formatStatus(applicationStatus: dict):
    output = "Application Status:"
    for name in applicationStatus:
        output += f"\n\t{name[:-2]} is {'not ' if not applicationStatus[name] else ''}running"
    return output


def formatStatusTuples(*nameStatusTuples: tuple):
    output = ""
    for name, status in nameStatusTuples:
        output += f"{name}:"
        for key in status:
            output += f"\n\t{key[:-2]} is {'not ' if not status[key] else ''}running"
    return output

def checkHealth(message):
    environment = getEnvironmentName(message)
    if(environment not in validEnvironments):
        message = input(f"\n{appName}: I could not figure out your environment from your message.\nCould you give me the name of the environment? Or you could even give me its url\n\nMe:")
        if(message.lower() not in negativeResponseSet):
            environment = message
    URL = getURL(environment)
    return URL, *runHealthCheck(URL+"/healthCheck/advanced")
        
        

def main():
    closeConversation = False
    outputMessage = openingGreeting

    while(not closeConversation):
        
        print(f"\n{appName}: {outputMessage}\n")
        userMessage = input("Me:")
        if(closeConversation or (userMessage.lower() in closingWords)):
            closeConversation = False
            break
        
        if not any([ word in userMessage for word in triggerHealthCheckWords ]):
            userMessage = askLLM("Paraphrase this: " + userMessage)['predictions'][0]
            if not any([ word in userMessage for word in triggerHealthCheckWords ]):
                outputMessage = "Sorry, I could not understand. Could you repeat that in a way which is a little easier for me to understand?"
                continue
        url, serviceStatus, applicationStatus, tenantStatus = str(), dict(),dict(),dict()
        try:
            url, serviceStatus, applicationStatus, tenantStatus = checkHealth(userMessage)
            
            if False not in applicationStatus.values():
                userMessage = input("\nApplication is healthy\nDo you want me to give you its URL?\n\nMe:")
                if(userMessage in positiveResponseSet):
                    print(f"\n{appName}: URL: {url}")
            else:
                userMessage = input(f"\n{appName}: Application is not healthy!\nDo you want me to show you what fails?\n\nMe:")
                
                if(userMessage not in negativeResponseSet):
                    print(f"{appName}: URL = {url}\n{formatStatus(applicationStatus)}")
                    userMessage = input(f"\n{appName}: Do you want me provide you with some SOPs?\n\nMe:")
                    if(userMessage not in negativeResponseSet):
                        suggestedLinks = [ SOPMapping[app] for app in applicationStatus if not applicationStatus[app] ]
                        if len(suggestedLinks)==0:
                            suggestedLinks.append(parentSOPLink)
                        print(f"\n{appName}: The following link{'s' if(len(suggestedLinks)>1) else ''} might help:")
                        for link in suggestedLinks:
                                print(f"\t{link}")
        except:
            print(f"\n{appName}: Oops! looks like something went wrong.")
            continue
        finally:
            userMessage = input(f"\n{appName}: Do you want me to help you with something else?\n\nMe:")
            if(userMessage.lower() in negativeResponseSet):
                closeConversation = True
                break
            elif(userMessage.lower() in positiveResponseSet):
                outputMessage = "How may I help you?"
    print(f"\n{appName}: {closingGreeting}")
            
            
if __name__ == "__main__":
    main()




