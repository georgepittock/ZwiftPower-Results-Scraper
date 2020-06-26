import csv
import re
import requests
import time
import os
import datetime
from collections import namedtuple
from itertools import groupby
from statistics import mean
from bs4 import BeautifulSoup
from colorama import Fore, Back, Style, init

# startup screen
string_startup = "'ZwiftPower Results Scraper' by George Pittock"
print(
    '\n''\n''\n' + "                                        ", Fore.RED + Style.BRIGHT +
    string_startup.center(50) + Back.RESET + Style.RESET_ALL + '\n''\n''\n''\n')

# startup to check we are ready
input(
    "Please ensure you have removed any files from the folders before entering the Race ID as this data will be lost. \n \n"
    "For this programme to work you need to ensure that in the same folder as this script you have"
    "the validclubs.txt file, this should include your ZwiftPower club ID's and the name, for example: \n"
    "6363 BCSE \n \n"
    "You should have the folders Club Results, Female and Male. These can be empty or have files in it does not matter. \n \n"
    "You should also have Microsoft Excel installed on your computer as this programme will export this results to Microsoft Excel Files \n \n \n"
    "Type YES and press enter if this is true, if not restart the programme once this is true:"
    "\n")
if input == "YES" or "yes":
    pass

# getting data race id
race_id = input(
    "This programme will give you a brief overview of the results but to view the full results for each category view the relevant output file. \n"
    "Please enter the race ID and press enter:"
    "\n")
date = datetime.datetime.now()
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

# setting color to auto-reset
init(autoreset=True)

# creating dictionary of validclubs and ids from validclubs txt file
validclubs = {}
# opening txt file
with open("validclubs.txt") as f:
    for line in f:
        # defining dictionary in form key is before first whitespace, value is after whitespace
        clubid, club = line.strip("\n").split(maxsplit=1)
        # defining in dictionary club is the value of the id
        validclubs[clubid] = club


# csv writer function
def write_csv(path, inputdata):
    with open(path, 'w', errors='ignore', newline='') as newfile:
        writer = csv.writer(newfile, dialect='excel')
        writer.writerows(inputdata)


disqualification_reasons = ["WKG", "UPG", "ZP", "HR", "HEIGHT", "ZRVG", "new", "AGE", "DQ", "MAP", "20MINS", "5MINS"]
# setting headers for request
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36/wziDaIGv-15"}
# post request form data
data = {'raceID': race_id,
        'csv': 'CSV',
        'submit': 'Submit Request'}
# url of php script which post request is sent to
url = "http://choddo.co.uk/ReadZP5.php"

# sending request to get html
with requests.Session() as s:
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

# open results file to get breakdown of results
with open("results.csv", 'rt', encoding='UTF-8', errors='ignore') as file:
    reader = csv.reader(file, skipinitialspace=True, escapechar='\\')
    # each variable is current number of riders in the category
    A = B = C = D = E = Q = W = 0  # setting all values to 0 so we can work out number of riders in each category
    for row in reader:
        try:
            if row[4] in validclubs and row[7] == "0":  # if club is in validclubs.txt and gender = female
                W = W + 1  # each time this condition is met increase value of W by 1, where W is the amount of women
            if row[4] in validclubs and "A" == row[0]:  # if club is in validclubs.txt and category is A
                A = A + 1  # each time this condition is met increase value of A by 1
            if row[4] in validclubs and "B" == row[0]:  # if club is in validclubs.txt and category is B
                B = B + 1  # each time this condition is met increase value of B by 1
            if row[4] in validclubs and "C" == row[0]:  # if club is in validclubs.txt and category is C
                C = C + 1  # each time this condition is met increase value of C by 1
            if row[4] in validclubs and "D" == row[0]:  # if club is in validclubs.txt and category is D
                D = D + 1  # each time this condition is met increase value of D by 1
            if row[4] in validclubs and row[0] in disqualification_reasons:  # all the possible DQ reason
                Q = Q + 1  # each time this condition is met increase value of Q by 1, where Q is the number of riders DQ'ed
            if row[4] in validclubs and "E" == row[0]:  # if club is in validclubs.txt and category is E
                E = E + 1  # each time this condition is met increase value of E by 1
        except IndexError:  # ignore errors where row is empty
            pass
        total = str(A + B + C + D + E + Q)
