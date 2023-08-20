from code.utils import create_basic_scatter, delete_legend_plot

import matplotlib.pyplot as plt
import pandas as pd 
import datetime 
import numpy as np
from scipy.stats import gaussian_kde, percentileofscore
import os, sys
from datetime import datetime, timedelta

########################################################################################################################################################################################################

# creates the plot for interval analysis
# creates the plot for interval analysis
def create_interval_plot (data, filepath):
  # Sort the dataframe by hour in ascending order
  data = data.sort_values(by='hour')

  # Get the unique dates in the dataframe
  dates = data['hour'].dt.date.unique()

  # Plot the data
  data_width = 24 / 2
  data_height = len(dates) / 2

  fig, ax = plt.subplots(figsize=(data_width, data_height))

  # Plot the gridlines
  ax.grid(True, which='both', linestyle='-', color='black', linewidth=1)

  # Iterate over each date (y-axis)
  for i, date in enumerate(dates):
    # Filter the dataframe for the current date
    date_df = data[data['hour'].dt.date == date]

    # Get the y-coordinate for the current date
    y = i

    # Iterate over each row of the current day (x-axis)
    for _, row in date_df.iterrows():
      hour = row['hour']
      nestingsite = row['nestingsite']

      # Get the x-coordinate for the current hour
      x = hour.hour + hour.minute / 60
      # get the relevant parameters
      color = 'green' if nestingsite else 'gray'
      # color the corresponding square
      patch = plt.Rectangle((x, y), 1, 1, facecolor=color, edgecolor='black')
      ax.add_patch(patch)
      # nighttime point; make darker
      if not row['daytime']:
        patch = plt.Rectangle((x, y), 1, 1, facecolor='black', edgecolor='black', alpha=0.3)
        ax.add_patch(patch)

  # Set the x-axis label and limits
  ax.set_xlabel('Time')
  ax.set_xlim(0, 24)
  xticks = ax.xaxis.get_major_ticks()
  xticks[-1].label1.set_visible(False)
  ax.set_xticks(range(0, 24))

  # Set the y-axis label and tick labels
  ax.set_ylabel('Date')
  ax.set_yticks(range(len(dates)))
  ax.set_yticklabels([date.strftime('%b %d') for date in dates])

  # makes some changes for neatness
  ax.yaxis.set_tick_params(width=0)
  yticks = ax.yaxis.get_major_ticks()
  yticks[-1].label1.set_visible(False)

  # Invert the y-axis to display the earliest date at the top
  ax.invert_yaxis()
  
  # Automatically scale the plot to make rectangles square-shaped
  ax.set_aspect('equal')

  # Adjust the subplot parameters to fit the plot elements
  plt.tight_layout()

  # save the plot
  print("Saving plot to", filepath)
  plt.savefig(filepath, bbox_inches='tight', dpi=200)
  i = filepath.find("plots/")
  all_plots_path = filepath[i:i+5] + "/analysis" + filepath[i+5:]
  print("and to", all_plots_path)
  plt.savefig(all_plots_path, bbox_inches='tight', dpi=200)

  # Show the plot
  plt.show()

########################################################################################################################################################################################################

def nesting_site_interval (data):
  # Create a list of whole hours within the dataframe range
  start_hour = data['timestamp'].min().floor('H')
  end_hour = data['timestamp'].max().ceil('H')
  hour_range = pd.date_range(start=start_hour, end=end_hour, freq='H')

  # Create an empty result dataframe
  result = pd.DataFrame(columns=['hour', 'nearest_timestamp', 'nestingsite' 'daytime'])

  # Create an empty list to store individual hour series
  hour_dfs = []

  # Iterate over each whole hour
  for hour in hour_range:
    hour_start = hour - timedelta(minutes=15)
    hour_end = hour + timedelta(minutes=15)

    # Filter the dataframe for timestamps within 15 minutes before and after the current hour
    filtered_data = data[(data['timestamp'] >= hour_start) & (data['timestamp'] <= hour_end)]

    if len(filtered_data) > 0:
      # Find the nearest timestamp to the hour, save the index
      nearest_timestamp = filtered_data['timestamp'].apply(lambda x: abs((x - hour).total_seconds())).idxmin()

      # Extract the cluster label and name for the nearest timestamp
      nestingsite = filtered_data.loc[nearest_timestamp, 'nestingsite']

      # Create a temporary dataframe for the current hour result
      hour_df = pd.DataFrame({
          'hour': [hour],
          'nearest_timestamp': [data.loc[nearest_timestamp, 'timestamp']],
          'nestingsite': [nestingsite],
          'daytime': [data.loc[nearest_timestamp, 'daytime']]
      })

      # Append the temporary dataframe to the list of hour dataframes
      hour_dfs.append(hour_df)

  result = pd.concat(hour_dfs, ignore_index=True)

  return result

