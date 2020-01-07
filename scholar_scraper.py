import random
import time
import re
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from unidecode import unidecode
from nordvpn_randomizer import logIn, chooseRandom, getCountries


# Used for some scientists in the list that have special characters in their names
translator   = {'á': ('%C3%A1', '=aacute='),  #, '\xc3\xa1'),
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

# List of different "user agents" (mimics browser usage)
user_agents  = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.79 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36', 
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Safari/605.1.15', 
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:70.0) Gecko/20100101 Firefox/70.0',
                'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; rv:68.0) Gecko/20100101 Firefox/68.0  Firefox 68.0',
                'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:70.0) Gecko/20100101 Firefox/70.0',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36']

# Initialize some useful variables
user_agent   = user_agents[0]        # Initialize user agent (changed if human/robot test)
delays       = [7, 4, 6, 2, 10, 19]  # Random delays between url requests, to avoid overloading google servers (and avoid human/robot test)
countries    = getCountries()[1:]    # List of countries for different IPs (changed if human/robot test), using NordVPN
countries[0] = countries[0][1:]      # The first country (Albania) starts with a weird character


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

        # Get [number of citations vs. year] from the citation histogram of the scientist's scholar page
        try:
            max_year  = max([int(line.split('">'      )[1].split('</')[0]) for line in scholar_src.split('gsc_g_t' )[3:]])
            citations =     [int(line.split('">'      )[1].split('</')[0]) for line in scholar_src.split('gsc_g_al')[6:]]
            z_indexes =     [int(line.split('z-index:')[1].split('">')[0]) for line in scholar_src.split('gsc_g_al')[5:-1]]
            years     =     [max_year-z+1 for z in z_indexes]
        except ValueError:
            years, citations = [], []

        # Get h-indexes and i10-indexes (in total and from 2014 to now only)
        try:
            cite_ctrl = int(scholar_src.split('i10')[ 0].split('<td class="gsc_rsb_std">')[-4].split('</td')[0])
            h_id      = int(scholar_src.split('i10')[ 0].split('<td class="gsc_rsb_std">')[-2].split('</td')[0])
            h_id_2014 = int(scholar_src.split('i10')[ 0].split('<td class="gsc_rsb_std">')[-1].split('</td')[0])
            i_id      = int(scholar_src.split('i10')[-1].split('<td class="gsc_rsb_std">')[ 1].split('</td')[0])
            i_id_2014 = int(scholar_src.split('i10')[-1].split('<td class="gsc_rsb_std">')[ 2].split('</td')[0])
        except (ValueError, IndexError):
            cite_ctrl, h_id, h_id_2014, i_id, i_id_2014 = 0, 0, 0, 0, 0

        # Some young scientists don't have a citations histogram because they only have citations over the last year
        if cite_ctrl != 0 and citations == []:
            citations, years = [cite_ctrl], [2019]

    # Return empty list if the scientist is not famous enough for a scholar publication page
    else:
        h_id, h_id_2014, i_id, i_id_2014, years, citations = 0, 0, 0, 0, [], []

    # Build a list to be published in the tsv file
    print('%s citations to analyse for %s' % (sum(citations), real_name))
    years_to_write = range(1980, 2020)
    cites_to_write = [0 for y in years_to_write]
    for i, y in enumerate(years_to_write):
        if y in years:
            cites_to_write[i] = citations[years.index(y)]

    # Return the citations to the program
    return h_id, h_id_2014, i_id, i_id_2014, cites_to_write, coauthors_list


