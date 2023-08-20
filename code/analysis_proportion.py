from code.utils import return_x_values

import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta


########################################################################################################################################################################################################

# creates the plot for proportion analysis
def create_proportion_plot (period_start, period_end, proportion_list, cluster_names, filepath, cmap):
  x = return_x_values(period_start, period_end)
  y = np.row_stack(proportion_list)

  # Create a stacked bar plot
  fig, ax = plt.subplots()

  # create the bars
  bottom = np.zeros(len(x))

  for i, cluster in enumerate(cluster_names):
    ax.bar(x, y[:, i], bottom=bottom, label=cluster, width=1.0, color=cmap.colors[i])
    bottom += y[:, i]

  xticks = []
  xtick_labels = []

  # create xtick labels at start of the month
  for i, date in enumerate(x):
    if '01' in date or i == 0:
      xticks.append(i)
      xtick_labels.append(date)
  xticks.append(i)
  xtick_labels.append(x[-1])

  # set some plot parameters
  ax.set_xticks(xticks)
  ax.set_xticklabels(xtick_labels)
  ax.set_xlabel('Date')
  ax.set_ylabel('Percentage')
  ax.margins(x=0)

  plt.xticks(rotation = 45)

  # save plot with legend
  max_col = len(cluster_names) if len(cluster_names) <= 4 else 4
  ax.legend(labels=cluster_names, loc='lower center', ncol=max_col, bbox_to_anchor = (0.5, 1))
  
  print("Saving plot to", filepath)
  plt.savefig(filepath, bbox_inches='tight', dpi=200)
  i = filepath.find("plots/")
  all_plots_path = filepath[i:i+5] + "/analysis" + filepath[i+5:]
  print("and to", all_plots_path)
  plt.savefig(all_plots_path, bbox_inches='tight', dpi=200)

  plt.show()

########################################################################################################################################################################################################

# perform the proportion analysis
def proportion_analysis (data, period_start, period_end, cluster_names):
  proportion_list = []
  included_clusters = []

  current_date = period_start
  while current_date <= period_end:
    # Get the start and end timestamps for the current day
    day_start = datetime.combine(current_date, datetime.min.time())
    day_end = datetime.combine(current_date, datetime.max.time())

    # Select the data for the current day
    current_day_data = data[
        (data['timestamp'] >= day_start) &
        (data['timestamp'] <= day_end)
    ]

    proportions = []
    # if we have data for this day
    if current_day_data.shape[0] > 0:
      current_cluster = None
      entry_timestamp = None

      time_diffs = {}

      # move through the individual day
      for index, row in current_day_data.iterrows():
        # First cluster
        if current_cluster is None:
          current_cluster = row['cluster']
          entry_timestamp = row['timestamp']
          if current_cluster not in included_clusters:
            included_clusters.append(current_cluster)
        # new cluster
        elif row['cluster'] != current_cluster:
          # Exit from the previous cluster
          exit_timestamp = current_day_data.at[index-1, 'timestamp']
          time_diff = exit_timestamp - entry_timestamp
          if time_diff.total_seconds() == 0: time_diff = timedelta(minutes=10)

          # save time difference for this cluster
          if current_cluster not in time_diffs.keys():
            time_diffs[current_cluster] = []
          time_diffs[current_cluster].append(time_diff)

          # Start a new cluster
          current_cluster = row['cluster']
          entry_timestamp = row['timestamp']
          if current_cluster not in included_clusters:
            included_clusters.append(current_cluster)
        # last entry
        elif index == current_day_data.index.max():
          # Exit from the previous cluster
          exit_timestamp = row['timestamp']
          time_diff = exit_timestamp - entry_timestamp
          if time_diff.total_seconds() == 0: time_diff = timedelta(minutes=10)

          # save time difference for this cluster
          if current_cluster not in time_diffs.keys():
            time_diffs[current_cluster] = []
          time_diffs[current_cluster].append(time_diff)

      # total duration we have for this day
      total_duration = timedelta()
      for cluster in sorted(time_diffs):
        total_duration += sum(time_diffs[cluster], timedelta())

      # sum up time per cluster
      for cluster in cluster_names:
        if cluster in time_diffs.keys():
          total_cluster_duration = sum(time_diffs[cluster], timedelta())
          prop = total_cluster_duration / total_duration * 100
        else: prop = 0
        proportions.append(prop)
    # no data for this day
    else:
      for cluster in cluster_names:
        proportions.append(0)

    proportion_list.append(proportions)

    # Move to the next day
    current_date += timedelta(days=1)
  
  return proportion_list, included_clusters
