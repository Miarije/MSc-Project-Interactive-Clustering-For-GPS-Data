from code.utils import input_time_period, create_basic_scatter
from code.analysis_interval import *
from code.analysis_proportion import *
from code.analysis_nestingsite import run_kernel_density, validate_nestingsite, evaluate_nesting_site, analyze_nesting_site, create_density_plot

import pandas as pd
import os

########################################################################################################################################################################################################

# returns data based on the period start and end
def return_analysis_data (indv_instance, period_start, period_end):
  # load and select data
  filepath = indv_instance.return_data_filepath("clustered")
  data = pd.read_csv(filepath, delimiter = ",")
  # conver to datetime
  data['timestamp'] = pd.to_datetime(data['timestamp'])
  # convert to string
  data['cluster'] = data['cluster'].astype(str)

  if period_start == 'first':
     period_start = data.iloc[0]['timestamp']
  if period_end == 'last':
     period_end = data.iloc[-1]['timestamp']

  selected_data = data[
                      (data['timestamp'].dt.date >= period_start.date()) &
                      (data['timestamp'].dt.date <= period_end.date())
  ].reset_index().copy()

  x, y, box, aspect, map, filepath = indv_instance.return_plot_parameters(selected_data, "preview")
  create_basic_scatter(x, y, box, aspect, map, filepath, selected_data['label'].values.tolist(), indv_instance.cmap, indv_instance.cluster_names, False, False)

  return selected_data, period_start, period_end

########################################################################################################################################################################################################

# runs the proportion analysis
def run_proportion_analysis(indv_instance):
  # receive user input for analysis period
  period_start, period_end = input_time_period(indv_instance.year)
  data, period_start, period_end = return_analysis_data(indv_instance, period_start, period_end)

  # run analysis
  print("Starting proportion analysis")
  proportion_list, included_clusters = proportion_analysis(data, period_start, period_end, indv_instance.cluster_names)
  # reorder the list so that the names and colors will match
  included_clusters = [name for name in indv_instance.cluster_names if name in included_clusters]

  # create plot
  print("Press enter to save the plot with the default name, or type a name.")
  user_input = input(">>> ")
  if len(user_input) > 0:
     pltname = user_input
  else:
     pltname = None

  # create plot
  filepath = indv_instance.return_analysis_plotname(indv_instance.clustering_name, "prop", pltname)
  cmap = indv_instance.cmap
  print("Proportion analysis finished, creating the plot.")
  create_proportion_plot(period_start, period_end, proportion_list, included_clusters, filepath, cmap)

  print("Proportion analysis finished.")
  print("Press any key to perform a different analysis or type 'exit' to return to the main menu.")

  user_input = input(">>> ")
  if user_input == 'exit':
     os.system('cls')
     return True
  else:
     os.system('cls') 
     return False

########################################################################################################################################################################################################

def run_interval_analysis(indv_instance):
  period_start, period_end = input_time_period(indv_instance.year)
  data, period_start, period_end = return_analysis_data(indv_instance, period_start, period_end)

  # run analysis
  print("Starting interval analysis")
  result = interval_analysis(data)

  # create plot
  print("Press enter to save the plot with the default name, or type a name.")
  user_input = input(">>> ")
  if len(user_input) > 0:
     pltname = user_input
  else:
     pltname = None

  filepath = indv_instance.return_analysis_plotname(indv_instance.clustering_name, "interval", pltname)
  cmap = indv_instance.cmap
  print("Interval analysis finished, creating the plot.")

  create_interval_plot(result, cmap, filepath)

  print("Interval analysis finished.")
  print("Press any key to perform a different analysis or type 'exit' to return to the main menu.")

  user_input = input(">>> ")
  if user_input == 'exit':
    os.system('cls')
    return True
  else:
     os.system('cls') 
     return False

########################################################################################################################################################################################################

def run_nestingsite_analysis(indv_instance):
    period_start, period_end = input_time_period(indv_instance.year)
    data, period_start, period_end = return_analysis_data(indv_instance, period_start, period_end)
    clusters = data['cluster'].unique().tolist()
    cluster_names = indv_instance.cluster_names
    cluster_list = [cluster for cluster in cluster_names if cluster in clusters]

    # present all clusters
    while True:
      print("Please select the cluster to analyse. This cluster should be your assumed territory.")
      print("Alternatively, type 'all' to perform the density analysis on ALL data, instead of one cluster.")
      print("(Type 'back' to return to the analysis menu.)")
      print("[#] cluster name")
      for i, cluster in enumerate(cluster_list):
        print("[{}] {}".format(i, cluster))

      # select user-chosen cluster
      user_input = input(">>> ").lower()
      if user_input == 'back':
         os.system('cls')
         return
      if user_input == 'all':
         territory = cluster_list
         break
      if user_input.isdigit():
         user_input = int(user_input)
         if user_input >= 0 and user_input < len(indv_instance.cluster_names):
            territory = [cluster_list[user_input]]
            break
         else:
            print("Invalid input.")
      else:
         print("Invalid input")
    
    # separate the data
    territory_data = data[data['cluster'].isin(territory)].copy()
    territory_data[['timestamp', 'location-long', 'location-lat', 'daytime']].drop_duplicates(inplace=True)
    other_data = data[~data['cluster'].isin(territory)].copy()
    other_data = other_data[['timestamp', 'location-long', 'location-lat', 'daytime']]

    result, kde, x, y = run_kernel_density(territory_data)

    print("Press enter to save the plot with the default name, or type a name.")
    user_input = input(">>> ")
    if len(user_input) > 0:
      pltname = user_input
    else:
      pltname = None

    # create a overview of estimate density plot
    x, y, box, aspect, map, filepath = indv_instance.return_plot_parameters(data, indv_instance.clustering_name)
    filepath = indv_instance.return_analysis_plotname(indv_instance.clustering_name, "density", pltname)
    create_density_plot(kde, x, y, box, aspect, map, filepath)
    
    # determine if we have a nesting site
    success, nestingsite_data, leftover_data = validate_nestingsite(indv_instance, result, pltname)
    if not success: 
       return True

    # if so, combine the data
    other_data['nestingsite'] = False
    combined_data = pd.concat([nestingsite_data, other_data, leftover_data], ignore_index=True)
    combined_data = combined_data.sort_values(by='timestamp').reset_index()

    # analyze the nesting site
    print("Data size:", combined_data.shape[0])

    print("Do you want to change the start and end date for the plots?")
    user_input = input("yes/no: ").lower()
    if user_input == 'yes':
      period_start, period_end = input_time_period(indv_instance.year)
      combined_data = combined_data[
                      (combined_data['timestamp'].dt.date >= period_start.date()) &
                      (combined_data['timestamp'].dt.date <= period_end.date())
    ].reset_index().copy()
    total_time_list, proportion_time_list = analyze_nesting_site(combined_data)

    # evaluate the resulting data
    filepath = indv_instance.return_analysis_plotname(indv_instance.clustering_name, "_", pltname)
    evaluate_nesting_site(combined_data, total_time_list, proportion_time_list, filepath)
