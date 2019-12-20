import random
import time
import re
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from NordVPN_Randomizer import logIn, chooseRandom, getCountries
user_agents = ['Mozilla/5.0 (compatible; 008/0.83; http://www.80legs.com/webcrawler.html) Gecko/2008032620',
               'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
               'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML like Gecko) Chrome/44.0.2403.155 Safari/537.36',
               'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
               'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36',
               'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36',
               'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36',
               'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2226.0 Safari/537.36',
               'Mozilla/5.0 (Windows NT 6.4; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2225.0 Safari/537.36',
               'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2225.0 Safari/537.36',
               'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2224.3 Safari/537.36',
               'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.93 Safari/537.36']
user_agent  = user_agents[0]
delays      = [7, 4, 6, 2, 10, 19]
translator  = {'á': ('%C3%A1', '=aacute='),  #, '\xc3\xa1'),
              'é': ('%C3%A9', '=eacute='),  #, '\xc3\xa9'),
              'í': ('%C3%AD', '=iacute='),  #, '\xc3\xad'),
              'ó': ('%C3%B3', '=oacute='),  #, '\xc3\xb3'),
              'ú': ('%C3%BA', '=uacute='),  #, '\xc3\xba'),
              'ý': ('%C3%BD', '=yacute='),  #, '\xc3\xbd'),
              'è': ('%C3%A8', '=egrave='),  #, '\xc3\xa8'),
              'ò': ('%C3%B2', '=ograve='),  #, '\xc3\xb2'),
              'ê': ('%C3%AA', '=ecirc=' ),  #, '\xc3\xaa'),
              'ô': ('%C3%B4', '=ocirc=' ),  #, '\xc3\xb4'),
              'ä': ('%C3%A4', '=auml='  ),  #, '\xc3\xa4'),
              'ë': ('%C3%AB', '=euml='  ),  #, '\xc3\xab'),
              'ï': ('%C3%AF', '=iuml='  ),  #, '\xc3\xaf'),
              'ö': ('%C3%B6', '=ouml='  ),  #, '\xc3\xb6'),
              'ü': ('%C3%BC', '=uuml='  ),  #, '\xc3\xbc'),
              'ã': ('%C3%A3', '=atilde='),  #, '\xc3\xa3'),
              'õ': ('%C3%B5', '=otilde='),  #, '\xc3\xb5'),
              'ñ': ('%C3%B1', '=ntilde=')}  #, '\xc3\xb1')}

# Get number of citations per each year, for any scientist featured on google scholar
def get_citation_statistics(real_name, dblp_url):

    # Assess whether the scientific has a dedicated scholar publication page
    scientist_ID, coauthors_list = get_user_ID_and_coauthors(real_name, dblp_url)
    if scientist_ID is not None:

        # Go to the scholar publication page of the scientist
        scholar_url  = 'https://scholar.google.com/citations?user=' + scientist_ID
        scholar_req  =  Request(scholar_url, headers={'User-Agent': user_agent})
        scholar_src  =  urlopen(scholar_req).read().decode('utf-8')
        time.sleep(random.choice(delays))

        # Get the number of citations with the correspond years
        max_year  = max([int(line.split('">'      )[1].split('</')[0]) for line in scholar_src.split('gsc_g_t' )[3:]])
        citations =     [int(line.split('">'      )[1].split('</')[0]) for line in scholar_src.split('gsc_g_al')[6:]]
        z_indexes =     [int(line.split('z-index:')[1].split('">')[0]) for line in scholar_src.split('gsc_g_al')[5:-1]]
        years     =     [max_year-z+1 for z in z_indexes]

    # Return empty list if the scientist is not famous enough for a scholar publication page
    else:
        years, citations = [], []

    # Build a list to be published in the tsv file
    print('%s citations to analyse for %s' % (sum(citations), real_name))
    years_to_write = range(1980, 2020)
    cites_to_write = [0 for y in years_to_write]
    for i, y in enumerate(years_to_write):
        if y in years:
            cites_to_write[i] = citations[years.index(y)]

    # Return the citations to the program
    return cites_to_write, coauthors_list


