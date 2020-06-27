import csv, os, re, requests, time as timeModule
from collections import namedtuple
from datetime import datetime, timedelta
from itertools import groupby
from bs4 import BeautifulSoup
from colorama import Fore, Back, Style, init

# setting color to auto-reset
init(autoreset=True)
date = datetime.now()  # getting date
# creating dictionary of validClubs and ids from validClubs txt file
disqualification_reasons = ["WKG", "UPG", "ZP", "HR", "HEIGHT", "ZRVG", "new", "AGE", "DQ", "MAP", "20MINS", "5MINS"]
validClubs = {}
# opening txt file
with open("validclubs.txt") as f:
    for line in f:
        # defining dictionary in form key is before first whitespace, value is after whitespace
        clubid, club = line.strip("\n").split(maxsplit=1)
        # defining in dictionary club is the value of the id
        validClubs[clubid] = club

# setting headers for request
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36/wziDaIGv-15"}
# url of php script which post request is sent to
url = "http://choddo.co.uk/ReadZP5.php"

# startup screen
string_startup = "'ZwiftPower Results Scraper' by George Pittock"
print(
    '\n''\n''\n' + "                                        ", Fore.RED + Style.BRIGHT +
    string_startup.center(50) + Back.RESET + Style.RESET_ALL + '\n''\n''\n''\n')


# csv writer function
def write_csv(path, inputdata):
    with open(path, 'w', errors='ignore', newline='') as newfile:
        writer = csv.writer(newfile, dialect='excel')
        writer.writerows(inputdata)


def remove_values_after_ambiguous_characters(text,
                                             there=re.compile(re.escape('(' or '[' or '|' or '/' or '{' or 'CCR' or
                                                                        'RMCC' or 'Penge' or 'SDW' or 'PWCC' or 'EGCC' or
                                                                        'VCM' or 'MVC' or '[LD' or '[CChasers') + '.*')):
    return there.sub('', text)  # function to remove any text after ambiguous characters


def points_calculator(category, regional_position):  # Function to calculate  points based on input A,B,C,D or E
    global points
    if regional_position == 0:  # if rider was DQ'ed
        return points == 0  # they receive no points
    else:
        points = 1  # points = 1 for all riders who were not in certain positions
        if category in ["A", "E"]:
            if regional_position < 12:  # in cat A and E, all riders in the top 11 receive a value of points of 100, decreasing by 5 for each position
                points = 105 - 5 * (int(regional_position))
            elif regional_position < 61:  # all other riders in the top 60 receive a value of points of 61 - their position
                points = 61 - regional_position
        elif category == "B":  # in cat B, all riders in the top 6 receive a value of points of 75, decreasing by 5 for each position
            if regional_position < 7:
                points = 80 - 5 * (int(regional_position))
            elif regional_position < 56 and (
                    row[7] == "0" or B < 56):  # all other riders in the top 55 receive a value of 55 - their position
                points = 56 - regional_position
            else:
                points = round(98 - ((2 * regional_position - 14) * (96 / (2 * B - 14)))) / 2
        elif category == "C":  # in cat C all riders in the top 50 receive a value of points 51 - their position
            if regional_position < 51:
                points = 51 - regional_position
        elif category == "D":  # in cat D all riders receive a value of points of 31 - their position
            if regional_position < 31:
                points = 31 - regional_position
        elif category == "B+":
            points = 1000
        return points


def write_csv_individual_results(path, values):  # function to write to CSV the second time for full clubs results
    with open(path, 'a', newline='') as csv_file:  # opening CSV file
        fieldnames = ['Position', 'Category', 'Name', 'Club', 'Points', 'Time']  # setting fieldnames
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames,
                                dialect='excel')  # writing to CSV file with fieldnames and so it can be opened in Excel
        writer.writerow(values)  # write input values to csv


def get_names():  # Function to get the names of the riders
    names = row[2]  # name = row[2] in file
    riders1 = ' '.join(names.split()[:4])  # remove any values after the 4th word
    riders2 = remove_values_after_ambiguous_characters(riders1)  # removing all values after the ambiguous characters
    riders = riders2.replace(r'[^a-zA-Z0-9]', '')  # replacing all ambiguous values with nothing
    return riders


def get_clubs():  # Function to get the clubs of the riders
    club_name = validClubs.get(row[4])  # searches dictionary of validClubs for the id and returns the value
    return club_name


