import csv
import os
import re
import time as time_module
from collections import namedtuple
from datetime import datetime, time, timedelta
from itertools import groupby
import requests
from bs4 import BeautifulSoup
from colorama import Fore, Back, Style, init

init(autoreset=True)  # setting color to auto-reset
date = datetime.now()  # getting date
# creating dictionary of valid_clubs and ids from valid_clubs txt file
disqualification_reasons = ["WKG", "UPG", "ZP", "HR", "HEIGHT", "ZRVG", "new",
                            "AGE", "DQ", "MAP", "20MINS", "5MINS"]
MIDNIGHT = time()
valid_clubs = {}
# opening txt file
with open("validclubs.txt") as f:
    for line in f:
        # defining dictionary in form key is before first whitespace, value is after whitespace
        clubid, club = line.strip("\n").split(maxsplit=1)
        # defining in dictionary club is the value of the id
        valid_clubs[clubid] = club

# setting headers for request
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36/wziDaIGv-15"}
# url of php script which post request is sent to
url = "http://choddo.co.uk/ReadZP6.php"


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


def remove_values_after_ambiguous_characters(
        text, there=re.compile(re.escape('(' or '[' or '|' or '/' or '{' or 'CCR' or
                                         'RMCC' or 'Penge' or 'SDW' or 'PWCC' or 'EGCC' or 'VCM' or 'MVC' or '[LD' or
                                         '[CChasers') + '.*')):
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
        return points


def write_csv_individual_results(path, values):  # function to write to CSV the second time for full clubs results
    with open(path, 'a', newline='') as csv_file:  # opening CSV file
        fieldnames = ['Position', 'Category', 'Name', 'Club', 'Points', 'Time']  # setting fieldnames
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames,
                                dialect='excel')  # writing to CSV file with fieldnames and so it can be opened in Excel
        writer.writerow(values)  # write input values to csv


def get_names(rider_name):  # Function to get the names of the riders
    riders1 = ' '.join(rider_name.split()[:4])  # remove any values after the 4th word
    riders2 = remove_values_after_ambiguous_characters(riders1)  # removing all values after the ambiguous characters
    riders = riders2.replace(r'[^a-zA-Z0-9]', '')  # replacing all ambiguous values with nothing
    return riders


def get_clubs(team):  # Function to get the clubs of the riders
    club_name = valid_clubs.get(team)  # searches dictionary of valid_clubs for the id and returns the value
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
    for file_to_merge in os.listdir(path):
        csv_in = open(os.path.join(path, file_to_merge))  # opening each file_to_merge individually
        for item in csv_in:  # every item in the files to be merged,
            try:
                csv_merge.write(item)  # will be written to a new csv
            except IndexError:  # unless there is an IndexError i.e. a blank item, where this item will be passed
                pass
        csv_in.close()  # closing the csv to be merged
    csv_merge.close()  # closing the output csv


def csv_to_tuple(path, tuple_to_use):  # function to turn the merged CSVs into namedtuple
    try:
        with open(path, 'r', errors='ignore') as datafile:
            csv_to_tuple_reader = csv.reader(datafile)
            for row in map(tuple_to_use._make, csv_to_tuple_reader):
                if row[1] != "Team":
                    yield row
    except RuntimeError:
        pass


def write_data(data_in, data_out):  # function to write namedtuple to a new CSV
    out = []  # create a list for the the namedtuples

    def return_teams(x):  # function to return the value of the team_id in the group
        return x.Team

    def return_number_of_riders():
        try:
            num_of_riders = sum(int(i.NumOfRiders) for i in group)
        except:
            num_of_riders = len(group)
        return num_of_riders

    for team, group in groupby(data_in,
                               return_teams):  # creating a group of namedtuples where each group is a different team_id
        group = list(group)  # creating a list of clubs, grouped so there is not any repeats
        if team == "Team":
            pass
        else:
            d = {'Team': team, 'Points': sum(float(i.Points) for i in group),
                 'AvgPoints': sum(float(i.Points) for i in group) / return_number_of_riders(),
                 'NumOfRider': return_number_of_riders()}  # defining a dictionary for each team_id where team_id is the value Team,
            # points is the sum of all the points of riders in that group,
            # AvgPoints is the avg value of points and num_of_riders is number of items in the group
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
    "This programme will give you a brief overview of the results but to view the full results "
    "for each category view the relevant output file. \n"
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
            if row[4] in valid_clubs and row[7] == "0":  # if club is in valid_clubs.txt and gender = female
                W = W + 1  # each time this condition is met increase value of W by 1, where W is the amount of women
            if row[4] in valid_clubs and "A" == row[0]:  # if club is in valid_clubs.txt and category is A
                A = A + 1  # each time this condition is met increase value of A by 1
            if row[4] in valid_clubs and "B" == row[0]:  # if club is in valid_clubs.txt and category is B
                B = B + 1  # each time this condition is met increase value of B by 1
            if row[4] in valid_clubs and "C" == row[0]:  # if club is in valid_clubs.txt and category is C
                C = C + 1  # each time this condition is met increase value of C by 1
            if row[4] in valid_clubs and "D" == row[0]:  # if club is in valid_clubs.txt and category is D
                D = D + 1  # each time this condition is met increase value of D by 1
            if row[4] in valid_clubs and row[0] in disqualification_reasons:  # all the possible DQ reason
                Q = Q + 1  # each time this condition is met increase value of Q by 1, where Q is the number of riders DQ'ed
            if row[4] in valid_clubs and "E" == row[0]:  # if club is in valid_clubs.txt and category is E
                E = E + 1  # each time this condition is met increase value of E by 1
        except IndexError:  # ignore errors where row is empty
            pass
        total = str(A + B + C + D + E + Q)
