###################################################################################
#### This is a crawler which get ranking data of 2,000 users and make .txt file ###
###################################################################################

from application import get_soup_from_url

user_url_st = set()

with open('ranking.txt', 'a') as f:
    for i in range(1, 21):
        url = "https://www.acmicpc.net/ranklist/" + str(i)
        soup = get_soup_from_url(url)
        table = soup.find(id="ranklist")
        trs = table.tbody.find_all('tr')
        for tr in trs:
            tds = tr.find_all('td')
            rating = tds[1].a.span['class'][0]

            ## Check if user has codeforce rating
            if len(rating) > 0:
                num_solved = tds[3].a.string.strip()
                print(num_solved)
                ## Get codeforce profile url
                if (rating == 'user-legendary'):
                    user_id = tds[1].a.span.find(text=True, recursive=True) + tds[1].a.span.find(text=True,
                                                                                                 recursive=False)
                else:
                    user_id = tds[1].a.span.string
                user_url = "https://www.acmicpc.net/user/" + user_id
                if user_url in user_url_st:
                    print("got some second id!!! " + user_url)
                    continue

                user_url_st.add(user_url)
                user_soup = get_soup_from_url(user_url)

                codeforce_th = user_soup.find('th', text='Codeforces')
                if codeforce_th:
                    codeforce_url = codeforce_th.findNext('td').a['href']
                    print(codeforce_url)
                else:
                    continue

                # Get accurate codeforce rating
                codeforce_soup = get_soup_from_url(codeforce_url)
                try:
                    acc_rating = codeforce_soup.find_all("span", class_="smaller")[0].find_all("span")[1].string
                except:
                    continue
                print(acc_rating)

                f.write(num_solved + ' ' + acc_rating + '\n')

        print("page " + str(i) + " done.")
