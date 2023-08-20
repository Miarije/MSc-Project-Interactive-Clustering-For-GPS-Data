from datetime import datetime, timedelta
import numpy as np
import statistics
import matplotlib.colors as mcolors
import os
import re
import matplotlib.pyplot as plt
import warnings

########################################################################################################################################################################################################

#returns the maximum, minimum, mean and median distances in the given dataset
def calculate_distances(data):
  data = np.array(data)
  distances = np.sqrt(np.sum(np.diff(data, axis=0) ** 2, axis=1))
  max_distance = np.max(distances)
  min_distance = np.min(distances)
  avg_distance = np.mean(distances)
  median_distance = statistics.median(distances)
  return max_distance, min_distance, avg_distance, median_distance

########################################################################################################################################################################################################

# re-arrange the cluster labels
def fix_cluster_labels (labels_original, labels_recluster):
  labels_new = []

  num_of_clusters = len(labels_original) + len(labels_recluster)
  count = len(labels_recluster)

  # go through the total number of clusters
  for i in range(num_of_clusters):
    # skip labels in the original cluster
    if i in labels_original:
      continue
    # create a new list out of each first available label
    else:
      labels_new.append(i)
      count -= 1
      # finished
      if count == 0:
        return labels_new

########################################################################################################################################################################################################

# return a simple, standard color map with distinct colors
def return_color_map (amount):
  custom_colors = ['#ff0000', # 0 bright red        # 1-9 are good together
                   '#18bbc9', # 1 light blue        # 1-23 do okay. some dark ones look similar, but not bad for the amount 
                   '#9423cc', # 2 bright purple
                   '#ff6f00', # 3 bright orange
                   '#876e1c', # 4 dark yellow
                   '#23705d', # 5 dark blue-greenish
                   '#d10fce', # 6 bright pink
                   '#451725', # 7 bordeau
                   '#07b58a', # 8 bright blue-greenish
                   '#33ff00', # 9 bright green
                   '#340d47', # 10 dark purple
                   '#615035', # 11 brown
                   '#cfba21', # 12 light yellow
                   '#0b5e2a', # 13 dark green
                   '#0f3f73', # 14 dark blue
                   '#364520', # 15 darkest green
                   '#b1c400', # 16 bright yellow
                   '#590142', # 17 dark pink                   
                   '#3d1002', # 18 dark red
                   '#504a57', # 19 purple grey ish
                   '#110d40', # 20 darkests blue
                   '#000000', # 21 black
                   '#ffffff', # 22 white
                   '#d9908b', # 23 light pink
                   '#415246', # 24 green grey ish
                   ]
  
  if amount > len(custom_colors):
    print("!Warning! You have more than", len(custom_colors), "clusters. There are only 25 colors available, which means some clusters will now have the same color.")
    difference = amount - len(custom_colors)
    if difference > 25: difference = 25
    extras = custom_colors[:difference]
    custom_colors = custom_colors + extras

  custom_cmap = mcolors.ListedColormap(custom_colors[:amount])

  return custom_cmap

########################################################################################################################################################################################################

# create data and plots folders for the given id
def create_individual_folders (id):
  # Get the current file's directory
  current_dir = os.path.dirname(os.path.abspath(__file__))

  # Get the parent directory
  parent_dir = os.path.dirname(current_dir)

  # individuals directory
  individuals_dir = os.path.join(parent_dir, "individuals")
  if not os.path.exists(individuals_dir):
    os.mkdir(individuals_dir)

  # create new folders
  new_dir = os.path.join(individuals_dir, id)
  os.mkdir(new_dir)

  os.mkdir(os.path.join(new_dir, "data"))
  os.mkdir(os.path.join(new_dir, "plots"))

  print("Created a folder for this individual at", new_dir)
  filename = id.replace("_", "-") + "-processed.csv"
  print("Ensure that the data for this individual is located in", os.path.join(new_dir, "data"), "with name:", filename)

########################################################################################################################################################################################################

# returns a dictionary containing the x,y data separated by cluster
def return_data_per_cluster (x, y, labels):
  data_per_cluster = {}

  # split the data per cluster
  zipped_data = zip(x,y,labels)
  for point in set(zipped_data):
    x, y, label = point
    
    if label in data_per_cluster:
      data_per_cluster[label]['x'].append(x)
      data_per_cluster[label]['y'].append(y)
    else:
      data_per_cluster[label] = {'x': [x], 'y': [y]}

  return data_per_cluster

########################################################################################################################################################################################################

