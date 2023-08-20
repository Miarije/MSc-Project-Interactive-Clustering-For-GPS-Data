from code.individual import Individual
from code.utils import create_basic_scatter
from code.database import add_database_entry

import astral
from astral.sun import sun
from datetime import datetime
import pytz

import os
import shutil

import pandas as pd
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon

########################################################################################################################################################################################################

def create_polygon (coords):
  min_long = coords[0]
  max_long = coords[1]
  min_lat = coords[2]
  max_lat = coords[3]

  poly = Polygon([
      (max_lat, min_long),
      (max_lat, max_long),
      (min_lat, max_long),
      (min_lat, min_long)
  ])
  return poly

########################################################################################################################################################################################################

# takes the data from february to july and excludes any data outside the selected habitat
# keeps track of trips consisting of > 1 point outside the habitat, after arriving
def keep_area_data (data, filepath, coords):
  rows_start = data.shape[0]

  start = False
  end = False

  outside_data = pd.DataFrame(columns=['location-lat', 'location-long', 'timestamp'])

  poly = create_polygon(coords)
  for index, row in data.iterrows():
    point = Point(row['location-lat'], row['location-long'])
    check = poly.contains(point)

    # point outside habitat
    if not check:
      new_row = row[["location-lat", "location-long", "timestamp"]]
      outside_data = pd.concat([outside_data, new_row.to_frame().T], ignore_index=True)

      data.drop(index, inplace=True)

      if not start:
        start = row['timestamp']
        end = row['timestamp']
      if start:
        end = row['timestamp']

    # just arrived inside habitat
    if check:
      if start != end:
        print("Entering area. Away from", start, "to", end)
      start = False
      end = False

  # if there is data left
  if data.shape[0] > 0:
    # end of data reached
    if start:
      print("Left area and did not return. Away from", start, "to", end, "\n")
      start = False
      end = False

    data.reset_index(inplace=True)
    rows_end = data.shape[0]
    print("Rows before:", rows_start, "row now: ", rows_end, " | Rows deleted:", rows_start-rows_end)
    print("Start date:", data['timestamp'].iloc[0])
    print("End date:", data['timestamp'].iloc[-1])

    # export data, leave out irrelevant columns
    data = data[[ 'event-id', 'timestamp', 'location-long', 'location-lat',
                  'external-temperature', 'ground-speed', 'heading', 'height-above-msl',
                  'year', 'month', 'day', 'animal-id']]

    print("File location:", filepath)
    print("Exporting file...\n")
    data.to_csv(filepath, sep=",", index=False)

    return outside_data, True
  # if there is no data in the breeding habitat for this year
  else:
    print("This year has no data in the breeding territory. Cancelled.")
    return outside_data, False

########################################################################################################################################################################################################

def create_file_dir (animal_id, year):
  main_dir = "individuals/"
  individual_dir = main_dir + str(animal_id) + "_" + str(year) + "_"

  i = 1
  # check which index to use
  while True:
    check_dir = individual_dir + str(i)
    # if current index is not in use
    if not os.path.exists(check_dir):
      # create main folder
      individual_dir = check_dir
      os.makedirs(individual_dir)

      # create data folder
      data_dir = individual_dir + "/data"
      os.makedirs(data_dir)

      # create plot folder
      plot_dir = individual_dir + "/plots"
      os.makedirs(plot_dir)

      return i

    # otherwise check the next one
    else:
      i += 1

########################################################################################################################################################################################################

def remove_file_dir (indv_object):
    dir = indv_object.return_base_dir()
    shutil.rmtree(dir)

########################################################################################################################################################################################################

