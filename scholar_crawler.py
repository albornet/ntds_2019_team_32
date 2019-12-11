from urllib.request import Request, urlopen

scientists_list = [('Michael', 'Herzog'), ('Greg', 'Francis'), ('Adrien', 'Doerig'), ('Wulfram', 'Gerstner')]
for (first_name, last_name) in scientists_list:

	google_url    = 'https://www.google.com/search?q='+first_name+last_name+'scholar'
	google_req    = Request(google_url, headers={'User-Agent': 'Mozilla/5.0'})
	google_source = str(urlopen(google_req).read())

	to_search = 'http://scholar.google.ch/citations%3Fuser%3D'
	to_crawl  = 'http://scholar.google.ch/citations?user='
	index = google_source.rfind(to_search) + len(to_search)
	ID    = google_source[index:index+12]

	scholar_url = to_crawl + ID
	scholar_req = Request(scholar_url, headers={'User-Agent': 'Mozilla/5.0'})
	scholar_source = str(urlopen(scholar_req).read())

	years     = [line.split('">')[1].split('</')[0] for line in scholar_source.split('gsc_g_t' )[3:]]
	citations = [line.split('">')[1].split('</')[0] for line in scholar_source.split('gsc_g_al')[6:]]
	
	print()
	print(first_name+' '+last_name+':')
	print((years, citations))