########################################################################################################################################################################################################

def evaluate_nesting_site(data, total_times_list, proportion_time_dict, filepath):
  print("Evaluating the results.. Creating some plots and doing maths")

  print("\nProportion of time spend at nesting site compared to total amount of time we have of each day.")
  percentages = list(proportion_time_dict.values())
  dates = list(proportion_time_dict.keys())

  # create bar plot
  fig, ax = plt.subplots()
  plt.bar(dates, percentages)
  plt.xticks(rotation=45)
  ax.set_xlabel('Date')
  ax.set_ylabel('Percentage')

  # save plot
  print("Saving plot to", filepath)
  plt.savefig(filepath, bbox_inches='tight', dpi=200)
  i = filepath.find("plots/")
  all_plots_path = filepath[i:i+5] + "/analysis" + filepath[i+5:]
  print("and to", all_plots_path)
  plt.savefig(all_plots_path, bbox_inches='tight', dpi=200)

  plt.show()

  print("\nPress enter to continue")
  _ = input()

  # get results
  os.system('cls')
  print("Interval plot, showing at each hour if the bird is at the nesting site or not.")

  result = nesting_site_interval(data)
  i = filepath.find('Proportion')
  filepath = filepath[:i] + 'Interval' + filepath[i+10:]
  create_interval_plot(result, filepath)

########################################################################################################################################################################################################

# analyze the nesting site. For each day in the data, create a list of the time periods spend on the nest
def analyze_nesting_site (data):
  print("Analyzing the nesting site - calculating time spend at the nesting site per day.")
  # find the first and last date in the data
  first_day = data.at[0, 'timestamp'].date()
  last_day = data.iloc[-1]['timestamp'].date()

  total_time_list = []
  proportion_time_dict = {}

  current_date = first_day

  # loop through each day
  while current_date <= last_day:
    # Select the data for the current day
    day_start = datetime.combine(current_date, datetime.min.time())
    day_end = datetime.combine(current_date, datetime.max.time())

    current_day_data = data[
        (data['timestamp'] >= day_start) &
        (data['timestamp'] <= day_end)
    ]

    day_time_list = []
    day_total_time = timedelta()
    entry_timestamp = None
    at_nest = False

    # go through every row of this day
    for index, row in current_day_data.iterrows():
      # first row, not at nest
      if not row['nestingsite'] and entry_timestamp is None:
        entry_timestamp = row['timestamp']

      # enter the nest
      if row['nestingsite'] and not at_nest:
        # time spend outside of nest
        if entry_timestamp is not None:
          exit_timestamp = current_day_data.at[index-1, 'timestamp']
          time_spend = exit_timestamp - entry_timestamp
          day_total_time += time_spend
        # update variables
        at_nest = True
        entry_timestamp = row['timestamp']
      
      # leave the nest
      if not row['nestingsite'] and at_nest:
        at_nest = False
        exit_timestamp = current_day_data.at[index-1, 'timestamp']

        # update variables
        time_spend = exit_timestamp - entry_timestamp

        day_time_list.append(time_spend)
        day_total_time += time_spend

        # new start time
        entry_timestamp = row['timestamp']

      # last row
      if index == current_day_data.index.max():
        exit_timestamp = row['timestamp']
        time_spend = exit_timestamp - entry_timestamp
        day_total_time += time_spend
        if row['nestingsite']:
          day_time_list.append(time_spend)
        
    if day_total_time > timedelta():
      # add times for this day to the complete list
      total_time_list.append(day_time_list)
      # calculate proportion of time spend on the nest
      nest_time = sum(day_time_list, timedelta())
      prop = (nest_time.total_seconds() / day_total_time.total_seconds()) * 100
      proportion_time_dict[current_date] = prop

    # move to next day
    current_date += timedelta(days=1)

  return total_time_list, proportion_time_dict

########################################################################################################################################################################################################

def show_nestingsite_location (x, y, box, aspect, map, filepath):
  fig, ax = plt.subplots(figsize = (8,7))
  ax.set_xlim(box[0],box[1])
  ax.set_ylim(box[2],box[3])

  ax.scatter(x, y, zorder=1, alpha=1, c='red', s=20)
  map = plt.imread(map)
  ax.imshow(map, zorder=0, extent = box, aspect = aspect)

  plt.xticks([])
  plt.yticks([])

  title =  str(y) + ' latitude, ' + str(x) + " longitude"
  plt.title(title)

  # save the plot
  print("Saving plot to", filepath)
  plt.savefig(filepath, bbox_inches='tight', dpi=200)

  i = filepath.find("plots/")
  all_plots_path = filepath[i:i+5] + "/clusterings" + filepath[i+5:]
  print("and to", all_plots_path)
  plt.savefig(all_plots_path, bbox_inches='tight', dpi=200)

  plt.show()