# Try to find scientific has a dedicated scholar publication page
def get_user_ID_and_coauthors(real_name, dblp_url):

    # Initialize and go tht the dblp page of the scientist (if it exists)
    global user_agent
    last_name = real_name.split(' ')[-1]
    search_name, dblp_url = check_for_special_characters(real_name, dblp_url)
    dblp_req  = Request(dblp_url, headers={'User-Agent': user_agent})
    try:
        dblp_src = urlopen(dblp_req).read().decode('utf-8')
    except HTTPError:
        return None, []

    # Find all coauthors for this scientist
    try:
        coauthors = [p.split('">')[1].split('</')[0] for p in dblp_src.split('"coauthor-section"')[1].split('"person"')[1:]]
    except IndexError:
        coauthors = [] 

    # Search for this scientist's last publication with first authorship on google scholar
    try:
        scholar_url = 'https://scholar' + dblp_src.split('au=' + search_name)[1].split('https://scholar')[1].split('">')[0]
    except IndexError:
        scholar_url = 'https://scholar' + dblp_src.split('"publ-section"')[1].split('https://scholar')[1].split('">')[0]

    # Try to connect to google scholar, avoiding robot issues
    google_scholar_thinks_I_am_a_robot = True
    while(google_scholar_thinks_I_am_a_robot):
        try:
            scholar_req = Request(scholar_url + '+' + last_name, headers={'User-Agent': user_agent})
            scholar_src = urlopen(scholar_req).read().decode('utf-8')
        except HTTPError:
            print('Google scholar HTTPError 429.')
            exit()
            # print('Google scholar HTTPError 429: IP address is changed...')
            # logIn(chooseRandom(getCountries()))
            # user_agent = random.choice(user_agents)
            # continue
        if 'Robot' in scholar_src or 'robot' in scholar_src:
            print('Google scholar Human/Robot test.')
            exit()
            # print('Google scholar Human/Robot test: IP address is changed...')
            # logIn(chooseRandom(getCountries()))
            # user_agent = random.choice(user_agents)
            # continue
        google_scholar_thinks_I_am_a_robot = False
    time.sleep(random.choice(delays))

    # Search for an existing scholar ID of the scientist
    user_ID = None
    try:
        crucial_str = scholar_src.split('<div class="gs_a">')[1]
        crucial_str = re.split(last_name.lower(), crucial_str, flags=re.IGNORECASE)[0]
        crucial_str = crucial_str.split(',')[-1].split('">')[0]
        if len(crucial_str) > 62 and crucial_str[-62:-46] == '/citations?user=':
            user_ID = crucial_str[-46:-34]
        if len(crucial_str) > 49 and crucial_str[-49:-33] == '/citations?user=':
            user_ID = crucial_str[-33:-21]
    except:
        pass
    # Return the user ID and the coauthors list to the program
    return user_ID, coauthors


# Make sure names with special characters can be found
def check_for_special_characters(real_name, dblp_url):
    
    # Strings cannot be modified, lists can
    probe_name = real_name.split(' ')
    probe_name.insert(0, probe_name.pop(-1))
    probe_name = list(' '.join(probe_name))
    probe_dblp = list(dblp_url.replace('==','='))

    # Go through every characters and modify if necessary
    is_special = False
    for i, c_name in enumerate(probe_name):
        for c_special in translator.keys():
            if c_special == c_name:
                probe_name[i   ] = translator[c_special][0]
                probe_dblp[i+35] = translator[c_special][1]
                is_special       = True

    # Regenerate the corrected name and url
    search_name = ''.join(probe_name).split(' ')
    search_name.append(search_name.pop(0))
    search_name = '+'.join(search_name)
    dblp_url    = ''. join(probe_dblp)
    return search_name, dblp_url


# Debug 0
def get_user_ID_debug(real_name, scholar_src):
    
    # # Look for an existing scholar ID of the scientist
    # last_name   = real_name.split(' ')[-1]
    # crucial_str = scholar_src.split(last_name)[0].split('">')[-2]
    # print(crucial_str[-62:-46])
    # if len(crucial_str) > 49 and crucial_str[-62:-46] == '/citations?user=':
    #     print(crucial_str[-46:-34])
    #     print(len(crucial_str[-46:-34]))

    for line in scholar_src.split('gsc_g_al')[6:-1]:
        print(int(line.split('z-index:')[1].split('">')[0]))


# Debug 1
def debug_function(years, citations):

    # Return both arrays to the main program
    years_to_write = range(1980, 2020)
    cites_to_write = [0 for y in years_to_write]
    for i, y in enumerate(years_to_write):
        if y in years:
            cites_to_write[i] = citations[years.index(y)]
    print(years_to_write)
    print(cites_to_write)


# Debug
if __name__ == '__main__':
    with open('debug_source.txt', 'r') as file:
        # get_user_ID_debug(real_name='Kasper Larsen', scholar_src=''.join(file.readlines()))
        # debug_function([2012, 2013, 2014, 2015], [2, 5, 14, 20])
        # print(check_for_special_characters('Sonja Schär', 'http://dblp.uni-trier.de/pers/hd/s/Sch==r:Sonja.html'))
        # print(check_for_special_characters('Santiago Ontañón', 'http://dblp.uni-trier.de/pers/hd/o/Onta====n:Santiago.html'))
        print(check_for_special_characters('Santiãgo De Palamé', 'http://dblp.uni-trier.de/pers/hd/p/Palam==:Santi==go_De.html'))
        # print(check_for_special_characters('Sarah Chasins', 'http://dblp.uni-trier.de/pers/hd/c/Chasins:Sarah.html'))