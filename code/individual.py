import pickle
import sqlite3
import os
import matplotlib.colors as mcolors


# database path
DB_PATH = "database/individual_data.db"

class Individual:
  def __init__(self, animal_id, year, individual_index):
    self.animal_id = animal_id
    self.year = year
    self.index = individual_index

    self.db_id =    str(self.animal_id) + "_" + str(self.year) + "_" + str(self.index)
    self.file_id =  str(self.animal_id) + "-" + str(self.year) + "-" + str(self.index)

    self.main_dir = "individuals/"
    self.clustering_name = "not given"

    self.cmap = None

  ########################################################################################################################################################################################################  

  def __str__(self):
    output = []
    output.append("Name of current set: " + self.set_name)
    output.append("Animal id: " + str(self.indv_id))
    output.append("Indvidual index: " + str(self.i))
    output.append("Year: " + str(self.year))

    return "\n".join(output)

  ########################################################################################################################################################################################################

  # creates a custom color map that assigns colors based on the cluster names the user provided
  def create_custom_cmap (self, cluster_names):
    custom_cmap = []
    # greens
    colors_territory =  ['#468a1e', '#0f4d19', '#4da157', '#00d111'] # checked and good
    # blues
    colors_club =       ['#3d91cc', '#00d4db', '#4846f0', '#0c236e',
                         '#3cbcd6', '#22435c', '#639992', '#79f7e7']
    # reds/oranges
    colors_secondary =  ['#8f0000', '#ed894e', '#ba4318', '#7d4300',
                         '#b84040', '#b89733'] # checked and good except for last two
    # purples, pinks
    colors_other =      ['#6b418a', '#9424ab', '#5e5e5e', '#632936', # checked and good
                         '#5c264f', '#ba0054', '#f394ff', '#ff00b3']

    for entry in cluster_names:
      if ('club' in entry or 'sea' in entry or 'lake' in entry or 'river' in entry or 'water' in entry or 'coast' in entry or 'harbor' in entry) and len(colors_club) > 0:
        colors = colors_club
      elif ('fields' in entry or 'field' in entry) and len(colors_secondary) > 0:
        colors = colors_secondary
      elif 'territory' in entry and len(colors_territory) > 0:
        colors = colors_territory
      else:
        colors = colors_other

      custom_cmap.append(colors[0])
      colors.pop(0)

    self.cmap = mcolors.ListedColormap(custom_cmap)
    return self.cmap

  ########################################################################################################################################################################################################

  # saves the data for this clustering to the database
  def save_cluster_data (self, cluster_names):
    pickled_names = pickle.dumps(cluster_names)
    pickled_cmap = pickle.dumps(self.cmap)

    data_entry = [self.db_id, self.animal_id, self.year, self.index, self.clustering_name, pickled_names, pickled_cmap]

    # path
    db_path = "database/individual_data.db"

    # connect
    connect = sqlite3.connect(db_path)
    cursor = connect.cursor()

    try:
      cursor.execute('INSERT INTO cluster_data VALUES (?,?,?,?,?,?,?)', data_entry)
    except sqlite3.IntegrityError:
      # delete current entry if one already exists
      cursor.execute('DELETE FROM cluster_data WHERE id=? AND clustering_name=?', (self.db_id, self.clustering_name))
      cursor.execute('INSERT INTO cluster_data VALUES (?,?,?,?,?,?,?)', data_entry)

    connect.commit()
    connect.close()

  ########################################################################################################################################################################################################

  def load_cluster_data (self):
    connect = sqlite3.connect(DB_PATH)
    cursor = connect.cursor()

    cursor.execute('SELECT * FROM cluster_data WHERE id = ? AND clustering_name=?', (self.db_id, self.clustering_name))
    entries = cursor.fetchall()

    connect.close()

    if entries is not None:
      # multiple clusterings for this data, ask user which one
      if len(entries) > 1:
        while True:
          print("There are multiple clusterings saved for this dataset. Which one would you like to analyse?")
          for i, entry in enumerate(entries):
            print("[{}] {}".format(i, entry[4]))
          user_input = input(">>> ")

          # check if input is a valid option
          if user_input.isdigit():
            user_input = int(user_input)
            if not (user_input >= 0 and user_input < len(entries)):
              print("ERROR: Invalid choice, please select the index of the entry you want to use\n")
            else:
              break
          else:
            print("ERROR: Invalid id\n")
      else:
        entry = entries[0]

      self.clustering_name = entry[4]
      self.cluster_names = pickle.loads(entry[5])
      self.cmap = pickle.loads(entry[6])

      print("Succesfully loaded clustering data with database id", self.db_id)
      print("Dataset name:", self.clustering_name, "\nCluster names:", self.cluster_names, "\n")
      return True
    else:
      print("Sorry, the database id", self.db_id, "is not in the database.")
      return False

  ########################################################################################################################################################################################################

  # loads data for this individual instance from the database
  def load_individual_data (self):
    # connect
    connect = sqlite3.connect(DB_PATH)
    cursor = connect.cursor()

    cursor.execute('SELECT * FROM indv_data WHERE id = ?', (self.db_id,))
    entry = cursor.fetchone()

    connect.close()

    if entry is not None:
      self.map_path = entry[4]
      self.plt_aspect = entry[5]
      self.min_long = entry[6]
      self.max_long = entry[7]
      self.min_lat = entry[8]
      self.max_lat = entry[9]

      print("Succesfully loaded individual data with database id", self.db_id)
      return True
    else:
      print("Sorry, the database id", self.db_id, "is not in the database.")
      return False
  
  
  ########################################################################################################################################################################################################

  def return_analysis_plotname (self, title, Atype, pltname):
    plot_dir = os.path.join(self.return_base_dir(), "plots")

    if Atype == "prop":
      name = "Proportion Analysis"
    elif Atype == "interval": 
      name = "Interval Analysis" 
    elif Atype == "density": 
      name = "Nestingsite Density"
    elif Atype == "nest":
      name = "Nestingsite"
    elif Atype == 'nest-loc':
      name = "Nestingsite Location"
    else:
      name = "Nestingsite Proportion"
    
    if pltname is not None:
      filename = self.file_id + " " + title + " (" + name + "-" + pltname + ").png"
    else:
      filename = self.file_id + " " + title + " (" + name + ").png"

    filepath = os.path.join(plot_dir, filename).replace("\\", "/")
    return filepath

########################################################################################################################################################################################################

  # return all the relevant data and parameters for a plot
  def return_plot_parameters (self, data, title):
    # get x and y data
    if data is not None:
      x = data['location-long'].values.tolist()
      y = data['location-lat'].values.tolist()
    else:
      x = None
      y = None

    # get plot info
    box = (self.min_long, self.max_long, self.min_lat, self.max_lat)

    # create file path
    plot_dir = os.path.join(self.return_base_dir(), "plots")
    filename = str(self.file_id) + " " + title + ".png"

    filepath = os.path.join(plot_dir, filename).replace("\\", "/")

    return x, y, box, self.plt_aspect, self.map_path, filepath

  ########################################################################################################################################################################################################

  def return_base_dir (self):
    dir = self.db_id
    return os.path.join(self.main_dir, dir)

  ########################################################################################################################################################################################################

  # return path to the data folder of this individual for given year and index
  def return_data_filepath (self, datatype):
    data_dir = os.path.join(self.return_base_dir(), "data") 

    if datatype == 'clustered':
      file_name = str(self.file_id) + "-" + datatype + ' [' + self.clustering_name + '].csv'
    else:
      file_name = str(self.file_id) + "-" + datatype + ".csv"

    file_path = os.path.join(data_dir, file_name)

    return file_path