print("There were", total, "riders", W, " were women:", "\nCat A:", A, "\nCat B:", B, "\nCat C:",
      C, "\nCat D:", D, "\nCat E:", E, "\nDisqualified:", Q)

# reset B values for men only
with open("results.csv", 'rt', encoding='UTF-8', errors='ignore') as file:
    reader = csv.reader(file, skipinitialspace=True, escapechar='\\')
    # each variable is current number of riders in the category
    B = 0  # setting all values to 0 so we can work out number of riders in each category
    for row in reader:
        if row[0] == "B" and row[4] in validclubs and row[7] == "1":
            B = B + 1


# function to remove any text after ambiguous characters
def remove_values_after_ambiguous_characters(text,
                                             there=re.compile(re.escape('(' or '[' or '|' or '/' or '{' or 'CCR' or
                                                                        'RMCC' or 'Penge' or 'SDW' or 'PWCC' or 'EGCC' or
                                                                        'VCM' or 'MVC' or '[LD' or '[CChasers') + '.*')):
    return there.sub('', text)


# Function to calculate  points based on input A,B,C,D or E
def points_calculator(category, regional_position):
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


# function to write to CSV the second time for full clubs results
def write_csv_individual_results(path, values):
    with open(path, 'a', newline='') as csv_file:  # opening CSV file
        fieldnames = ['Position', 'Category', 'Name', 'Club', 'Points']  # setting fieldnames
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames,
                                dialect='excel')  # writing to CSV file with fieldnames and so it can be opened in Excel
        writer.writerow(values)  # write input values to csv


# Function to get the names of the riders
def get_names():
    names = row[2]  # name = row[2] in file
    riders1 = ' '.join(names.split()[:4])  # remove any values after the 4th word
    riders2 = remove_values_after_ambiguous_characters(riders1)  # removing all values after the ambiguous characters
    riders = riders2.replace(r'[^a-zA-Z0-9]', '')  # replacing all ambiguous values with nothing
    return riders


# Function to get the clubs of the riders
def get_clubs():
    club_name = validclubs.get(row[4])  # searches dictionary of validclubs for the id and returns the value
    return club_name


with open("results.csv", 'rt', encoding='UTF-8', errors='ignore') as file:  # opening the full results file
    reader = csv.reader(file, skipinitialspace=True, escapechar='\\')  # skipping headers
    catlist = []  # setting category as blank so a change is recognised
    for row in reader:
        try:
            if row[4] in validclubs:  # only search CSV for relevant clubs
                if row[7] == "1":  # searching for only men
                    if row[0] not in catlist:  # each time there's a change of category,
                        bcse_position = 1  # reset the rider's finish position to 1
                        catlist.append(row[0])
                    else:  # if category does not change increase BCSE position by 1
                        bcse_position = bcse_position + 1
                    position = row[1]  # second index in row contains position number
                    cat = row[0]
                    club = get_clubs()  # using get_clubs function to return clubs value
                    name = get_names()  # using get_names function to return names which have been cleaned up
                    points = points_calculator(cat,
                                               bcse_position)  # calculate rider points for that cat & position, including DQs
                    if position == "0":  # set the position to be written to CSV, which needs to be different if the rider was DQed (position ==0)
                        position_for_file = "DQ"  # if rider was DQ'ed position in file will be DQ instead of zero
                        points = int(0)  # and they will receive 0 points
                    elif position != 0:  # if they received a finish position i.e. they were not DQed,
                        position_for_file = bcse_position  # position in file will be the value of the variable bcse_position
                    # dictionary of data to write to CSV
                    data = {'Position': position_for_file, 'Category': cat, 'Name': name, 'Club': club,
                            'Points': points}
                    # set name of file + opening & writing to output CSV
                    write_csv_individual_results(
                        ('Male/Individual Results/Male output' + cat + ' ' + date.strftime("%Y, %B, %d") + '.csv'),
                        values=data)
        # ignore blank rows etc.
        except IndexError:
            pass