def convert(seconds):  # function to convert amount of seconds to a time format
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%d:%02d:%02d" % (hour, minutes, seconds)


def merge_csv(path, gender):  # function to merge csvs into one csv
    csv_out = path + "Full " + gender + " Results" + date.strftime(
        "%Y, %B, %d") + '.csv'  # defining the csv of all the merged files
    csv_merge = open(csv_out, 'w')  # opening the final csv
    for fileToMerge in os.listdir(path):
        csv_in = open(os.path.join(path, fileToMerge))  # opening each fileToMerge individually
        for item in csv_in:  # every item in the files to be merged,
            try:
                csv_merge.write(item)  # will be written to a new csv
            except IndexError:  # unless there is an IndexError i.e. a blank item, where this item will be passed
                pass
        csv_in.close()  # closing the csv to be merged
    csv_merge.close()  # closing the output csv


def csv_to_tuple(path, tupleToUse):  # function to turn the merged CSVs into namedtuple
    try:
        with open(path, 'r', errors='ignore') as datafile:
            csv_to_tuple_reader = csv.reader(datafile)
            for row in map(tupleToUse._make, csv_to_tuple_reader):
                if row[1] != "Team":
                    yield row
    except RuntimeError:
        pass


def write_data(data_in, data_out):  # function to write namedtuple to a new CSV
    out = []  # create a list for the the namedtuples

    def return_teams(x):  # function to return the value of the team in the group
        return x.Team

    def return_number_of_riders():
        try:
            NumOfRiders = sum(int(i.NumOfRiders) for i in group)
        except:
            NumOfRiders = len(group)
        return NumOfRiders

    for team, group in groupby(data_in,
                               return_teams):  # creating a group of namedtuples where each group is a different team
        group = list(group)  # creating a list of clubs, grouped so there is not any repeats
        if team == "Team":
            pass
        else:
            d = {'Team': team, 'Points': sum(float(i.Points) for i in group),
                 'AvgPoints': sum(float(i.Points) for i in group) / return_number_of_riders(),
                 'NumOfRider': return_number_of_riders()}  # defining a dictionary for each team where team is the value Team,
            # points is the sum of all the points of riders in that group,
            # AvgPoints is the avg value of points and NumOfRiders is number of items in the group
            out.append(d)  # adding the above dictionary to the list out
            with open(data_out, 'w', newline='') as csv_file:  # writing data to a new csv
                fieldnames = ['Team', 'Points', 'AvgPoints', 'NumOfRider']  # setting row headers of output csv
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writeheader()
                for row in out:  # for every value in the list out a new row in the csv will be written
                    writer.writerow(row)


# open the csv where the merged files will go
with open("Male/Individual Results/Full Male Results" + date.strftime("%Y, %B, %d") + '.csv', 'wb') as file:
    file.close()
with open("Female/Individual Results/Full Female Results" + date.strftime("%Y, %B, %d") + '.csv', 'wb') as file:
    file.close()
with open("Club Results/Full Club Results(not sorted)" + date.strftime("%Y, %B, %d") + '.csv', 'wb') as file:
    file.close()

# getting data race id
race_id = input(
    "This programme will give you a brief overview of the results but to view the full results for each category view the relevant output file. \n"
    "Please enter the race ID and press enter:"
    "\n")
date = datetime.now()
print(date, "Started")

# removing all files
try:
    os.remove("results.csv")
except:
    pass

for file_name_male in os.listdir(path='Male/Individual Results'):
    os.remove('Male/Individual Results/' + file_name_male)

for file_name_female in os.listdir(path='Female/Individual Results'):
    os.remove('Female/Individual Results/' + file_name_female)

for file_name_clubs in os.listdir(path='Club Results'):
    os.remove('Club Results/' + file_name_clubs)

# sending request to get html
with requests.Session() as s:
    # post request form data
    data = {'raceID': race_id,
            'csv': 'CSV',
            'submit': 'Submit Request'}
    response = s.post(headers=headers, data=data, url=url)  # getting html content
    html_string = str(response.content)  # using beautiful soup to parse html
    soup = BeautifulSoup(html_string, features="html.parser")
    # getting new lines in HTML - all rows of CSV are in a br tag, so finding all these values
    for br in soup.find_all('br'):
        br.replace_with('\n')  # separating each br value with a new line
    rows = [[i.replace('"', '').strip()  # clean the lines
             for i in item.split(',')]  # split each item by a comma
            # get the first item matching the filter
            for item in soup.text.splitlines()]
    # remove empty rows and defining rows
    rows = [[item for item in row if item]
            for row in rows]
    # write to results.csv - all results not just BCSE riders
    write_csv('results.csv', rows)

