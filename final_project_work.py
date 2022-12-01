import requests
import json
import csv
import hashlib
import plotly.graph_objects as go
from fuzzywuzzy import fuzz

# For security reasons, I'm not pushing my API keys to Github at the moment.
# GOOGLE_API_KEY = [API KEY HELD ELSEWHERE]
# OPEN_SECRETS_API_KEY = [API KEY HELD ELSEWHERE]

class RepTree:

    def __init__(self, local, state, federal):

        self.federal = federal
        self.state = state
        self.local = local

    def json_version(self):
        return {"federal" : [rep.json_version() for rep in self.federal.reps], "state" : [rep.json_version() for rep in self.state.reps], "local" : [rep.json_version() for rep in self.local.reps]}


class GovLevel:

    def __init__(self, level, reps):

        self.level = level
        self.reps = reps


class Representative:

    def __init__(self, rep_dict, role, level):

        level_dict = {
        "country" : "Federal",
        "administrativeArea1" : "State",
        "administrativeArea2" : "Local",
        "regional" : "Local"}

        self.rep_dict = rep_dict

        try:
            self.name = rep_dict["name"]
        except:
            self.name = None
        try:
            self.party = rep_dict["party"]
        except:
            self.party = None
        try:
            self.role = role
        except:
            self.role = None
        if level in level_dict.keys():
            self.level = level_dict[level]

        try:
            self.address = " ".join([val for val in rep_dict["address"][0].values()])
        except:
            self.address = "No address available"

        try:
            self.phone = rep_dict["phones"][0]
        except:
            self.phone = None

        try:
            self.website = rep_dict["urls"][0]
        except:
            self.website = None

        self.financial_info = None
        self.os_id = None
    
    def short_info(self):
        return(f"{self.name} - {self.role} - {self.party}")
    
    def full_info(self):
        return(f'''
        ————————————————————
        ———Information on———
           {self.name}
        ————————————————————
        -Position: {self.role}
        -Party: {self.party}
        -Level: {self.level}
        -Address: {self.address}
        -Phone Number: {self.phone}
        -Website: {self.website}
        ————————————————————
        ''')

    def json_version(self):
        return self.__dict__