with open("results.csv", 'rt', encoding='UTF-8', errors='ignore') as file:  # repeat the above section of code for women
    reader = csv.reader(file, skipinitialspace=True, escapechar='\\')
    womenscatlist = []  # as women_category rather than cat, so it resets completely
    for row in reader:
        try:
            if row[4] in validclubs:
                if row[7] == "0":  # searching for only women
                    if row[0] not in womenscatlist:  # Each time there's a change of category,
                        BCSE_Women_Position = 1  # reset the rider's finish position to 1
                        womenscatlist.append(row[0])
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

with open("Female/Individual Results/Full Women's Results" + date.strftime("%Y, %B, %d") + '.csv', 'wb') as file1:
    file1.close()

# defining the csv of all the merged files
csv_out_women = "Female/Individual Results/Full Women's Results" + date.strftime("%Y, %B, %d") + '.csv'
# list of CSVs to merge
csv_list_women = [r'Female\Individual Results\Female outputA' + ' ' + date.strftime("%Y, %B, %d") + '.csv',
                  r'Female\Individual Results\Female outputB' + ' ' + date.strftime("%Y, %B, %d") + '.csv',
                  r'Female\Individual Results\Female outputC' + ' ' + date.strftime("%Y, %B, %d") + '.csv',
                  r'Female\Individual Results\Female outputD' + ' ' + date.strftime("%Y, %B, %d") + '.csv',
                  r'Female\Individual Results\Female outputE' + ' ' + date.strftime("%Y, %B, %d") + '.csv',
                  r'Female\Individual Results\Female outputUPG' + ' ' + date.strftime("%Y, %B, %d") + '.csv',
                  r'Female\Individual Results\Female outputWKG' + ' ' + date.strftime("%Y, %B, %d") + '.csv',
                  r'Female\Individual Results\Female outputHR' + ' ' + date.strftime("%Y, %B, %d") + '.csv']
csv_merge = open(csv_out_women, 'w')  # opening the csv of the merged files
for file in csv_list_women:
    try:
        csv_in = open(file)  # opening each file individually
        for line in csv_in:  # every line in the files to be merged,
            try:
                csv_merge.write(line)  # will be written to a new csv
            except IndexError:  # unless there is an IndexError i.e. a blank line, where this line will be passed
                pass
        csv_in.close()  # closing the csv to be merged
    except FileNotFoundError:
        pass
csv_merge.close()  # closing the output csv

with open("Male/Individual Results/Full Men's Results" + date.strftime("%Y, %B, %d") + '.csv', 'wb') as file2:
    file2.close()

# defining the csv of all the merged files
csv_out_Male = "Male/Individual Results/Full Men's Results" + date.strftime("%Y, %B, %d") + '.csv'
# list of CSVs to merge
csv_list_Male = [r'Male\Individual Results\Male outputA' + ' ' + date.strftime("%Y, %B, %d") + '.csv',
                 r'Male\Individual Results\Male outputB' + ' ' + date.strftime("%Y, %B, %d") + '.csv',
                 r'Male\Individual Results\Male outputB+' + ' ' + date.strftime("%Y, %B, %d") + '.csv',
                 r'Male\Individual Results\Male outputC' + ' ' + date.strftime("%Y, %B, %d") + '.csv',
                 r'Male\Individual Results\Male outputD' + ' ' + date.strftime("%Y, %B, %d") + '.csv',
                 r'Male\Individual Results\Male outputE' + ' ' + date.strftime("%Y, %B, %d") + '.csv',
                 r'Male\Individual Results\Male outputUPG' + ' ' + date.strftime("%Y, %B, %d") + '.csv',
                 r'Male\Individual Results\Male outputWKG.' + ' ' + date.strftime("%Y, %B, %d") + '.csv',
                 r'Male\Individual Results\Male outputHR.' + ' ' + date.strftime("%Y, %B, %d") + '.csv']
