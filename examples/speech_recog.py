import speech_recognition as sr


recognitizer = sr.Recognizer()




with sr.Microphone() as source:

    print("Please speak anything")
    audio = recognitizer.listen(source)
        
    try:
        Spoken_Text = recognitizer.recognize_sphinx(audio)
        print("The user spoke: {}".format(Spoken_Text))

    except sr.UnknownValueError:
        print("Sorry, could not understand the audio")
        
    except sr.RequestError as e:
        print("Sphinx error; {0}".format(e))
        
    except:
        print("Sorry could not recognize the test")
        print("Sphinx error; {0}".format(e))
        
        