with open("results.csv", 'rt', encoding='UTF-8',
          errors='ignore') as file:  # open results file to get breakdown of results
    reader = csv.reader(file, skipinitialspace=True, escapechar='\\')
    # each variable is current number of riders in the category
    A = B = C = D = E = Q = W = 0  # setting all values to 0 so we can work out number of riders in each category
    for row in reader:
        try:
            if row[4] in validClubs and row[7] == "0":  # if club is in validClubs.txt and gender = female
                W = W + 1  # each time this condition is met increase value of W by 1, where W is the amount of women
            if row[4] in validClubs and "A" == row[0]:  # if club is in validClubs.txt and category is A
                A = A + 1  # each time this condition is met increase value of A by 1
            if row[4] in validClubs and "B" == row[0]:  # if club is in validClubs.txt and category is B
                B = B + 1  # each time this condition is met increase value of B by 1
            if row[4] in validClubs and "C" == row[0]:  # if club is in validClubs.txt and category is C
                C = C + 1  # each time this condition is met increase value of C by 1
            if row[4] in validClubs and "D" == row[0]:  # if club is in validClubs.txt and category is D
                D = D + 1  # each time this condition is met increase value of D by 1
            if row[4] in validClubs and row[0] in disqualification_reasons:  # all the possible DQ reason
                Q = Q + 1  # each time this condition is met increase value of Q by 1, where Q is the number of riders DQ'ed
            if row[4] in validClubs and "E" == row[0]:  # if club is in validClubs.txt and category is E
                E = E + 1  # each time this condition is met increase value of E by 1
        except IndexError:  # ignore errors where row is empty
            pass
        total = str(A + B + C + D + E + Q)
print("There were", total, "riders", W, " were women:", "\nCat A:", A, "\nCat B:", B, "\nCat C:",
      C, "\nCat D:", D, "\nCat E:", E, "\nDisqualified:", Q)

with open("results.csv", 'rt', encoding='UTF-8', errors='ignore') as file:  # opening the full results file
    reader = csv.reader(file, skipinitialspace=True, escapechar='\\')  # skipping headers
    MaleCategoryList = []  # setting category as blank so a change is recognised
    for row in reader:
        try:
            if row[4] in validClubs and row[7] == "1":  # only search CSV for relevant clubs + men
                if row[0] not in MaleCategoryList:
                    if row[0] == "A":
                        firstPlaceTime = datetime.strptime(row[3], "%H:%M:%S.%f")
                        timeInSecs = firstPlaceTime.second + firstPlaceTime.minute * 60 + firstPlaceTime.hour * 3600
                        timeDifference = timeInSecs * 1.15
                        MaxTime = datetime.strptime(convert(timeDifference), "%H:%M:%S")
                    bcse_position = 1  # reset the rider's finish position to 1
                    MaleCategoryList.append(row[0])
                else:  # if category does not change increase BCSE position by 1
                    bcse_position = bcse_position + 1
                position = row[1]  # second index in row contains position number
                cat = row[0]
                time = row[3]
                club = get_clubs()  # using get_clubs function to return clubs value
                name = get_names()  # using get_names function to return names which have been cleaned up
                points = points_calculator(cat,
                                           bcse_position)  # calculate rider points for that cat & position, including DQs
                if position == "0":  # set the position to be written to CSV, which needs to be different if the rider was DQed (position ==0)
                    position_for_file = "DQ"  # if rider was DQ'ed position in file will be DQ instead of zero
                    points = int(0)  # and they will receive 0 points
                elif position != 0:  # if they received a finish position i.e. they were not DQed,
                    position_for_file = bcse_position  # position in file will be the value of the variable bcse_position
                if cat == "A" and datetime.strptime(row[3], "%H:%M:%S.%f") > MaxTime:
                    points = int(0)
                    position_for_file = "DQ Time-Cut"
                    cat = "Time Cut"
                data = {'Position': position_for_file, 'Category': cat, 'Name': name, 'Club': club,
                        'Points': points, 'Time': time}  # dictionary of data to write to CSV
                # set name of file + opening & writing to output CSV
                write_csv_individual_results(
                    ('Male/Individual Results/Male output' + cat + ' ' + date.strftime("%Y, %B, %d") + '.csv'),
                    values=data)
        except IndexError:  # ignore blank rows etc.
            pass

