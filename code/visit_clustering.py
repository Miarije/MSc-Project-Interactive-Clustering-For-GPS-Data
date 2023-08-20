from code.utils import create_basic_scatter, is_valid_filename
from code.plot import InteractivePlot

import pandas as pd
import os
import sqlite3
import pickle

DB_PATH = "database/individual_data.db"

def view_clustering (indv_instance):
  data_path = indv_instance.return_data_filepath("clustered")
  data = pd.read_csv(data_path, delimiter = ",")

  title = indv_instance.clustering_name + " (view)"
  cluster_names = indv_instance.cluster_names
  x, y, box, aspect, map, filepath = indv_instance.return_plot_parameters(data, title)
  create_basic_scatter(x, y, box, aspect, map, filepath, data['label'].values.tolist(), indv_instance.cmap, cluster_names, False, True)


def edit_names (indv_instance):
  cluster_names = indv_instance.cluster_names
  data_path = indv_instance.return_data_filepath("clustered")
  data = pd.read_csv(data_path, delimiter = ",")

  while True:
    print("[1] Change a cluster name\n[2] Change clustering name")
    print("Type 'back' to go back.")

    user_input = input(">>> ")
    if user_input == 'back':
      return
    
    os.system('cls')
    if user_input.isdigit():
      choice = int(user_input)

      # edit cluster names
      if choice == 1:
        while True:
          # receive new name
          print("Change a cluster name with the following format: original_name=new_name.")
          print("Available names:", cluster_names)
          print("Type 'back' to go back to the menu.")

          user_input = input(">>> ").strip()
          if user_input == 'back':
            os.system('cls')
            return

          # get names
          name_parts = user_input.split('=')
          original_name = name_parts[0].strip()
          new_name = name_parts[1].strip()

          # update name
          if original_name in cluster_names and not new_name in cluster_names:
            # in the data
            data['cluster'] = data['cluster'].replace(original_name, new_name)
            data.to_csv(data_path, sep=",")

            # in the database
            connect = sqlite3.connect(DB_PATH)
            cursor = connect.cursor()

            id = indv_instance.db_id

            cluster_names = [new_name if name == original_name else name for name in cluster_names]
            pickled_names = pickle.dumps(cluster_names)
            # update color map
            cmap = indv_instance.create_custom_cmap(cluster_names)
            pickled_cmap = pickle.dumps(cmap)
            cursor.execute("UPDATE cluster_data SET cluster_names=? WHERE id=?", (pickled_names, id))
            cursor.execute("UPDATE cluster_data SET cluster_cmap=? WHERE id=?", (pickled_cmap, id))

            connect.commit()
            connect.close()

            os.system('cls')
            print("Succesfully updated cluster name", original_name, "to", new_name, "\n")
          else:
            os.system('cls')
            print("Either the original name you entered is not in the current cluster names, or the new name you entered is already in use.")
            print("Please try again")

      # edit clustering name
      elif choice == 2:
        print("Enter the new clustering name.")
        print("Note that this does not change the name in previously made plot names, only future ones.")
        user_input = input(">>> ").strip()

        original_name = indv_instance.clustering_name
        valid = is_valid_filename(user_input)
        if valid:
          new_name = user_input
          # update file name
          i = data_path.find('[')
          j = data_path.find(']')

          new_data_path = data_path[:i+1] + new_name + data_path[j:]
          data.to_csv(new_data_path, sep=",")
          # remove old file
          os.remove(data_path)

          # update database
          connect = sqlite3.connect(DB_PATH)
          cursor = connect.cursor()

          id = indv_instance.db_id

          try:
            cursor.execute("UPDATE cluster_data SET clustering_name=? WHERE id=? AND clustering_name=?", (new_name, id, original_name))
          except sqlite3.IntegrityError:
            # delete current entry if one already exists
            cursor.execute('DELETE FROM cluster_data WHERE id=? AND clustering_name=?', (id, new_name))
            cursor.execute("UPDATE cluster_data SET clustering_name=? WHERE id=?", (new_name, id))

          connect.commit()
          connect.close()

          os.system('cls')
          print("Succesfully updated clustering name", original_name, "to", new_name, "\n")
          return new_name

def restart_clustering (indv_instance):
  data_path = indv_instance.return_data_filepath("clustered")
  data = pd.read_csv(data_path, delimiter = ",")

  print("Succesfully loaded in clustered data. Do you want to give the clustering a new name?")
  user_input = input("yes/no: ")
  if user_input == 'yes':
    print("Enter the new name:")
    user_input = input(">>> ")
    if is_valid_filename(user_input):
      indv_instance.clustering_name = user_input

  # create instance for interactive plot functionality
  plot_instance = InteractivePlot(indv_instance, data)

  # adjustment loop
  while True:
    if plot_instance.end_clustering:
      return plot_instance.saved_clustering
    
    print("\nTo make changes, select the clusters you wish to adjust on the plot.")
    print("Use the buttons underneath the plot to start reclustering, merging or to undo.")
    print("Type 'algorithm=agglo' to cluster with agglomerative clustering.")

    # create the plot and start the interactive clustering
    title = indv_instance.clustering_name + " | clustered data"
    x, y, box, aspect, map, filepath = indv_instance.return_plot_parameters(plot_instance.data, title)

    saveFile = False
    labels = plot_instance.data['label'].values.tolist()
    plot_instance.create_interactive_plot(x, y, box, aspect, map, filepath, labels, saveFile)

    if plot_instance.end_clustering:
      return plot_instance.saved_clustering
    
    #os.system('cls')
    print("\nType 'algorithm=agglo' to cluster with agglomerative clustering.")
    print("Type 'cont' to bring the plot back up if you close it.")
    print("Type 'exit' to return to the main menu. !WARNING! This will delete any progress.")

    # receive input
    user_input = input(">>> ").lower()
    os.system('cls')
    if user_input == 'exit':
      while True:
        print("Are you sure you wish to end the clustering? All your progress will be deleted.")
        user_input = input("yes/no: ").lower()
        os.system('cls')
        if user_input == 'yes':
          print("Clustering cancelled.")
          return
        elif user_input == 'no':
          break
    
    if user_input == 'algorithm=agglo':
      print("Reclustering using agglomerative clustering. Note that this may take longer.")
      if len(plot_instance.clusterlist) > 0:
        plot_instance.adjustments += 1
        plot_instance.reclusterings += 1
        plot_instance.recluster('agglo')
      else:
        print("Please select one or more clusters to recluster on.")
    
    if user_input == 'cont':
      continue