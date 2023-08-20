from code.individual import Individual
from code.utils import create_basic_scatter, is_valid_filename
from code.interactive_clustering import interactive_clustering
from code.database import add_database_entry, input_animal_id
from code.cluster_analysis import run_interval_analysis, run_nestingsite_analysis, run_proportion_analysis
from code.preprocessing import start_preprocessing
from code.visit_clustering import *

import sqlite3
import os
import pandas as pd

########################################################################################################################################################################################################

# receives and checks user input to add a new database entry
def add_individual():
  while True:
    print("Does the individual require preprocessing, or is it ready to go?")
    print("Preprocessing means: removing data outside of the defined home range, adding a daytime column and adding behaviour tags if available.")
    print("[1] To start preprocessing\n[2] To add a preprocessed individual dataset to the database.")
    print("(Type 'exit' to return to the main menu)")

    user_input = input(">>> ")
    os.system('cls')
    if user_input == 'exit':
      return

    if user_input.isdigit():
      user_input = int(user_input)
      if user_input == 1:
        start_preprocessing()
        print("Preprocessing complete. Press enter to return to the main menu.")
        _ = input()
        return
      elif user_input == 2:
        break
      else:
        print("Invalid number")
    else:
      print("Invalid option.")

  while True:
    print("In order to add a new individual's dataset to the database, we need the following information:")
    print("animal id, year, minimum longitude, maximum longitude, minimum latitude, maximum latitude")
    print("The longitude and latitude coordinates should correspond to those of the map image, which should be located in the maps folder.")
    print("(Type 'exit' to return to the main menu)")

    user_input = input(">>>")
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

    if len(input_list) == 6:
      add_database_entry(input_list, True)
      return
    else:
      print("ERROR: You did not provide all necessary data.\n")

########################################################################################################################################################################################################

# load individual's data and prepare it to start clustering
def prepare_data_for_clustering (indv_instance):
  # load data
  data_path = indv_instance.return_data_filepath("processed")

  # wait until the data file exists
  while not os.path.exists(data_path):
    print("!Warning! There is no data file for this individual. Please make sure to place it at", data_path, "before continuing.")
    print("Press enter to continue once the file is in the correct location. Ensure it has the naming specified above.")
    _ = input()
  
  os.system('cls')
  # wait until map path exists
  map_path = indv_instance.map_path
  while not os.path.exists(map_path):
    print("!Warning! There is no map image for this individual. Please make sure to place it at", map_path, "before continuing.")
    print("Press enter to continue once the image is in the correct location. Ensure it has the naming specified above.")
    _ = input()

  data = pd.read_csv(data_path, delimiter = ",")

  while True:
    os.system('cls')
    # check for behaviour tags
    if 'behavioural-classification' in data.columns:
      print("Your data contains behaviour tags. Press enter to cluster on all data, or type the names of the behaviours you want to cluster.")
      behaviours_in_data = data['behavioural-classification'].dropna().unique().tolist()
      print("Behaviours available:", behaviours_in_data)
      print("(Type 'back' to choose another individual or 'exit' to return to the main menu)")

      # check input
      user_input = input(">>> ").lower()
      os.system('cls')
      if len(user_input) != 0:
        if user_input == 'back':
          initialize_interactive_clustering()
          return
        elif user_input == 'exit':
          print("Exit")
          return
        
        # select behaviours
        user_behaviours = [item.strip() for item in user_input.split(",")]
        complete = all(item in behaviours_in_data for item in user_behaviours)
        if not complete:
          print("!Warning! One or more of the behaviours you entered do not correspond to the behaviours available.")
          print("The behaviours you entered are:", user_behaviours)
          print("Please make sure you enter valid behaviours. Press enter to retry.")
          _ = input()
          continue
        data = data[data['behavioural-classification'].isin(user_behaviours)]
        rows_before = data.shape[0]
        data = data[~data['timestamp'].duplicated()]
        rows_diff = rows_before - data.shape[0]
        if rows_diff != 0:
          print("Removed", rows_diff, "duplicated rows.")

    # name clustering
    print("Please give your clustering a name. Note that if it is not unique, it will overwrite previous results.")
    while True:
      user_input = input(">>> ")
      os.system('cls')
      if is_valid_filename(user_input):
        indv_instance.clustering_name = user_input
        break

    # show plot of selected data
    x, y, box, aspect, map, filepath = indv_instance.return_plot_parameters(data, indv_instance.clustering_name)
    create_basic_scatter(x, y, box, aspect, map, filepath, None, None, None, False, False)
    
    # confirmation
    while True:
      # confirm to start clustering  
      print("Your selected data- or subset has", data.shape[0], "rows. Do you want to start clustering?")
      user_input = input("start/exit: ")
      os.system('cls')
      if user_input == "start":
        interactive_clustering(indv_instance, data)
        return
      elif user_input == "exit":
        return

