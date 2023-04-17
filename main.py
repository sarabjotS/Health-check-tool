import requests
from requests.exceptions import ConnectionError
from enum import Enum

appName = "DiagnoBuddy"
userName = "Me"
openingGreeting = f"Hi, I am {appName}. How may I help you?"
closingGreeting = f'Thanks for using {appName}. Bye and have a nice day!'
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
        print("Sorry! GoogleLLM is unreachable at the moment. Please try again after some time.")
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
        urlEndIndex = indexOfKronosDotCom+len(KRONOS_DOT_COM)
        healthCheckUrl = environment[ : urlEndIndex ]
        if " " in healthCheckUrl:
            urlStartIndex = healthCheckUrl.rindex(" ")+1
            if(urlStartIndex > urlEndIndex):
                healthCheckUrl = healthCheckUrl[ urlStartIndex : ]
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
        message = input(f"\n{appName}: I could not figure out the environment name from your message.\nCould you please help me with the name of the environment or its URL?\n\n{userName}: ")
        if(message.lower() not in negativeResponseSet):
            environment = message
    URL = getURL(environment)
    return URL, *runHealthCheck(URL+"healthCheck/advanced")



def main():
    closeConversation = False
    outputMessage = openingGreeting

    while(not closeConversation):
        
        print(f"\n{appName}: {outputMessage}\n")
        userMessage = input(f"{userName}: ")
        if(closeConversation or (userMessage.lower() in closingWords)):
            closeConversation = False
            break
        
        if not any([ word in userMessage for word in triggerHealthCheckWords ]):
            userMessage = askLLM("Rephrase this: " + userMessage)['predictions'][0]
            if not any([ word in userMessage for word in triggerHealthCheckWords ]):
                outputMessage = "Sorry, I could not comprehend your request. Could you please rephrase your request?"
                continue
        url, serviceStatus, applicationStatus, tenantStatus = str(), dict(),dict(),dict()
        try:
            url, serviceStatus, applicationStatus, tenantStatus = checkHealth(userMessage)
            
            if False not in applicationStatus.values():
                userMessage = input(f"\n{appName}: Yay! Your application is super healthy on the specified environment.\nDo you want me to help you with its URL?\n\n{userName}: ")
                if(userMessage in positiveResponseSet):
                    print(f"\n{appName}: URL: {url}")
            else:
                userMessage = input(f"\n{appName}: Sorry to say that your application is not running healthy on the specified environment!\nDo you want me to show you details around what is failing?\n\n{userName}: ")
                if(userMessage not in negativeResponseSet):
                    print(f"{appName}: URL = {url}\n{formatStatus(applicationStatus)}")
                    
                    userMessage = input(f"\n{appName}: Do you want me to help you with SOPs to address this issue?\n\n{userName}: ")
                    if(userMessage not in negativeResponseSet):
                        suggestedLinks = [ SOPMapping[app] for app in applicationStatus if not applicationStatus[app] ]
                        if len(suggestedLinks)==0:
                            suggestedLinks.append(parentSOPLink)
                        print(f"\n{appName}: The following link{'s' if(len(suggestedLinks)>1) else ''} might help:")
                        for link in suggestedLinks:
                            print(f"\t{link}")
               
        except ConnectionError as error:
            print(f"\n{appName}: Oops! The specified environment is either invalid or unreachable. Please check the environment name or try again later.")             
        except:
            print(f"\n{appName}: Something went wrong. Please try again.")
        finally:
            userMessage = input(f"\n{appName}: Do you want me to help you with something else?\n\n{userName}: ")
            if(userMessage.lower() in negativeResponseSet):
                closeConversation = True
                break
            elif(userMessage.lower() in positiveResponseSet):
                outputMessage = "How may I help you?"
    print(f"\n{appName}: {closingGreeting}")
            
            
if __name__ == "__main__":
    main()