csv_merge = open(csv_out_Male, 'w')  # opening the csv of the merged files
for file in csv_list_Male:
    try:
        csv_in = open(file)  # opening each file individually
        for line in csv_in:  # every line in the files to be merged,
            try:
                csv_merge.write(line)  # will be written to a new csv
            except IndexError:  # unless there is an IndexError i.e. a blank line, where this line will be passed
                pass
        csv_in.close()  # closing the csv to be merged
    except FileNotFoundError:
        pass
csv_merge.close()  # closing the output csv


# function to turn the merged CSVs into namedtuple
def csv_to_tuple(path):
    try:
        with open(path, 'r', errors='ignore') as datafile:
            csv_to_tuple_reader = csv.reader(datafile)
            for row in map(FinalIndividualResults._make, csv_to_tuple_reader):
                yield row
    except RuntimeError:
        pass


fields = ("Position", "Category", "Name", "Team", "Points")  # setting the fields for the namedtuple
# creating new namedtuple which will contain the results of all categories, one for men, one for women
FinalIndividualResults = namedtuple('FinalIndividualResults', fields)

try:
    MenFinalOutput = sorted(
        csv_to_tuple("Male/Individual Results/Full Men's Results" + date.strftime("%Y, %B, %d") + ".csv"),
        key=lambda k: k.Team)  # sorting namedtuple into a grouped list
except RuntimeError:  # unless the row is blank, when it will be passed
    pass
try:
    WomenFinalOutput = sorted(
        csv_to_tuple("Female/Individual Results/Full Women's Results" + date.strftime("%Y, %B, %d") + ".csv"),
        key=lambda k: k.Team)  # sorting namedtuple into a grouped list
except RuntimeError:  # unless the row is blank, when it will be passed
    pass


# Function to write namedtuple to a new CSV
def write_data(data_in, data_out):
    out = []  # create a list for the the namedtuples

    def return_teams(x):  # function to return the value of the team in the group
        return x.Team

    for team, group in groupby(data_in,
                               return_teams):  # creating a group of namedtuples where each group is a different team
        group = list(group)  # creating a list of clubs, grouped so there is not any repeats
        d = {'Team': team, 'Points': sum(float(i.Points) for i in group),
             'AvgPoints': mean(float(i.Points) for i in group),
             'NumOfRider': len(group)}  # defining a dictionary for each team where team is the value Team,
        # points is the sum of all the points of riders in that group,
        # AvgPoints is the avg value of points and NumOfRiders is number of items in the group
        out.append(d)  # adding the above dictionary to the list out
        with open(data_out, 'w', newline='') as csv_file:  # writing data to a new csv
            fieldnames = ['Team', 'Points', 'AvgPoints', 'NumOfRider']  # setting row headers of output csv
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            for row in out:  # for every value in the list out a new row in the csv will be written
                writer.writerow(row)


try:
    write_data(MenFinalOutput,
               "Club Results/Men's Club Results" + date.strftime("%Y, %B, %d") + ".csv")  # write the men's data to csv
except NameError:  # unless there is an NameError i.e. the variable doesn't exist - this happens if there are no values because is it a gender specific race
    pass
try:
    write_data(WomenFinalOutput, "Club Results/Women's Club Results" + date.strftime(
        "%Y, %B, %d") + ".csv")  # write the women's data to csv
