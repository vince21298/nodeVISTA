"""
simpleSetup2: runs POST the JS setup

NOTE: for 1.2 USERS (and their signatures) still done here. Next jsSetup will take this over and the User setup part
will be removed from here.
"""

import os
import re
import sys
import logging
import time
sys.path = ['rasUtilities'] + sys.path

import OSEHRASetup
from OSEHRAHelper import ConnectToMUMPS, PROMPT

logging.basicConfig(level=logging.INFO,
                    #filename='debug.log',
                    #format='%(asctime)s %(levelname)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

"""
ConnectToMUMPS relies on environment:
- is GTM => defined os.getenv('gtm_dist') == /home/nodevista/lib/gtm
- is Linux => defined sys.platform == 'linux2'
"""
# print "Platform", sys.platform, "GT.M MUMPS VM", os.getenv('gtm_dist'), "GTM Prompt", os.getenv("gtm_prompt")

LOGFILE = '/home/nodevista/log/pySetup.txt'

"""
Expect to be called from Shell - PRINT can be read with 
     result=`python simpleSetup.py`
     if [ "$result" != "OK" ]; then ... 
"""
def pySetup():

    try:
        print "Connecting to MUMPS roll n scroll ..."
        VistA=ConnectToMUMPS(LOGFILE)
    except:
        print "EXIT_PYS_CANT_CONNECT_TO_MUMPS"
        return

    try:
        print "Setting up basics ..."
        postImportSetupBasics(VistA)
    except:
        print "EXIT_PYS_CANT_SETUP_BASICS_BUT_GOING_ON"
        VistA=ConnectToMUMPS(re.sub(r'Setup', 'Setup1', LOGFILE))

    try:
        print "Now setting up Users (signatures only now) ..."
        postImportSetupUsers(VistA)
    except Exception as e:
        print "EXIT_PYS_PROBLEM_SETTING_USERS_BUT_GOING_ON"
        VistA=ConnectToMUMPS(re.sub(r'Setup', 'Setup2', LOGFILE))

    try:
        print "Now setting up Patients ..."
        # have to reset VistA as Signature Setup halts from VISTA
        time.sleep(10)
        VistA=ConnectToMUMPS(re.sub(r'Setup', 'Setup3', LOGFILE)) # reset up VISTA
        postImportSetupPatients(VistA)
    except:
        print "EXIT_PYS_CANT_SETUP_PATIENTS"
        return

    print "PY Setup FileMan, User, Patient ... Complete OK"

def postImportSetupBasics(VistA):
    """
    Basics of postImportSetup from initializeFileMan to division addition
    """

    # from test.cmake
    TEST_VISTA_SETUP_SITE_NAME = "DEMO.NODEVISTA.ORG"
    TEST_VISTA_STATION_NUMBER = "999"

    VistA.wait(PROMPT,60)

    # Reset site name to domain name, station number too. Uses D ^DINIT
    # ... sets (via ^ZUSET) ZUGTM to ZU and ^DINIT for MSC FileMan
    OSEHRASetup.initializeFileman(VistA, TEST_VISTA_SETUP_SITE_NAME, TEST_VISTA_STATION_NUMBER) # from 6161

    # Start TaskMan through the XUP Menu system.
    OSEHRASetup.restartTaskMan(VistA)

def postImportSetupUsers(VistA):
    """
    Setup Users - paired down in v1.2. Now only resetting signatures.
    """

    # Required to add Patient, User etc 
    OSEHRASetup.addSystemManager(VistA)

    # The Sikuli test for CPRS orders a Streptozyme test for the patient
    # This information ensures the test can be ordered at the VistA Health care
    # Facility
    # OSEHRASetup.setupStrepTest(VistA)
    # OSEHRASetup.signonZU(VistA,"SM1234","SM1234!!")

    """
    Note that these verifies are temporary - VISTA forces a reset which is done as part of
    the electronic signature setups below. It's the reset signature that will be used from
    now on
    """    
    OSEHRASetup.addDoctor(VistA,"ALEXANDER,ROBERT","RA","000000029","M","fakedoc1","2Doc!@#$")

    #Enter the Nurse Mary Smith
    OSEHRASetup.addNurse(VistA,'SMITH,MARY','MS','000000030','F','fakenurse1','2Nur!@#$')

    # Add a clerk user with permissions for Problem List Data entry
    OSEHRASetup.addClerk(VistA,"CLERK,JOE","JC","000000112","M","fakeclerk1","2Cle!@#$")

    # Add a Pharmacist
    OSEHRASetup.addPharmacist(VistA,"SHARMA,FRED","FS","000000031","M","fakepharma1","2Pha!@#$");

    #Create a new Order Menu
    OSEHRASetup.createOrderMenu(VistA)

    #Give all users of the instance permission to mark allergies as "Entered in error')
    OSEHRASetup.addAllergiesPermission(VistA)
    
    #Give Mary Smith permission to create shared templates
    OSEHRASetup.addTemplatePermission(VistA,"MS")

    # Add clinic via the XUP menu to allow scheduling - DOCKER V2 move to JS
    OSEHRASetup.createClinic(VistA,'VISTA HEALTH CARE','VHC','M')
    
    """
    The sleep and ConnectToMUMPS is needed as createClinic has halted and 
    setup signature does a similar thing. Could debug and stop the halts but 
    as replacing with JS, not worth it.
    
    Same "logic" is in OSEHRA's PostImportSetupScript.py
    """
    time.sleep(10)
    
    VistA=ConnectToMUMPS(LOGFILE)
    #Set up the Doctors electronic signature
    OSEHRASetup.setupElectronicSignature(VistA,"fakedoc1",'2Doc!@#$','1Doc!@#$','ROBA123')

    VistA=ConnectToMUMPS(LOGFILE)
    # #Set up the Nurse electronic signature
    OSEHRASetup.setupElectronicSignature(VistA,"fakenurse1","2Nur!@#$","1Nur!@#$","MARYS123")

    VistA=ConnectToMUMPS(LOGFILE)
    # #Set up the Clerk verification code
    OSEHRASetup.setupElectronicSignature(VistA,"fakeclerk1","2Cle!@#$","1Cle!@#$","CLERKJ123")

def postImportSetupPatients(VistA):

    # Add patient to the instance using the registration menu.
    # Not using the Clerk user to avoid dropping the connection on the error when trying to connect to the MPI.
    # and the Register a Patient menu option.
    # The patient can be a veteran but not service connected
    # Function arguments:
    # VistA, Patient Name, Patient Sex,Patient DOB, Patient SSN, Patient Veteran?
    OSEHRASetup.addPatient(VistA,'dataFiles/patdata0.csv')

def main():
    pySetup()

if __name__ == "__main__":
    main()