# Try to find scientific has a dedicated scholar publication page
def get_user_ID_and_coauthors(real_name, dblp_url):

    # Initialize and go to the dblp page of the scientist (if it exists)
    global user_agent
    search_name, last_name, dblp_url = check_for_special_characters(real_name, dblp_url)
    dblp_req = Request(dblp_url, headers={'User-Agent': user_agent})
    try:
        dblp_src = urlopen(dblp_req).read().decode('utf-8')

    # In rare cases, the scientist name was changed and is linked in the 404 error page
    except HTTPError as error:
        error_src  = error.read().decode('utf-8')
        key_string = 'Did you mean:</p><ul><li><a href="'
        if key_string in error_src:
            dblp_url = error_src.split(key_string)[1].split('">')[0]
            dblp_req = Request(dblp_url, headers={'User-Agent': user_agent})
            dblp_src = urlopen(dblp_req).read().decode('utf-8')
        else:
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
        try:
            scholar_url = 'https://scholar' + dblp_src.split('"publ-section"')[1].split('https://scholar')[1].split('">')[0]
        except IndexError:
            return None, []

    # Try to connect to google scholar, avoiding robot issues
    scholar_says_Im_robot = True
    stop_trying_count     = 0
    while scholar_says_Im_robot:

        # Stops abusing google scholar in case it is too angry
        if stop_trying_count > 5:
            print('Already many IP were tried... Try to find a manual solution!')
            exit()
        stop_trying_count += 1

        # Tries to open the scholar url obtained from the dblp wep page
        try:
            scholar_req = Request(scholar_url + '+' + unidecode(last_name), headers={'User-Agent': user_agent})
            scholar_src = urlopen(scholar_req).read().decode('utf-8')
            time.sleep(random.choice(delays))
        except UnicodeEncodeError as error:
            print('The last name induced an url encoding error. Skipping this scientist...')
            scholar_src = []

        # Check for 429 error (too many requests), in which case the VPN IP address is changed
        except HTTPError:
            print('Google scholar HTTPError 429: IP address is changed...')
            user_agent = random.choice(user_agents)
            try:
                logIn(chooseRandom(countries))
                time.sleep(10)
            except:
                print('NordVPN is not installed on this computer. Try to find a manual solution!')
                exit()
            continue

        # Check for the human/robot captcha test, in which case the VPN IP address is changed
        if '"gs_captcha_f"' in scholar_src:
            print('Google scholar Human/Robot test: IP address is changed...')
            user_agent = random.choice(user_agents)
            try:
                logIn(chooseRandom(countries))
                time.sleep(10)
            except:
                print('NordVPN is not installed on this computer. Try to find a manual solution!')
                exit()
            continue

        # If everything went fine, continue below this while loop
        scholar_says_Im_robot = False

    # Search for an existing scholar ID of the scientist
    user_ID = None
    try:
        crucial_str = scholar_src.split('<div class="gs_a">')[1]
        crucial_str = re.split(last_name.lower(), crucial_str, flags=re.IGNORECASE)[0]
        crucial_str = crucial_str.split(',')[-1].split('">')[0].split('&amp;hl=')[0]
        if len(crucial_str) > 28 and crucial_str[-28:-12] == '/citations?user=':
            user_ID = crucial_str[-12:]
    except:
        print('Error in the search, probably because the scientist has no scholar page.')

    # Return the user ID and the coauthors list to the program
    return user_ID, coauthors


# Make sure names with special characters can be found
def check_for_special_characters(real_name, dblp_url):
    
    # Strings cannot be modified, lists can
    last_name  = list(real_name.split(' ')[-1])
    probe_name = real_name.split(' ')
    probe_name.insert(0, probe_name.pop(-1))
    probe_name = list(' '.join(probe_name))
    probe_dblp = list(dblp_url.replace('==','='))

    # Special case for apostrophies
    if "'" in real_name:
        probe_dblp[probe_dblp.index('=')+1] = probe_dblp[probe_dblp.index('=')+1].capitalize()
        probe_name[probe_name.index("'")+1] = probe_name[probe_name.index("'")+1].capitalize()
        probe_name[probe_name.index("'")]   = '%27'
        if '' in last_name:
            last_name[ last_name .index("'")]   = '&#39;'

    # Special case for dashes
    if '-' in real_name:
        probe_dblp[probe_dblp.index('=')+1] = probe_dblp[probe_dblp.index('=')+1].capitalize()
        probe_name[probe_name.index('-')+1] = probe_name[probe_name.index('-')+1].capitalize()
        if '-' in last_name:
            last_name = last_name[:last_name.index('-')]
        
    # Go through every characters and modify if necessary
    else:
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
    last_name   = ''.join(last_name)
    dblp_url    = ''. join(probe_dblp)
    return search_name, last_name, dblp_url
