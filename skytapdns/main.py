# Required: install cli53. Github repo: https://github.com/barnybug/cli53

import commands
from datetime import datetime
import json
import pyconfluence as pyco
import time


def recreate_all_vm_dns(e):
    """Recreate DNS record sets and CNAMEs belonging to enviroment VMs.

    Parameters:
    e = Skytap Environment object.
    create = if False, end the function after deletion.
    """

    vm_hostname = "error"
    ip = None

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open("dns.log", "a") as logfile:
        logfile.write("\n\n\n[" + timestamp + "] Starting DNS writing function for " + e.name + ".\n")


    print ("Managing DNS settings for " + e.name + "...")

    for v in e.vms:
        for i in v.interfaces:
            if (str(i.hostname) == "None" ):
                continue
            vm_hostname = i.hostname
            int_data = json.loads(i.json())
            try:
                valid_vpns = ["vpn-661182", "vpn-3631944", "vpn-3288770",
                              "vpn-15108689"]
                for n in int_data["nat_addresses"]["vpn_nat_addresses"]:
                    if (n["vpn_id"] in valid_vpns):
                        ip = n["ip_address"]
            except (KeyError, TypeError, IndexError):
                # Default to US in case of buggery
                ip = i.ip

        dns_name = (vm_hostname + "-" + str(e.id) + ".skytap")

        if ip:
            created = False

            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open("dns.log", "a") as logfile:
                logfile.write("[" + timestamp + "] Beginning to create record set for " + vm_hostname + ".\n")

            print ("Creating record set for " + vm_hostname + "...")

            while not created:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                with open("dns.log", "a") as logfile:
                    logfile.write("[" + timestamp + "] Requesting creation of " + vm_hostname + " record set.\n")

                with open("skytapdns/recordset_A.json", "r") as file:
                    filedata = file.read()

                filedata = filedata.replace("DNS_NAME", vm_hostname + "-" + str(e.id) + ".skytap.fulcrum.net")
                filedata = filedata.replace("VALUE_NAME", ip)

                with open("skytapdns/recordset_A_temp.json", "w") as file:
                    file.write(filedata)

                status, output = commands.getstatusoutput("aws route53 change-"
                                                          "resource-record-sets"
                                                          " --hosted-zone-id "
                                                          "Z2M6JEL5C4DYRL "
                                                          "--change-batch file://"
                                                          "~/autodocs/skytapdns"
                                                          "/recordset_A_temp.json")

                time.sleep(2)

                try:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    with open("dns.log", "a") as logfile:
                        logfile.write("[" + timestamp + "] Checking to see if the record set status for " + vm_hostname + " is still pending.\n")

                    status_id = json.loads(output)["ChangeInfo"]["Id"]

                    status = "blah"
                    while (status != "INSYNC"):
                        status, output = commands.getstatusoutput("aws route53 get-change --id " + status_id)

                        status = json.loads(output)["ChangeInfo"]["Status"]

                        time.sleep(10)

                    created = True

                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    with open("dns.log", "a") as logfile:
                        logfile.write("[" + timestamp + "] Successfully created record set for " + vm_hostname + ".\n")

                    print ("Created record set: " + vm_hostname + "-" + str(e.id) + ".skytap.fulcrum.net")

                except: # If an exception is caught, then we'll try again.
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    with open("dns.log", "a") as logfile:
                        logfile.write("[" + timestamp + "] Failed to create record set for " + vm_hostname + ", and will retry. Error returned from AWS: " + output + "\n")

                    print ("AWS output caused an error. Retrying in 4 seconds...")
                    time.sleep(2)

                if not created:
                    time.sleep(2)

        env_dns_alias = None

        if "env_dns_alias" in e.user_data:
            env_dns_alias = e.user_data.env_dns_alias

        if env_dns_alias:
            created = False

            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open("dns.log", "a") as logfile:
                logfile.write("[" + timestamp + "] Beginning to create CNAME for " + vm_hostname + ".\n")

            print ("Creating CNAME for " + vm_hostname + "...")
            while not created:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                with open("dns.log", "a") as logfile:
                    logfile.write("[" + timestamp + "] Requesting creation of " + vm_hostname + " CNAME.\n")

                with open("skytapdns/recordset_CNAME.json", "r") as file:
                    filedata = file.read()

                filedata = filedata.replace("DNS_NAME", vm_hostname + "-" + env_dns_alias + ".skytap.fulcrum.net")
                filedata = filedata.replace("VALUE_NAME", vm_hostname + "-" + str(e.id) + ".skytap.fulcrum.net")

                with open("skytapdns/recordset_CNAME_temp.json", "w") as file:
                    file.write(filedata)

                status, output = commands.getstatusoutput("aws route53 change-"
                                                          "resource-record-sets"
                                                          " --hosted-zone-id "
                                                          "Z2M6JEL5C4DYRL "
                                                          "--change-batch file://"
                                                          "~/autodocs/skytapdns"
                                                          "/recordset_CNAME_temp.json")

                time.sleep(2)

                try:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    with open("dns.log", "a") as logfile:
                        logfile.write("[" + timestamp + "] Checking to see if record set status for " + vm_hostname + " is still pending.\n")

                    status_id = json.loads(output)["ChangeInfo"]["Id"]

                    status = "blah"
                    while (status != "INSYNC"):
                        status, output = commands.getstatusoutput("aws route53 get-change --id " + status_id)

                        status = json.loads(output)["ChangeInfo"]["Status"]

                        time.sleep(10)

                    created = True

                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    with open("dns.log", "a") as logfile:
                        logfile.write("[" + timestamp + "] Successfully created CNAME for " + vm_hostname + ".\n")

                    print ("Created CNAME: " + vm_hostname + "-" + env_dns_alias + ".skytap.fulcrum.net")
                except:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    with open("dns.log", "a") as logfile:
                        logfile.write("[" + timestamp + "] Failed to create CNAME for " + vm_hostname + ", and will retry. Error returned from AWS: " + output + "\n")

                    print ("AWS output caused an error. Retrying in 4 seconds...")
                    time.sleep(2)

                if not created:
                    time.sleep(2)


    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open("dns.log", "a") as logfile:
        logfile.write("[" + timestamp + "] Finished setting up DNS settings for this environment.\n")