print("There were", total, "riders", W, " were women:", "\nCat A:", A, "\nCat B:", B, "\nCat C:",
      C, "\nCat D:", D, "\nCat E:", E, "\nDisqualified:", Q)

with open("results.csv", 'rt', encoding='UTF-8', errors='ignore') as file:  # opening the full results file
    reader = csv.reader(file, skipinitialspace=True, escapechar='\\')  # skipping headers
    male_category_list = []  # setting category as blank so a change is recognised
    for row in reader:
        if len(row) == 9:  # only finding rows with all these values, some without a team have len == 8, also ignores blank rows
            cat, position, name, time, team_id, avg_power, twenty_min_wkg, male, twenty_min_watts = row
            if time != 'Time':  # ignore first row
                time = datetime.strptime(time, "%H:%M:%S.%f")  # get time as datetime
            if team_id in valid_clubs and male == "1":  # only search CSV for relevant clubs + men
                if cat not in male_category_list:
                    if cat == "A":
                        first_place_time = time  # getting the first place time
                        time_span = first_place_time - datetime.combine(first_place_time, MIDNIGHT)
                        time_difference = time_span.total_seconds() * 1.15  # getting 115% of the first place time
                        max_time = datetime.strptime(convert(time_difference), "%H:%M:%S")  # converting 115% to a datetime object
                    bcse_position = 1  # reset the rider's finish position to 1
                    male_category_list.append(cat)  # add cat to cat list
                else:  # if category does not change increase BCSE position by 1
                    bcse_position = bcse_position + 1
                club = get_clubs(team_id)  # using get_clubs function to return clubs value
                name = get_names(name)  # using get_names function to return names which have been cleaned up
                points = points_calculator(cat, bcse_position)  # calculate rider points for that cat & position, including DQs
                if position == "0":  # set the position to be written to CSV, which needs to be different if the rider was DQed (position ==0)
                    position_for_file = "DQ"  # if rider was DQ'ed position in file will be DQ instead of zero
                    points = 0  # and they will receive 0 points
                elif position != 0:  # if they received a finish position i.e. they were not DQed,
                    position_for_file = bcse_position  # position in file will be the value of the variable bcse_position
                try:
                    if cat == "A" and time > max_time:
                        points = 0  # anyone over the 115% time gets 0 points
                        position_for_file = "DQ Time-Cut"
                        cat = "Time Cut"
                except ValueError:
                    pass
                data = {'Position': position_for_file, 'Category': cat, 'Name': name, 'Club': club,
                        'Points': points, 'Time': time.strftime("%H:%M:%S.%f")}  # dictionary of data to write to CSV
                # set rider_name of file + opening & writing to output CSV
                write_csv_individual_results(
                    ('Male/Individual Results/Male output' + cat + ' ' + date.strftime("%Y, %B, %d") + '.csv'),
                    values=data)