# create a scatter plot of GPS data on top of a map
def create_basic_scatter (x, y, box, aspect, map, filepath, labels, cmap, cluster_names, allowInput, doSave):
  warnings.filterwarnings("ignore")
  fig, ax = plt.subplots(figsize = (8,7))
  scatters = []

  # plotting clusterdata
  if labels is not None:
    if cmap is None:
      cmap = return_color_map(len(set(labels)))

    # plot data per cluster
    data_per_cluster = return_data_per_cluster(x,y,labels)  

    for label in set(labels):
      x = data_per_cluster[label]['x']
      y = data_per_cluster[label]['y']

      if cluster_names is not None:
        scatter = ax.scatter(x, y, zorder=1, alpha=1, c=cmap.colors[label], label=cluster_names[label], s=10, picker=True)
      else:
        scatter = ax.scatter(x, y, zorder=1, alpha=1, c=cmap.colors[label], label=label, s=10, picker=True)
      scatters.append(scatter)

    # create legend
    legend = ax.legend(*scatter.legend_elements(),
                      loc="best", markerscale=2.5)

    ax.add_artist(legend)
    ax.legend()
  else:
    scatter = ax.scatter(x, y, zorder=1, alpha= 0.4, c='b', s=10)

  ax.set_xlim(box[0],box[1])
  ax.set_ylim(box[2],box[3])

  # source: https://www.openstreetmap.org/export#map=8/31.815/34.887
  map = plt.imread(map)

  ax.imshow(map, zorder=0, extent = box, aspect = aspect)

  plt.xticks([])
  plt.yticks([])

  # save the image
  if doSave:
    # Hide the legend
    if labels is not None:
      ax.legend().set_visible(False)
    
    # then save
    print("Saving plot to", filepath)
    plt.savefig(filepath, bbox_inches='tight', dpi=200)

    i = filepath.find("plots/")
    all_plots_path = filepath[i:i+5] + "/clusterings" + filepath[i+5:]
    print("and to", all_plots_path)
    plt.savefig(all_plots_path, bbox_inches='tight', dpi=200)
    
    # bring legend back
    if labels is not None:
      ax.legend().set_visible(True)
      
      # save the plot
      i = filepath.find(".png")
      filepath_2 = filepath[:i] + ' (l)' + filepath[i:]
      plt.savefig(filepath_2, bbox_inches='tight', dpi=200)
      i = filepath.find("plots/")
      j = filepath.find(".png")
      all_plots_path_2 = filepath[i:i+5] + "/clusterings" + filepath[i+5:j] + ' (l)' + filepath[j:]
      plt.savefig(all_plots_path_2, bbox_inches='tight', dpi=200)

  if allowInput:
    plt.show(block=False)
  else: plt.show()

########################################################################################################################################################################################################

def is_valid_filename (filename):
  pattern = r'[<>:"\/|?*]'
  valid = not bool(re.search(pattern, filename))
  if not valid:
    print("This name contains characters that are not allowed in filenames. Please avoid the following characters: < > : \" \\ / | ? *")
  return valid

########################################################################################################################################################################################################

def input_time_period (year):
  # start date
  while True:
    print("Choose the start date for analysis. Use any of the following formats: 'April 1', 'Apr 1', '01-04.")
    print("Press enter without any input to select the first entry in the data as starting date.")

    user_input = input(">>> ")
    os.system('cls')
    if len(user_input) == 0:
      period_start = 'first'
      break
    else:
      period_start = parse_date(user_input, year)
      if period_start is not None:
        break
  
  while True:
    # end date
    print("Choose the end date for analysis. Use any of the following formats: 'April 1', 'Apr 1', '01-04.")
    print("Press enter without any input to select the first entry in the data as starting date.")

    user_input = input(">>> ")
    os.system('cls')
    if len(user_input) == 0:
      period_end = 'last'
      break
    else:
      period_end = parse_date(user_input, year)
      if period_end is not None:
        break
  

  return period_start, period_end

########################################################################################################################################################################################################

def parse_date (date_str, year):
    try: # 01-04
        date = datetime.strptime(date_str, "%d-%m")
    except ValueError:
        try: # April 1
            date = datetime.strptime(date_str, "%B %d")
        except ValueError:
            try: # Apr 1
              date = datetime.strptime(date_str, "%b %d")
            except ValueError:
              try: # 1 April
                date = datetime.strptime(date_str, "%d %B")
              except ValueError:
                print("Invalid date format. Use any of the following formats: 'April 1', 'Apr 1', '01-04.")
                return None

    return date.replace(year=year)  # Set the year to a specific value (e.g., 2023)

########################################################################################################################################################################################################

def return_x_values (period_start, period_end):
  x = []

  current_date = period_start
  while current_date <= period_end:
    # Extract the month and day and format it as month-day
    month_day = current_date.strftime("%b %d")
    x.append(month_day)

    # Move to the next day
    current_date += timedelta(days=1)
  return x

########################################################################################################################################################################################################

def return_hour_list():
  start_hour = 0  # Start hour (0 represents 00:00)
  end_hour = 23  # End hour (23 represents 23:00)

  hours_list = []

  for hour in range(start_hour, end_hour + 1):
      hour_string = f"{hour:02d}:00"
      hours_list.append(hour_string)

  return (hours_list)

########################################################################################################################################################################################################

def delete_legend_plot (filepath):
  i = filepath.find(".png")
  filepath_1 = filepath[:i] + ' (l)' + filepath[i:]
  os.remove(filepath_1)

  i = filepath.find("plots/")
  j = filepath.find(".png")
  filepath_2 = filepath[i:i+5] + "/clusterings" + filepath[i+5:j] + ' (l)' + filepath[j:]
  os.remove(filepath_2)