#!/usr/bin/python
#
# Author: fLa
#
from urllib2 import Request, urlopen, URLError, HTTPError
import json
import time
import sys



#==============================================================================================
# Create your application API keys from https://trakt.tv/oauth/applications below (the redirect URI can be anything)
# Either fill in the 64 character Client ID and Client Secret below or leave 
# these variables empty ("") and the script will prompt for them on execution
clientID     = ""
clientSecret = ""
#==============================================================================================



class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'

headers = { 
  'Content-Type': 'application/json'
}
    
#------------------------------------------------------------------------------------------

def getDeviceCode(clientID):
  """Generates a new device code for an API application
  clientID -- Application API client ID from https://trakt.tv/oauth/applications
  """
  values = """
    {
        "client_id": "%(clientid)s"
    }
  """ % {
    'clientid': clientID }  

  # Send request to get device code
  request_deviceCode = Request('https://api.trakt.tv/oauth/device/code', data=values, headers=headers)
  try:
    response = urlopen(request_deviceCode)
  except HTTPError as e:
    if e.code == 403:
      print(color.RED + "Invalid API client ID or unapproved app" + color.END)
      exit(1)
    else:
      print(color.RED + "Unexpected HTTP return code: %i" % e.code + color.END)
      exit(1)
  except URLError as e:
    print(color.RED + "ERROR\nURL request failed!" + color.END)  
    print(e) 
    exit(1)
  except Exception:
    print(color.RED + "ERROR\nUnexpected exception while requesting device code." + color.END)         
    exit(2)
  
  # Parse the json response
  response_body = response.read()                  
  parsed_json = json.loads(response_body)
  deviceCode      = parsed_json["device_code"]
  userCode        = parsed_json["user_code"]
  pollinterval    = parsed_json["interval"]
  expiresin       = parsed_json["expires_in"]
  verificationUrl = parsed_json["verification_url"]

  # Request user to authenticate application API device code using the PIN
  print("\nVisit the URL below and approve the application API to use\nyour Trakt.tv account using this PIN code %s%s%s" % (color.BLUE, userCode, color.END))
  print(color.UNDERLINE+verificationUrl+color.END)
  return deviceCode, pollinterval
  

def getToken(deviceCode, clientID, clientSecret):
  """ Gets a token derived from device code, client ID and client secret.
  deviceCode -- The application API device code, provided by getDeviceCode(clientID)
  clientID -- The application API client ID.
  clientSecret -- The application API client secret.
  """

# Bugg reportted to Trakt.tv, client_secret is not needed:
#      "client_secret": "%(clientsecret)s",
#    'clientsecret': clientSecret }    
  values = """
    {
      "code": "%(devicecode)s",
      "client_id": "%(clientid)s"
    }
  """ % {
    'devicecode': deviceCode,
    'clientid': clientID }

  # Send the request for the device API token
  request_getToken = Request('https://api.trakt.tv/oauth/device/token', data=values, headers=headers)
  try:
    response = urlopen(request_getToken)
  except HTTPError as e:
    return e.code, ""
  except URLError as e:
    print(color.RED + "ERROR\nURL request failed!" + color.END)
    print(e)
    exit(1)
  except Exception:    
    print(color.RED + "ERROR\nUnexpected exception while requesting device token." + color.END)
    exit(2)
  else:
    # We received it
    return 200, response.read()


#====================== MAIN =============================
def main(argv):
  global clientID
  global clientSecret
  
  # Check authorization details
  if not clientID or not clientSecret:
    print(color.YELLOW + "Create your application API keys at https://trakt.tv/oauth/applications below (the redirect URI cam be anything)" + color.END)
  if not clientID:
    clientID = raw_input("Enter your Trakt.tv API app Client ID    : ")  
  if len(clientID) != 64:
    print(color.RED + "The client ID is invalid, should be 64 characters." + color.END)
    exit(1)          
  if not clientSecret:
    clientSecret = raw_input("Enter your Trakt.tv API app Client Secret: ")
  if len(clientSecret) != 64:
    print(color.RED + "The client secret is invalid, should be 64 characters." + color.END)
    exit(1)
    
  # Get device code
  code, pollint = getDeviceCode(clientID)

  # Get access token 
  while True:
    responseCode, responseData = getToken(code, clientID, clientSecret)
    if responseCode == 200:
      # We got the device code
      break
    if responseCode == 400:
      print(color.YELLOW + "Waiting for you to approve the PIN code..." + color.END)
      time.sleep(pollint)
    elif responseCode == 404:
      print(color.RED + "Failed! Invalid device code." + color.END)
      exit(1)
    elif responseCode == 409:
      print(color.RED + "Failed! Code already used." + color.END)
      exit(1)
    elif responseCode == 410:
      print(color.YELLOW + "Expired - the tokens have expired." + color.END)
      exit(1)
    elif responseCode == 418:
      print(color.RED + "Failed! User explicitly denied this code." + color.END)
      exit(1)
    elif responseCode == 429:
      print(color.YELLOW + "Slowing down - polling too quickly..." + color.END)
      time.sleep(10)
    else:
      print(color.RED + "Failure. Unexpected response code: " + responseCode + color.END)
      exit(2)

  # Parse response data
  try:
    parsed_json = json.loads(responseData)
  except ValueError, e:
    print(color.RED + "Error. Invalid data received:" + color.END)
    print(responseData)
    exit(1)
    
  # Parse out the access token
  accessToken      = parsed_json["access_token"]
  #refreshToken     = parsed_json["refresh_token"]

  if accessToken:
    print(color.GREEN + "PIN approved.\n" + color.GREEN)
    print(color.GREEN + "You new authorization bearer access token for this client ID is " + color.BOLD + accessToken + color.END + "\n")
  else:
    print(color.RED + "Something went wrong, access token is missing. This was the response data:" + color.END)
    print(responseData)

  print(color.CYAN + "EXITING" + color.END)
  exit(0)

if __name__ == "__main__":
    main(sys.argv)