########################################################################################################################################################################################################

# receives and checks user input to select an individual instance for clustering
def initialize_interactive_clustering():
  while True:
    print("Select an individual instance on which to run the clustering. Provide the animal id of the individual you want to cluster.")
    print("Or type 'show' to show a list of all available animal ids.")
    entries, user_input = input_animal_id(True)

    if entries is not None:
      break
    if entries is None and user_input:
      return

  # load the data
  indv_list = entries[user_input]
  indv_instance = Individual(indv_list[0], indv_list[1], indv_list[2])
  indv_instance.load_individual_data()

  prepare_data_for_clustering(indv_instance)

########################################################################################################################################################################################################

def run_analysis():
  while True:
    print("Select an individual instance on which to perform analysis. Provide the animal id of the individual you want to analyse.")
    print("Or type 'show' to show a list of all available animal ids.")
    entries, user_input = input_animal_id(False)

    if entries is not None:
      break
    if entries is None and user_input:
      return

  # load the data
  indv_list = entries[user_input]
  os.system('cls')
  indv_instance = Individual(indv_list[0], indv_list[1], indv_list[2])
  indv_instance.clustering_name = indv_list[3]
  indv_instance.load_cluster_data()
  indv_instance.load_individual_data()

  data_path = indv_instance.return_data_filepath("clustered")

  # wait until the data file exists
  while not os.path.exists(data_path):
    print("!Warning! There is no data file for this individual. Please make sure to place it at", data_path, "before continuing.")
    print("Press enter to continue once the file is in the correct location. Ensure it has the naming specified above.")
    _ = input()

  # which analysis
  stop = False
  while not stop:
    print("Which type of analysis would you like to perform on this data?")
    print("[1] Proportion analysis\n[2] Interval analysis\n[3] Nesting site analysis")
    print("Type 'exit' to return to the main menu.")

    user_input = input(">>> ").lower()
    os.system('cls')
    if user_input.isdigit():
      choice = int(user_input)
      if choice == 1:
        stop = run_proportion_analysis(indv_instance)
      elif choice == 2:
        stop = run_interval_analysis(indv_instance)
      elif choice == 3:
        stop = run_nestingsite_analysis(indv_instance)
      else:  
        print("Please enter a number between 1 and 3 to make your choice.")
    elif user_input == 'exit':
      return


def revisit_clustering():
  while True:
    print("Provide the animal id of the individual you want to view or edit.")
    print("Or type 'show' to show a list of all available animal ids.")
    entries, user_input = input_animal_id(False)

    if entries is not None:
      break
    if entries is None and user_input:
      return

  # load the data
  indv_list = entries[user_input]
  os.system('cls')
  # check if data file exists
  indv_instance = Individual(indv_list[0], indv_list[1], indv_list[2])
  indv_instance.clustering_name = indv_list[3]
  data_path = indv_instance.return_data_filepath("clustered")

  # wait until the data file exists
  while not os.path.exists(data_path):
    print("!Warning! There is no data file for this individual. Please make sure to place it at", data_path, "before continuing.")
    print("Press enter to continue once the file is in the correct location. Ensure it has the naming specified above.")
    _ = input()
  
  # vars for updated clustering name
  name = indv_list[3]
  new_name = None
  while True:
    # reload instance in case some names changed
    indv_instance = Individual(indv_list[0], indv_list[1], indv_list[2])
    indv_instance.clustering_name = name
    indv_instance.load_cluster_data()
    indv_instance.load_individual_data()

    os.system('cls')
    print("What do you want to do?")
    print("[1] View the clustered data\n[2] Change the name of the clustering or clusters\n[3] Make changes to the clustering")
    print("Type 'exit' to exit.")

    if user_input == 'exit':
      return

    # select choice
    user_input = input("Select the number: ")
    os.system('cls')
    if user_input.isdigit():
      choice = int(user_input)
      if choice == 1:
        _ = view_clustering(indv_instance)
      elif choice == 2:
        new_name = edit_names(indv_instance)
        name = new_name if new_name is not None else name
      elif choice == 3:
        saved = restart_clustering(indv_instance)
        # clustering has been saved with different name
        if saved and name != indv_instance.clustering_name:
          os.system('cls')
          print("Do you want to delete the clustering with the name " + name + "?")
          user_input = input("yes/no: ")
          if user_input == 'yes': 
            # delete csv file
            os.remove(data_path)
            # delete database entry
            connect = sqlite3.connect(DB_PATH)
            cursor = connect.cursor()

            id = indv_instance.db_id

            cursor.execute("DELETE FROM cluster_data WHERE id=? and clustering_name=?", (id, name))

            connect.commit()
            connect.close()
          name = indv_instance.clustering_name

      else:
        print("Please enter a number between 1 and 3 to make your choice.")
    else:
      print("Please enter a number between 1 and 3 to make your choice.")