class CongressPerson(Representative):

    def __init__(self, rep_dict, role, level, os_id, contributors=None, industries=None):
        super().__init__(rep_dict, role, level)

        self.level = "Federal"
        self.os_id = os_id
        self.contributors = None
        self.contributor_notice = "The organizations themselves did not donate, rather the money came from the organization's PAC, its individual members or employees or owners, and those individuals' immediate families"
        self.industries = None

    def short_info(self):
        return(f"{self.name} - {self.role} - {self.party}")
    
    def full_info(self):
        return(f'''
        ————————————————————
        ———Information on———
           {self.name}
        ————————————————————
        -Position: {self.role}
        -Party: {self.party}
        -Level: {self.level}
        -Address: {self.address}
        -Phone Number: {self.phone}
        -Website: {self.website}
        -Top Donors : {'Available' if self.contributors else "Not Available"}
        -Top Contributing Industries : {'Available' if self.industries else "Not Available"}
        ————————————————————
        ''')

    def get_top_contributors(self, cache=None):

        if cache:
            if check_cache(self.os_id, cache=cache):
                self.contributors = cache[self.os_id]
            else:
                root = "https://www.opensecrets.org/api/?method=candContrib"
                params = {"output" : "json", "cid" : self.os_id, "apikey" : OPEN_SECRETS_API_KEY}
                contributors = requests.get(root, params=params).json()

                self.contributors = [x for x in contributors["response"]["contributors"]["contributor"]]
                contributor_list_a = []
                for x in self.contributors:
                    contributor_list_a.append(list(x["@attributes"].values())[0:])

                self.contributors = contributor_list_a

                cache[self.os_id] = self.contributors

                with open("contributor_cache.json", 'w', encoding='utf-8') as file_obj:
                    json.dump(cache, file_obj, ensure_ascii=False, indent=2)
                    print("wrote cache")
        else:
            root = "https://www.opensecrets.org/api/?method=candContrib"
            params = {"output" : "json", "cid" : self.os_id, "apikey" : OPEN_SECRETS_API_KEY}
            contributors = requests.get(root, params=params).json()

            self.contributors = [x for x in contributors["response"]["contributors"]["contributor"]]
            contributor_list_b = []
            for x in self.contributors:
                contributor_list_b.append(list(x["@attributes"].values())[0:])

            self.contributors = contributor_list_b

            cache = {}
            cache[self.os_id] = self.contributors

            with open("contributor_cache.json", 'w', encoding='utf-8') as file_obj:
                json.dump(cache, file_obj, ensure_ascii=False, indent=2)
                print("wrote cache")
    
    def json_version(self):
        return self.__dict__
        #return {"name": self.name, "party" : self.party, "role" : self.role, "contributors" : self.contributors, "industries" : self.industries}



    def get_top_industries(self, cache=None):

        if cache:
            if check_cache(self.os_id, cache=cache):
                self.industries = cache[self.os_id]
            else:

                root = "https://www.opensecrets.org/api/?method=candIndustry"
                params = {"output" : "json", "cid" : self.os_id, "apikey" : OPEN_SECRETS_API_KEY}
                try:
                    industries = requests.get(root, params=params).json()
                except:
                    print("using except verion")
                    params["cycle"] = "2020"
                    industries = requests.get(root, params=params).json()

                self.industries = [x for x in industries["response"]["industries"]["industry"]]
                industries_list_a = []
                for x in self.industries:
                   industries_list_a.append(list(x["@attributes"].values())[1:])

                self.industries = industries_list_a

                cache[self.os_id] = self.industries

                with open("industry_cache.json", 'w', encoding='utf-8') as file_obj:
                    json.dump(cache, file_obj, ensure_ascii=False, indent=2)
                    print("wrote cache")
        else:
            root = "https://www.opensecrets.org/api/?method=candIndustry"
            params = {"output" : "json", "cid" : self.os_id, "apikey" : OPEN_SECRETS_API_KEY}
            industries = requests.get(root, params=params).json()

            self.industries = [x for x in industries["response"]["industries"]["industry"]]
            industries_list_b = []
            for x in self.industries:
                industries_list_b.append(list(x["@attributes"].values())[1:])

            self.industries = industries_list_b

            cache = {}
            cache[self.os_id] = self.industries

            with open("industry_cache.json", 'w', encoding='utf-8') as file_obj:
                json.dump(cache, file_obj, ensure_ascii=False, indent=2)
                print("wrote cache")
            
        print(self.industries)

    def plot_contributors(self):
        if self.contributors:
            x = [contributor[0] for contributor in self.contributors]

            fig = go.Figure(go.Bar(x=x, y=[int(contributor[2]) for contributor in self.contributors], name='PAC Contributions'))
            fig.add_trace(go.Bar(x=x, y=[int(contributor[3]) for contributor in self.contributors], name='Individual Contributions'))
            fig.update_layout(barmode='stack')
            fig.update_layout(
                title=f"Top Campaign Contributors for {self.name}, {self.role} in the most recent election cycle.",
                xaxis_title="Top Campaign Contributors",
                yaxis_title="USD($) Contributed",
                legend_title="Kind of Donations")
            fig.show()
        else:
            print("No Contributor Information Available")
    
    def plot_industries(self):
        if self.industries:
            x = [industry[0] for industry in self.industries]

            fig = go.Figure(go.Bar(x=x, y=[int(industry[2]) for industry in self.industries], name='PAC Contributions'))
            fig.add_trace(go.Bar(x=x, y=[int(industry[1]) for industry in self.industries], name='Individual Contributions'))
            fig.update_layout(barmode='stack')
            fig.update_layout(
                title=f"Top Contributing Industries for {self.name}, {self.role} in the most recent election cycle.",
                xaxis_title="Top Contributing Industry",
                yaxis_title="USD($) Contributed",
                legend_title="Kind of Donations")
            fig.show()
        else:
            print("No Industry Contribution Information Available")


def get_rep_info(address):
    root_url = "https://civicinfo.googleapis.com/civicinfo/v2/representatives"
    params = {"key" : GOOGLE_API_KEY, "address" : address}

    data = None
    try:
        response = requests.get(root_url, params=params)
        if response.status_code == 200:
            print("got data")
            print(response.url)
            data = response.json()
    except:
        print("api issue happened")

    return data


def construct_Reps(data):
    if data:
        office_indices ={}
        for role in data["offices"]:
            office_indices[role["name"]] = [role["officialIndices"], role["levels"][0]]
    print(office_indices)

    officials = []
    for key,val in office_indices.items():
        for person_index in val[0]:
            officials.append(Representative(data["officials"][person_index], key, val[1]))

    return officials


def sort_reps(reps):
    federal_reps = [rep for rep in reps if rep.level == "Federal"]
    state_reps = [rep for rep in reps if rep.level == "State"]
    local_reps = [rep for rep in reps if rep.level == "Local"]
    return {"federal" : federal_reps, "state": state_reps, "local" : local_reps}


