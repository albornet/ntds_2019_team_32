#!/usr/bin/env python3
import subprocess
import random
import re


# Generate a list of the current countries with available servers for your nordvpn account.
def getCountries():
    nord_output = subprocess.Popen(["nordvpn", "countries"], stdout=subprocess.PIPE)
    countries = re.split("[\t \n]", nord_output.communicate()[0].decode("utf-8"))
    while "" in countries:
        countries.remove("")
    return countries


# Randomly choose a country out of the available countries list.
def chooseRandom(country_list):
    return country_list[random.randrange(0, len(country_list))]


# Take the randomly chosen country and attempt to log in to NordVPN using that country.
def logIn(random_country):
    print("{} has been selected as the random country.".format(random_country))
    subprocess.call(["nordvpn", "c", random_country])