########################################################################################################################################################################################################

# determine if we located a nesting site
def validate_nestingsite (indv_instance, data, pltname):
  percentile = 85
  while True:
    # filter data by percentile
    highdensity_data = data[data['percentile'] >= percentile].copy()
    leftover_data = data[data['percentile'] < percentile].copy()

    os.system('cls')
    print("The following plot contains the data included in the " + str(percentile) + "th percentile based on the kernel density analysis.")
    print("Please observe the result and determine if you would like to use this area, with these points, as the nesting site for further analysis.\n")

    # show the resulting data
    x, y, box, aspect, map, _ = indv_instance.return_plot_parameters(highdensity_data, 'Nesting site')
    filepath = indv_instance.return_analysis_plotname(indv_instance.clustering_name, "nest", pltname)
    create_basic_scatter(x, y, box, aspect, map, filepath, None, None, None, False, True)

    print("Type 'cont' or press enter if you accept this nesting site and want to continue analysis.")
    print("Type any round number between 0 and 100 if you want to use a different percentile.")
    print("Type 'exit' if you want to cancel the analysis and return to the main menu.")

    user_input = input(">>> ")
    if user_input == 'cont' or len(user_input) == 0:
      break
    if user_input == 'exit':
      os.system('cls')
      return False, None, None
    
    if user_input.isdigit():
      user_input = int(user_input)
      if user_input >= 0 and user_input <= 100:
        percentile = user_input
      else:
        print("Invalid number.")
    else:
      print("Invalid option.")


  highdensity_data['nestingsite'] = True
  leftover_data['nestingsite'] = False

  sorted_highdensity_data = highdensity_data.sort_values(by=['percentile'], ascending=False).copy()
  point = sorted_highdensity_data.iloc[0]
  
  # save the plot
  _, _, box, aspect, map, _ = indv_instance.return_plot_parameters(None, '_')
  x = point['location-long']
  y = point['location-lat']
  filepath = indv_instance.return_analysis_plotname(indv_instance.clustering_name, "nest-loc", pltname)
  os.system('cls')
  print("Plotting the single most dense point to identify the location of the possible nesting site.")
  print("Coordinates of the point (lat, long): " + str(y) + ", " + str(x))
  show_nestingsite_location(x, y, box, aspect, map, filepath)
  
  return True, highdensity_data, leftover_data

########################################################################################################################################################################################################

def create_density_plot (kde, x, y, box, aspect, map, filepath):
  cmap = "Reds"
  xmin = min(x)
  xmax = max(x)
  ymin = min(y)
  ymax = max(y)

  threshold = 80

  # create grid of points
  xx, yy = np.mgrid[xmin:xmax:100j, ymin:ymax:100j]

  # calculate estimated density for each point
  positions = np.vstack([xx.ravel(), yy.ravel()])
  f = np.reshape(kde(positions).T, xx.shape)

  # create the plot
  fig, ax = plt.subplots()
  # set levels for colors
  levels = np.linspace(threshold, np.max(f), 20)
  ax.contourf(xx, yy, f, cmap=cmap,  zorder=1, vmin=threshold, levels=levels, alpha=0.8)

  #ax.scatter([xmin, xmax], [ymin, ymax], c='b', s=15)
  
  map = plt.imread(map)
  ax.imshow(map, zorder=0, extent = box, aspect = aspect)

  plt.xticks([])
  plt.yticks([])

  print("Saving plot to", filepath)
  plt.savefig(filepath, bbox_inches='tight', dpi=200)
  plt.show()

########################################################################################################################################################################################################

# perform kernel density analysis on the given data
def run_kernel_density (data):
  # Combine coordinates into a 2D array
  x = data['location-long']
  y = data['location-lat']
  points = np.vstack([x, y])
  # Perform Gaussian kernel density estimation
  kde = gaussian_kde(points)

  # Evaluate the density at each point
  densities = kde.evaluate(points)

  # add points and density to dataframe
  data['density'] = densities
  result = pd.DataFrame(data)

  # sort density values
  result = result.sort_values(by='density')

  # calculate the percentiles
  sorted_densities = result['density'].values.tolist()
  percentiles = [percentileofscore(sorted_densities, density) for density in sorted_densities]

  # finalize dataframe
  result['percentile'] = percentiles
  result = result[['timestamp', 'location-long', 'location-lat', 'daytime', 'percentile']]
  result = result.sort_values(by='timestamp')

  return result, kde, x, y