def make_congressperson(rep, congress_ids):
    print("making congress persons")
    for person in congress_ids[1:]:
        #print(person[1].split(" ")[1] + person[1].split(" ")[0].strip(","))
        if rep.name == person[1].split(" ")[1] + " " + person[1].split(" ")[0].strip(","):
            print("found match")
            return CongressPerson(rep.rep_dict, rep.role, rep.level, person[0])
        elif rep.name.split(" ")[-1] == person[1].split(" ")[0].strip(",") and rep.party[1] == person[2]:
            return CongressPerson(rep.rep_dict, rep.role, rep.level, person[0])
    print("going second round")
    for person in congress_ids[1:]:
        if rep.name.split(" ")[-1] == person[1].split(",")[0]:
            if fuzz.ratio(rep.name, person[1].split(",")[1].strip(" ") + " " + person[1].split(",")[0].strip(",").strip(" ")) > 70:
                print("Fuzz Find")
                return CongressPerson(rep.rep_dict, rep.role, rep.level, person[0])
    print("could not find")
    return rep


def check_cache(input, cache=None):
    if cache:
        if input in cache.keys():
            if cache[input] is not None:
                print("FOUND IN CACHE")
                return cache[input]
    else:
        print("NOT FOUND IN CACHE")
        return None

#Interaction

def main():

    #loading caches
    with open("os_congress.csv", 'r', encoding="utf-8", newline='') as file_obj:
            congress_ids = []
            reader = csv.reader(file_obj, delimiter=",")
            for row in reader:
                congress_ids.append(row)

    cache = None
    try:
        with open("final_cache.json", 'r', encoding="utf-8") as file_obj:
            cache = json.load(file_obj)
        print("loaded cache")
    except:
        print("could not load cache")

    contributor_cache = None
    try:
        with open("contributor_cache.json", 'r', encoding="utf-8") as file_obj:
            contributor_cache = json.load(file_obj)
        print("loaded cache")
    except:
        print("could not load cache")

    industry_cache = None
    try:
        with open("industry_cache.json", 'r', encoding="utf-8") as file_obj:
            industry_cache = json.load(file_obj)
        print("loaded cache")
    except:
        print("could not load cache")


    address = input("please submit an address: ")
    address_code = hashlib.md5(address.encode()).hexdigest()

    if check_cache(address_code, cache=cache):
        rep_data = check_cache(address_code, cache=cache)
    else:
        rep_data = get_rep_info(address)

        if cache and check_cache(address_code, cache=cache) is None:
            cache[address_code] = {key : val for key, val in rep_data.items() if key != "normalizedInput"}

            with open("final_cache.json", 'w', encoding='utf-8') as file_obj:
                json.dump(cache, file_obj, ensure_ascii=False, indent=2)
                print("wrote cache")

        elif cache is None:
            cache = {}
            cache[address_code] = {key : val for key, val in rep_data.items() if key != "normalizedInput"}

            with open("final_cache.json", 'w', encoding='utf-8') as file_obj:
                json.dump(cache, file_obj, ensure_ascii=False, indent=2)
                print("wrote cache")

    officials = construct_Reps(rep_data)

    sorted_officials = sort_reps(construct_Reps(rep_data))

    new_feds = []
    for rep in sorted_officials["federal"]:
        if "President" not in rep.role:
            print(rep.name)
            new_feds.append(make_congressperson(rep, congress_ids))
        else:
            new_feds.append(rep)

    for fed in new_feds:
        print(type(fed))

    sorted_officials["federal"] = new_feds

    sorted_officials = [val for val in sorted_officials.values()]
    for fed in sorted_officials[0]:
        if fed.os_id:
            fed.get_top_contributors(cache=contributor_cache)
            fed.get_top_industries(cache=industry_cache)

    #building class tree
    federal = GovLevel(level="Federal", reps=sorted_officials[0])
    state = GovLevel(level="State", reps=sorted_officials[1])
    local = GovLevel(level="Local", reps=sorted_officials[2])

    #building top-level
    tree = RepTree(local=local, state=state, federal=federal)
    print("tree successfully contructed")

    with open("RepTree.json", 'w', encoding='utf-8') as file_obj:
        json.dump(tree.json_version(), file_obj, ensure_ascii=False, indent=2)


    for rep in tree.federal.reps:
        print(rep.full_info())

if __name__ == "__main__":
    main()