with open("results.csv", 'rt', encoding='UTF-8', errors='ignore') as file:  # repeat the above section of code for women
    reader = csv.reader(file, skipinitialspace=True, escapechar='\\')
    FemaleCategoryList = []  # as women_category rather than cat, so it resets completely
    for row in reader:
        try:
            if row[4] in validClubs and row[7] == "0":  # only search CSV for relevant clubs
                if row[0] not in FemaleCategoryList:  # Each time there's a change of category,
                    BCSE_Women_Position = 1  # reset the rider's finish position to 1
                    FemaleCategoryList.append(row[0])
                else:
                    BCSE_Women_Position = BCSE_Women_Position + 1
                position = row[1]  # Second index in row contains position number
                women_category = row[0]
                club = get_clubs()
                name = get_names()
                points = points_calculator(women_category,
                                           BCSE_Women_Position)  # calculate rider points for that cat & position, including DQs
                if position == "0":  # Set the position to be written to CSV, which needs to be different if the rider was DQed (position ==0)
                    position_for_file = "DQ"
                    points = int(0)
                elif position != 0:
                    position_for_file = BCSE_Women_Position
                # dictionary of data to write to CSV
                data = {'Position': position_for_file, 'Category': women_category, 'Name': name, 'Club': club,
                        'Points': points}
                # set name of file + opening & writing to output CSV
                write_csv_individual_results(
                    ('Female/Individual Results/Female output' + women_category + ' ' + date.strftime(
                        "%Y, %B, %d") + '.csv'),
                    values=data)
        except IndexError:
            pass

merge_csv(r"Female\\Individual Results\\", "Female")
merge_csv(r"Male\\Individual Results\\", "Male")

fields = ("Position", "Category", "Name", "Team", "Points", "Time")  # setting the fields for the namedtuple
# creating new namedtuple which will contain the results of all categories, one for men, one for women
FinalIndividualResults = namedtuple('FinalIndividualResults', fields)

try:
    MenFinalOutput = sorted(
        csv_to_tuple("Male/Individual Results/Full Male Results" + date.strftime("%Y, %B, %d") + ".csv",
                     FinalIndividualResults),
        key=lambda k: k.Team)  # sorting namedtuple into a grouped list
except RuntimeError:  # unless the row is blank, when it will be passed
    pass
try:
    WomenFinalOutput = sorted(
        csv_to_tuple("Female/Individual Results/Full Female Results" + date.strftime("%Y, %B, %d") + ".csv",
                     FinalIndividualResults),
        key=lambda k: k.Team)  # sorting namedtuple into a grouped list
except RuntimeError:  # unless the row is blank, when it will be passed
    pass

if A+B+C+D > 0:
    write_data(MenFinalOutput,
               "Club Results/Men's Club Results" + date.strftime("%Y, %B, %d") + ".csv")  # write the men's data to csv
else:  # unless there is an NameError i.e. the variable doesn't exist - this happens if there are no values because is it a gender specific race
    pass
if W > 0:
    write_data(WomenFinalOutput, "Club Results/Women's Club Results" + date.strftime(
        "%Y, %B, %d") + ".csv")  # write the women's data to csv
else:
    pass

merge_csv('Club Results/', 'unsorted club')

fields_clubs = ("Team", "Points", "AvgPoints", "NumOfRiders")  # setting the fields for the namedtuple
# creating new namedtuple which will contain the results of all categories, one for men, one for women
FinalClubResults = namedtuple('FinalClubResults', fields_clubs)

ClubFinalOutput = sorted(
    csv_to_tuple("Club Results/Full unsorted club Results" + date.strftime("%Y, %B, %d") + '.csv', FinalClubResults),
    key=lambda k: k.Team)  # sorting namedtuple into a grouped list

write_data(ClubFinalOutput, "Full Club Results" + date.strftime("%Y, %B, %d") + '.csv')
print(datetime.now(),
      Fore.GREEN + "Process Complete, check your folder for the results")  # print that the process is complete
os.remove('results.csv')
os.remove("Club Results/Full unsorted club Results" + date.strftime("%Y, %B, %d") + '.csv')

print("Execution time =", datetime.now() - date)

timeModule.sleep(int(3600))  # sleep to stop terminal closing automatically so overview can be seen