except NameError:  # unless there is an NameError i.e. the variable doesn't exist - this happens if there are no values because is it a gender specific race
    pass

with open("Club Results/Full Club Results(not sorted)" + date.strftime("%Y, %B, %d") + '.csv', 'wb') as file2:
    file2.close()

# defining the csv of all the merged files
csv_out_clubs = "Club Results/Full Club Results(not sorted)" + date.strftime("%Y, %B, %d") + '.csv'
# list of CSVs to merge
csv_list_clubs = ["Club Results/Men's Club Results" + date.strftime("%Y, %B, %d") + '.csv',
                  "Club Results/Women's Club Results" + date.strftime("%Y, %B, %d") + '.csv']
csv_merge = open(csv_out_clubs, 'w')  # opening the csv of the merged files
for file in csv_list_clubs:
    try:
        csv_in = open(file)  # opening each file individually
        for line in csv_in:  # every line in the files to be merged,
            try:
                csv_merge.write(line)  # will be written to a new csv
            except IndexError:  # unless there is an IndexError i.e. a blank line, where this line will be passed
                pass
        csv_in.close()  # closing the csv to be merged
    except FileNotFoundError:
        pass
csv_merge.close()  # closing the output csv


# function to turn the merged CSVs into namedtuple
def csv_to_tuple_clubs(path):
    with open(path, 'r', errors='ignore') as datafile:
        csv_to_tuple_reader = csv.reader(datafile)
        for row in map(FinalClubResults._make, csv_to_tuple_reader):
            if row[1] is int or float:
                yield row


fields_clubs = ("Team", "Points", "AvgPoints", "NumOfRiders")  # setting the fields for the namedtuple
# creating new namedtuple which will contain the results of all categories, one for men, one for women
FinalClubResults = namedtuple('FinalClubResults', fields_clubs)

ClubFinalOutput = sorted(
    csv_to_tuple_clubs("Club Results/Full Club Results(not sorted)" + date.strftime("%Y, %B, %d") + '.csv'),
    key=lambda k: k.Team)  # sorting namedtuple into a grouped list


# Function to write namedtuple to a new CSV
def write_data_clubs(data_in, data_out):
    out = []  # create a list for the the namedtuples

    def return_teams(x):  # function to return the value of the team in the group
        return x.Team

    for team, group in groupby(data_in,
                               return_teams):  # creating a group of namedtuples where each group is a different team
        if team == "Team":
            pass
        else:
            group = list(group)  # creating a list of clubs, grouped so there is not any repeats
            d = {'Team': team, 'Points': sum(float(i.Points) for i in group),
                 'AvgPoints': sum(float(i.Points) for i in group) / sum(float(i.NumOfRiders) for i in group),
                 'NumOfRiders': sum(
                     int(i.NumOfRiders) for i in
                     group)}  # defining a dictionary for each team where team is the value Team,
            # points is the sum of all the points of riders in that group,
            # AvgPoints is the avg value of points and NumOfRiders is number of items in the group
            out.append(d)  # adding the above dictionary to the list out
            with open(data_out, 'w', newline='') as csv_file:  # writing data to a new csv
                fieldnames = ['Team', 'Points', 'AvgPoints', 'NumOfRiders']  # setting row headers of output csv
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writeheader()
                for row in out:  # for every value in the list out a new row in the csv will be written
                    writer.writerow(row)


write_data_clubs(ClubFinalOutput, "Full Club Results" + date.strftime("%Y, %B, %d") + '.csv')
os.remove('results.csv')
os.remove("Club Results/Full Club Results(not sorted)" + date.strftime("%Y, %B, %d") + '.csv')
print(datetime.datetime.now(),
      Fore.GREEN + "Process Complete, check your folder for the results")  # print that the process is complete
print("Execution time =", datetime.datetime.now() - date)
time.sleep(3600)  # sleep to stop terminal closing automatically so overview can be seen