# def delete_listed_dns(name):
#     """Delete DNS names as listed in a Confluence page."""
#     to_delete = []
#     to_delete_cname = []
#
#     content = pyco.get_page_content(pyco.get_page_id(name, "AutoDocs"))
#     env_id = content[content.find("Environment ID: ")+16:content.find("Environment ID: ")+23]
#
#     cname = None
#
#     if "Grey</ac:parameter><ac:parameter ac:name=\"title\">" in content:
#         cname = content[content.find("Grey</ac:parameter><ac:parameter ac:name=\"title\">")+49:content.find("</ac:parameter></ac:structured-macro></p><p>&nbsp;</p><p><strong>Additional Details")]
#
#     children = json.loads(pyco.get_page_children(pyco.get_page_id(name, "AutoDocs")))
#     for vm in children["results"]:
#         to_delete.append(vm["title"][:vm["title"].find(" - ")] + "-" + str(env_id) + ".skytap")
#         if cname:
#             to_delete_cname.append(vm["title"][:vm["title"].find(" - ")] + "-" + cname + ".skytap")
#
#     for vm in to_delete:
#         status, output = commands.getstatusoutput("cli53 rrdelete Z2M6JEL5C4DYRL"
#                                                   " " + vm + " A")
#
#     for vm in to_delete_cname:
#         status, output = commands.getstatusoutput("cli53 rrdelete "
#                                                   "Z2M6JEL5C4DYRL "
#                                                   "" + vm + " CNAME")
