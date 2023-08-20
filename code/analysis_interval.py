import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta


########################################################################################################################################################################################################

def create_interval_plot (data, cmap, filepath):
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

  legend_colors = []
  legend_labels = []

  # Iterate over each date (y-axis)
  for i, date in enumerate(dates):
    # Filter the dataframe for the current date
    date_df = data[data['hour'].dt.date == date]

    # Get the y-coordinate for the current date
    y = i

    # Iterate over each row of the current day (x-axis)
    for _, row in date_df.iterrows():
      hour = row['hour']
      cluster_label = row['cluster_label']

      # Get the x-coordinate for the current hour
      x = hour.hour + hour.minute / 60
      # get the relevant parameters
      color = cmap.colors[cluster_label]
      label = row['cluster_name']
      # color the corresponding square
      patch = plt.Rectangle((x, y), 1, 1, facecolor=color, edgecolor='black', label=label)
      ax.add_patch(patch)
      # nighttime point; make darker
      if not row['daytime']:
        patch = plt.Rectangle((x, y), 1, 1, facecolor='black', edgecolor='black', alpha=0.3)
        ax.add_patch(patch)

      if color not in legend_colors: legend_colors.append(color)
      if label not in legend_labels: legend_labels.append(label)

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

  # Create a legend based on the unique labels
  max_col = len(legend_colors) if len(legend_colors) <= 4 else 4
  ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, facecolor=color, edgecolor='black') for color in legend_colors],
          labels=legend_labels, loc='lower center', ncol=max_col, bbox_to_anchor = (0.5, 1), fontsize=20)
  
  # save plot with legend
  print("Saving plot to", filepath)
  plt.savefig(filepath, bbox_inches='tight', dpi=200)
  i = filepath.find("plots/")
  all_plots_path = filepath[i:i+5] + "/analysis" + filepath[i+5:]
  print("and to", all_plots_path)
  plt.savefig(all_plots_path, bbox_inches='tight', dpi=200)

  # Show the plot
  plt.show()

########################################################################################################################################################################################################

# performs the interval analysis
def interval_analysis (data):
  # Create a list of whole hours within the dataframe range
  start_hour = data['timestamp'].min().floor('H')
  end_hour = data['timestamp'].max().ceil('H')
  hour_range = pd.date_range(start=start_hour, end=end_hour, freq='H')

  # Create an empty result dataframe
  result = pd.DataFrame(columns=['hour', 'nearest_timestamp', 'cluster_label', 'cluster_name', 'daytime'])

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
      cluster_label = filtered_data.loc[nearest_timestamp, 'label']
      cluster_name = filtered_data.loc[nearest_timestamp, 'cluster']

      # Create a temporary dataframe for the current hour result
      hour_df = pd.DataFrame({
          'hour': [hour],
          'nearest_timestamp': [data.loc[nearest_timestamp, 'timestamp']],
          'cluster_label': [cluster_label],
          'cluster_name': [cluster_name],
          'daytime': [data.loc[nearest_timestamp, 'daytime']]
      })

      # Append the temporary dataframe to the list of hour dataframes
      hour_dfs.append(hour_df)

  result = pd.concat(hour_dfs, ignore_index=True)

  return result