with open("results.csv", 'rt', encoding='UTF-8', errors='ignore') as file:  # repeat the above section of code for women
    reader = csv.reader(file, skipinitialspace=True, escapechar='\\')
    female_category_list = []  # as women_category rather than cat, so it resets completely
    for row in reader:
        if len(row) == 9:
            cat, position, name, time, team_id, avg_power, twenty_min_wkg, male, twenty_min_watts = row
            if time != 'Time':
                time = datetime.strptime(time, "%H:%M:%S.%f")
            try:
                if team_id in valid_clubs and male == "0":  # only search CSV for relevant clubs + women
                    if cat not in female_category_list:  # Each time there's a change of category,
                        bcse_women_position = 1  # reset the rider's finish position to 1
                        female_category_list.append(cat)
                    else:
                        bcse_women_position = bcse_women_position + 1
                    position = row[1]  # Second index in row contains position number
                    women_category = row[0]
                    club = get_clubs(team_id)  # using get_clubs function to return clubs value
                    name = get_names(name)  # using get_names function to return names which have been cleaned up
                    points = points_calculator(cat, bcse_women_position)  # calculate rider points for that cat & position, including DQs
                    if position == "0":  # Set the position to be written to CSV, which needs to be different if the rider was DQed (position ==0)
                        position_for_file = "DQ"
                        points = int(0)
                    elif position != 0:
                        position_for_file = bcse_women_position
                    # dictionary of data to write to CSV
                    data = {'Position': position_for_file, 'Category': women_category, 'Name': name, 'Club': club, 'Points': points, 'Time': time.strftime("%H:%M:%S.%f")}
                    # set rider_name of file + opening & writing to output CSV
                    write_csv_individual_results(
                        ('Female/Individual Results/Female output' + women_category + ' ' + date.strftime("%Y, %B, %d") + '.csv'),
                        values=data)
            except IndexError:
                pass

merge_csv(r"Female\\Individual Results\\", "Female")
merge_csv(r"Male\\Individual Results\\", "Male")

fields = ("Position", "Category", "Name", "Team", "Points", "Time")  # setting the fields for the namedtuple
# creating new namedtuple which will contain the results of all categories, one for men, one for women
final_individual_results_namedtuple = namedtuple('final_individual_results_namedtuple', fields)

try:
    tuple_men_full_results = sorted(
        csv_to_tuple("Male/Individual Results/Full Male Results" + date.strftime("%Y, %B, %d") + ".csv",
                     final_individual_results_namedtuple),
        key=lambda k: k.Team)  # sorting namedtuple into a grouped list
except RuntimeError:  # unless the row is blank, when it will be passed
    pass
try:
    tuple_women_full_results = sorted(
        csv_to_tuple("Female/Individual Results/Full Female Results" + date.strftime("%Y, %B, %d") + ".csv",
                     final_individual_results_namedtuple),
        key=lambda k: k.Team)  # sorting namedtuple into a grouped list
except RuntimeError:  # unless the row is blank, when it will be passed
    pass

if A + B + C + D > 0:
    write_data(tuple_men_full_results,
               "Club Results/Men's Club Results" + date.strftime("%Y, %B, %d") + ".csv")  # write the men's data to csv
else:  # unless there is an NameError i.e. the variable doesn't exist - this happens if there are no values because is it a gender specific race
    pass
if W > 0:
    write_data(tuple_women_full_results, "Club Results/Women's Club Results" + date.strftime(
        "%Y, %B, %d") + ".csv")  # write the women's data to csv
else:
    pass

merge_csv('Club Results/', 'unsorted club')

fields_clubs = ("Team", "Points", "AvgPoints", "NumOfRiders")  # setting the fields for the namedtuple
# creating new namedtuple which will contain the results of all categories, one for men, one for women
final_club_results_namedtuple = namedtuple('final_club_results_namedtuple', fields_clubs)

tuple_club_full_results = sorted(
    csv_to_tuple("Club Results/Full unsorted club Results" + date.strftime("%Y, %B, %d") + '.csv', final_club_results_namedtuple),
    key=lambda k: k.Team)  # sorting namedtuple into a grouped list

write_data(tuple_club_full_results, "Full Club Results" + date.strftime("%Y, %B, %d") + '.csv')
print(datetime.now(),
      Fore.GREEN + "Process Complete, check your folder for the results")  # print that the process is complete
os.remove('results.csv')
os.remove("Club Results/Full unsorted club Results" + date.strftime("%Y, %B, %d") + '.csv')

print("Execution time =", datetime.now() - date)
print("Closing in 5 seconds")
time_module.sleep(1)
print("Closing in 4 seconds")
time_module.sleep(1)
print("Closing in 3 seconds")
time_module.sleep(1)
print("Closing in 2 seconds")
time_module.sleep(1)
print("Closing in 1 seconds")
time_module.sleep(1)
time_module.sleep(int(3600))  # sleep to stop terminal closing automatically so overview can be seen
