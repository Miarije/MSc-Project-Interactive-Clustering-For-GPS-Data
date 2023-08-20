from code.clustering import start_initial_clustering
from code.plot import InteractivePlot

import os

########################################################################################################################################################################################################

# houses the interactive clustering loop
def interactive_clustering (indv_instance, data):
  algorithm = "agglo"
  penalty = True

  print("Starting initial clustering")
  print("Algorithm: ", algorithm)
  print("15% penalty to 2-cluster clusterings applied")

  # perform the first clustering
  labeled_dataset = start_initial_clustering(data, algorithm, penalty)
  if labeled_dataset is None:
    return

  print("Initial clustering completed.")

  # create instance for interactive plot functionality
  plot_instance = InteractivePlot(indv_instance, labeled_dataset)

  # adjustment loop
  while True:
    if plot_instance.end_clustering:
      return
    
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
      return
    
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
            
    