def create_breeding_dataset (animal_id, coords, data_file):
  print("Reading csv file...")
  # load vlieland data
  if data_file == 'vlieland':
    gps_2016_vlieland = pd.read_csv("full_data/O_VLIELAND-gps-2016.csv", delimiter = ",")
    gps_2017_vlieland = pd.read_csv("full_data/O_VLIELAND-gps-2017.csv", delimiter = ",")
    gps_2018_vlieland = pd.read_csv("full_data/O_VLIELAND-gps-2018.csv", delimiter = ",")
    gps_2019_vlieland = pd.read_csv("full_data/O_VLIELAND-gps-2019.csv", delimiter = ",")
    gps_2020_vlieland = pd.read_csv("full_data/O_VLIELAND-gps-2020.csv", delimiter = ",")
    gps_2021_vlieland = pd.read_csv("full_data/O_VLIELAND-gps-2021.csv", delimiter = ",")

    all_years = [gps_2016_vlieland, gps_2017_vlieland, gps_2018_vlieland, gps_2019_vlieland, gps_2020_vlieland, gps_2021_vlieland]
    vlieland_data = pd.concat(all_years)

  # load custom data
  else:
    vlieland_data = pd.read_csv(data_file, delimiter = ",")

  if 'animal-id' not in vlieland_data.columns:
    vlieland_data['animal-id'] = vlieland_data['individual-local-identifier']

  print("preparing to create breeding dataset")
  individual_data = vlieland_data.copy()

  # retrieve individual's data
  individual_data = individual_data[individual_data['animal-id'] == animal_id]
  individual_data.reset_index(inplace=True)
  individual_data['timestamp'] = pd.to_datetime(individual_data['timestamp'])

  if 'year' not in individual_data.columns:
    individual_data['year'] = individual_data['timestamp'].dt.year
  if 'month' not in individual_data.columns:
    individual_data['month'] = individual_data['timestamp'].dt.month
  if 'day' not in individual_data.columns:
    individual_data['day'] = individual_data['timestamp'].dt.day

  years = list(set(individual_data['year'].tolist()))
  print("Years with data:", years)
  indexes = []

  years_with_data = []

  for year in years:
    # retrieve data for this year
    print("============================================================")
    print(animal_id, "|", year)
    individual_data_yr = individual_data.copy()
    individual_data_yr = individual_data_yr[individual_data_yr['year'] == year]

    # create file directory
    individual_index = create_file_dir(animal_id, year)
    indexes.append(individual_index)

    # exclude data outside of area
    indv_object = Individual(animal_id, year, individual_index)
    filepath = indv_object.return_data_filepath("processed")
    outside_data, export = keep_area_data(individual_data_yr, filepath, coords)

    if export:
      input_list = [animal_id, year, coords[0], coords[1], coords[2], coords[3]]
      add_database_entry(input_list, False)

      filepath = indv_object.return_data_filepath("excluded")
      outside_data.to_csv(filepath, sep=",", index=False)
      years_with_data.append(year)
    else:
      remove_file_dir(indv_object)

  # for use later
  return years_with_data, indexes

########################################################################################################################################################################################################

def separate_day_night (data, filepath):
  print("Preparing to add daytime column")
  print("Size of original data file:", data.shape[0])

  data['daytime'] = False

  # for each point, check if daytime
  for index, row in data.iterrows():
    # create observer
    loc = astral.Observer(row['location-lat'], row['location-long'], row['height-above-msl'])
    timezone = pytz.timezone("Europe/Amsterdam")

    # convert to datetime
    row['timestamp'] = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')

    # get sunrise and sunset times
    sunrise = (astral.sun.sunrise(loc, row['timestamp'].date(), timezone)).time()
    sunset = (astral.sun.sunset(loc, row['timestamp'].date(), timezone)).time()

    current_time = row['timestamp'].time()

    # check if day
    if sunrise < current_time < sunset:
      data.at[index, 'daytime'] = True

  # separate by day and night
  day = data[data['daytime'] == True].copy()
  night = data[data['daytime'] == False].copy()

  print("Size of daytime data file:", day.shape[0])
  print("Size of nighttime data file:", night.shape[0])

  # overwrite datafile with day/night data
  print("Exporting file...\n")
  data.to_csv(filepath, sep = ",", index=False)

  # for use later
  return data

########################################################################################################################################################################################################

