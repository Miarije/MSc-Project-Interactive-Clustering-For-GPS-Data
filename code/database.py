from code.utils import create_individual_folders, create_basic_scatter

import sqlite3
import os
import matplotlib.pyplot as plt

# global variables
DB_PATH = "database/individual_data.db"
PLOT_ASPECT = 1.64

########################################################################################################################################################################################################

# receive user input to add a new individual instance to the database
def add_database_entry(input_list, create_folders):
  # connect
  connect = sqlite3.connect(DB_PATH)
  cursor = connect.cursor()

  animal_id = int(input_list[0])
  year = int(input_list[1])
  min_long = input_list[2]
  max_long = input_list[3]
  min_lat = input_list[4]
  max_lat = input_list[5]

  # check if there are existing entries for this individual and this year
  cursor.execute("SELECT * FROM indv_data WHERE animal_id=? AND year=?", (animal_id, year))
  result = cursor.fetchall()

  index = len(result) + 1 if result else 1
  id = str(animal_id) + "_" + str(year) + "_" + str(index)
  map_path = "maps/" + str(animal_id) + "-" + str(index) + ".png"

  data_entry = [(id, animal_id, year, index, map_path, PLOT_ASPECT, min_long, max_long, min_lat, max_lat)]

  cursor.executemany('INSERT INTO indv_data VALUES (?,?,?,?,?,?,?,?,?,?)', data_entry)

  connect.commit()
  connect.close()

  print("\nNew individual dataset successfully added with id", id)

  if create_folders:
    create_individual_folders(id)

  # check if map path exists
  if not os.path.isfile(map_path):
    print("\n!WARNING! There is no map available for this individual. Make sure it is located at", map_path)

########################################################################################################################################################################################################

# create a database entry for the clustering
def save_clustering (indv_instance, data):
  print("Please take a look at the map and name your clusters, in order of index. Make sure the names are unique.")
  # show the map again
  x, y, box, aspect, map, filepath = indv_instance.return_plot_parameters(data, "preview")
  create_basic_scatter(x, y, box, aspect, map, filepath, data['label'].values.tolist(), None, None, True, False)
         
  while True:
    user_input = input(">>> ")
    cluster_names = [item.strip() for item in user_input.split(",")]

    # check if we have the right amount of names
    length = len(data['label'].unique().tolist())
    if len(cluster_names) != length:
      print("Incorrect number of names, please try again and ensure there are", length, "names.")
    # check if there's no duplicates
    elif len(cluster_names) > len(set(cluster_names)):
      print("Please make sure the names are unique, duplicate names are not allowed.")
    else:
      break

  plt.close()
  os.system('cls')

  # save the data for this clustering to the database
  indv_instance.create_custom_cmap(cluster_names)
  indv_instance.save_cluster_data(cluster_names)

  # save the csv
  data['cluster'] = [cluster_names[label] for label in data['label']]
  filepath = indv_instance.return_data_filepath("clustered")

  print("Exporting clustered data to", filepath)
  data.to_csv(filepath, sep=",", index=False)

  # save the plot
  title = indv_instance.clustering_name + " (clustered)"

  x, y, box, aspect, map, filepath = indv_instance.return_plot_parameters(data, title)
  create_basic_scatter(x, y, box, aspect, map, filepath, data['label'].values.tolist(), indv_instance.cmap, cluster_names, False, True)

########################################################################################################################################################################################################

# retrieve all entries in the database for given animal id, return a dictionary containing the index and corresponding database id
def retrieve_individual_entries (animal_id):
  # connect
  connect = sqlite3.connect(DB_PATH)
  cursor = connect.cursor()

  cursor.execute("SELECT id, animal_id, year, idx FROM indv_data WHERE animal_id=?", (animal_id,))
  result = cursor.fetchall()

  connect.commit()
  connect.close()

  
  entries = {}
  if result:
    print("Please choose the index of the dataset for this individual that you want to cluster on.")
    print("[#] animal id | year | index")
    for i, entry in enumerate(result):
      print("[{}] {}   | {} | {}".format(i, entry[1], entry[2], entry[3]))
      entries[i] = [entry[1], entry[2], entry[3]]
  else:
    print("No individuals found in the database with animal id", animal_id)
    return None

  
  return entries

########################################################################################################################################################################################################

def retrieve_cluster_entries (animal_id):
  # connect
  connect = sqlite3.connect(DB_PATH)
  cursor = connect.cursor()

  cursor.execute("SELECT id, animal_id, year, idx, clustering_name FROM cluster_data WHERE animal_id=?", (animal_id,))
  result = cursor.fetchall()

  connect.commit()
  connect.close()

  
  entries = {}
  if result:
    print("Please choose the index of the clustering for this individual that you want to analyze.")
    print("[#] animal id | year | index | clustering name")
    for i, entry in enumerate(result):
      print("[{}] {}   | {} | {}     | {}".format(i, entry[1], entry[2], entry[3], entry[4]))
      entries[i] = [entry[1], entry[2], entry[3], entry[4]]
  else:
    print("No individuals found in the database with animal id", animal_id)
    print("\n")
    return None
  
  return entries

########################################################################################################################################################################################################

def retrieve_all_entries(to_cluster):
  connect = sqlite3.connect(DB_PATH)
  cursor = connect.cursor()

  if to_cluster:
    cursor.execute("SELECT animal_id FROM indv_data")
  else:
    cursor.execute("SELECT animal_id FROM cluster_data")
  # retrieve list of all animal_ids
  result = cursor.fetchall()
  result_list = [row[0] for row in result]

  connect.commit()
  connect.close()

  # remove duplicates
  animal_ids = list(set(result_list))

  db = 'individuals' if to_cluster else 'clusterings'
  print("The following animals are in the", db, "database.")

  for entry in sorted(animal_ids):
    print(entry)

########################################################################################################################################################################################################

# load data for entered animal id from either database and select desired dataset
def input_animal_id (to_cluster):
  while True:
    print("(Type 'exit' to return to the main menu)")
    user_input = input(">>> ").lower()
    os.system('cls')

    if user_input == 'exit': return None, True

    if user_input == 'show':
      retrieve_all_entries(to_cluster)
      print("Provide the animal id of the individual you want to use.")
      continue

    if user_input.isdigit():
      # show entries for this animal id
      user_input = int(user_input)
      if to_cluster:
        entries = retrieve_individual_entries(user_input)
      else:
        entries = retrieve_cluster_entries(user_input)

      # animal id not found, ask again
      if entries is None:
        if to_cluster:
          print("Make sure to register the individual before clustering.")
        else:
          print("You have to complete at least one clustering with this individual to do this.")
        return None, None
      else:
        break
    else:
      print("Invalid animal id")
        
  # animal id found, options were printed
  # ask for their choice
  print("(Type 'exit' to return to the main menu)")
  while True:
    user_input = input(">>> ").lower()

    if user_input == 'exit': return None, True
    
    # check if input is a valid option
    if user_input.isdigit():
      user_input = int(user_input)
      if not (user_input >= 0 and user_input < len(entries)):
        print("ERROR: Invalid choice, please select the index of the entry you want to use\n")
      else:
        return entries, user_input
    else:
      print("ERROR: Invalid id\n")