def add_behaviours (gps_data, filepath, individual, year):
  print("Preparing to add behaviour tags")
  print("Original file size:", gps_data.shape[0])
  # read tag file
  tags_file = "full_data/O_VLIELAND-accessory-measurements-" + str(year) + ".csv"
  tags = pd.read_csv(tags_file, delimiter = ",")

  # check if there is data available
  if not individual in tags['individual-local-identifier'].unique():
    print("No behaviour tags found for", str(individual), "in", str(year))
    print("Operation cancelled.")
    return

  # grab individual tags
  indv_tag_data = tags.copy()
  indv_tag_data = indv_tag_data[indv_tag_data['individual-local-identifier'] == individual]

  incomplete = False
  # are there enough tags?
  if gps_data.shape[0] > indv_tag_data.shape[0]:
    print("!! The GPS data contains", gps_data.shape[0], "rows while the tag data contains", indv_tag_data.shape[0], "rows.")
    print("!! The behaviour tags may be incomplete.")
    incomplete = True

  # convert timestamps to leave out seconds, for merging
  indv_tag_data['timestamp'] = pd.to_datetime(indv_tag_data['timestamp'])
  indv_tag_data['timestamp'] = indv_tag_data['timestamp'].round("min")

  gps_data['timestamp'] = pd.to_datetime(gps_data['timestamp'])
  gps_data['timestamp'] = gps_data['timestamp'].round("min")
  #gps_data['timestamp'] = gps_data['timestamp'].dt.strftime('%Y-%m-%d %H:%M')

  # merge on gps data
  tagged_gps_data = gps_data.merge(indv_tag_data, on='timestamp', how='left')

  # remove columns we don't need
  data = tagged_gps_data[['event-id_x', 'timestamp', 'location-long', 'location-lat',
       'external-temperature', 'ground-speed', 'heading', 'height-above-msl',
       'year', 'month', 'day', 'animal-id', 'daytime', 'behavioural-classification']].copy()
  data.rename(columns={"event-id_x": "event-id"}, inplace=True)

  # drop possible duplicate rows
  data.drop_duplicates(inplace=True)
  print("New file size:", tagged_gps_data.shape[0])

  # check if nan values for behaviour
  print("!! There are", data['behavioural-classification'].isna().sum(), "behaviour tags missing.")

  # export data
  print("Exporting file...\n")
  data.to_csv(filepath, sep = ",", index=False)

########################################################################################################################################################################################################


def start_preprocessing():
  while True:
    print("In order to add a new individual's dataset to the database, we need the following information:")
    print("animal id, minimum longitude, maximum longitude, minimum latitude, maximum latitude")
    print("The longitude and latitude coordinates should correspond to those of the map image, which should be located in the maps folder.")
    print("(Type 'exit' to return to the main menu)")

    user_input = input(">>> ")
    os.system('cls')

    if user_input == 'exit': return

    split_parts = user_input.split(",")
    input_list = []
      
    # check each input
    for part in split_parts:
      item = part.strip()
      # check if integer
      try:
        item = float(item)
      except ValueError: 
        print("ERROR: ", item, "is not a valid float.")
        break
      input_list.append(item)
    if len(input_list) != 5:
      print("ERROR: You did not provide all necessary data.\n")
    else:
      break

  aspect = 1.64
  input_list[0] = int(input_list[0])

  while True:
    print("Presss enter to use the Vlieland data, or enter the path to the csv file you wish to use. If it is in the full_data folder, the path will be full_data/your_data.csv")
    user_input = input(">>> ")

    if len(user_input) == 0:
      data_file = 'vlieland'
      break

    elif os.path.exists(user_input):
      data_file = user_input
      break
    else:
      print("File not found")

  ####################################################

  print("The following data has been entered.")
  print("Animal id to be preprocessed:", input_list[0])
  print("Coordinates:", input_list[1], input_list[2], input_list[3], input_list[4])
  print("Data:", data_file)

  print("Do you want to continue? Press enter. Otherwise, type 'exit' to return to the main menu.")
  user_input = input(">>> ")

  if user_input == 'exit':
    return

  animal_id = input_list[0]
  min_long = input_list[1]
  max_long = input_list[2]
  min_lat = input_list[3]
  max_lat = input_list[4]

  coords = [min_long, max_long, min_lat, max_lat]

  # remove data outside of habitat for all years -> separate into years
  years, indexes = create_breeding_dataset(animal_id, coords, data_file)

  if years is None:
    return

  # for each year of this individual
  for year, i in zip(years, indexes):
    indv_object = Individual(animal_id, year, i)
    indv_object.load_individual_data()
    filepath = indv_object.return_data_filepath("processed")

    print("\n=======================================================================")
    print("Current year:", year)

    # load current data for this year
    data = pd.read_csv(filepath, delimiter = ",")

    # add column to indicate daytime
    data = separate_day_night(data, filepath)

    # add behaviour tags
    add_behaviours(data, filepath, animal_id, year)

  print("Finished pre-processing data")
  print("Creating plots..")

  # create basic scatter plots
  for year, i in zip(years,indexes):
    # read data
    indv_object = Individual(animal_id, year, i)
    indv_object.load_individual_data()
    filepath = indv_object.return_data_filepath("processed")

    data = pd.read_csv(filepath, delimiter = ",")

    data = data[~data['timestamp'].duplicated()]

    title = "raw data"
    x, y, box, aspect, map, filepath = indv_object.return_plot_parameters(data, title)

    while True:
      if not os.path.exists(map):
        print("No map image found at", map)
        print("Please provide one, then press enter")

        _ = input()
      else:
        break

    # create plot
    create_basic_scatter(x, y, box, aspect, map, filepath, None, None, None, None, True)