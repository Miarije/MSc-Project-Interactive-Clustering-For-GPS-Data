from code.utils import return_color_map, return_data_per_cluster
from code.clustering import adjust_reclustering, adjust_merge
from code.database import save_clustering

import matplotlib.pyplot as plt
from matplotlib.artist import Artist
from matplotlib.widgets import Button
import os
from time import sleep

class InteractivePlot():
  def __init__(self, indv_instance, labeled_dataset):
    # clustering variables
    self.clusterlist = []
    self.revisions = 0
    self.end_clustering = False
    self.saved_clustering = False

    # data variables
    self.backup = None
    self.indv_instance = indv_instance
    self.data = labeled_dataset

    # plot variables
    self.fig = None
    self.cid = None
    self.cmap = None
    self.text = None
    self.buttons = []
    self.scatters = {}
    self.clicked = {}

    # keeping track of adjustments
    self.adjustments = 0
    self.merges = 0
    self.reclusterings = 0
    self.undos = 0

########################################################################################################################################################################################################

  # handles click events on scatter points, updates cluster list and changes color of pointss
  def on_click (self, event):
    label = int(event.artist.get_label())
    
    # update clusterlist
    if label in self.clusterlist:
      self.clusterlist.remove(label)
    else:
      self.clusterlist.append(label)

    # update point colors
    if label in self.clicked:
      Artist.update(event.artist, {'color': self.cmap.colors[label]})
      del self.clicked[label]
    else:
      Artist.update(event.artist, {'color': 'gray'})
      self.clicked[label] = True

    self.text.set_text("Selected clusters: " +  ', '.join(map(str, self.clusterlist)))
    self.fig.canvas.draw()

  ########################################################################################################################################################################################################

  # reclusters the selected clusters using DBSCAN
  def recluster(self, algorithm):
    # parameters
    clusters = self.clusterlist
    self.revisions += 1
    penalty = False

    print("Reclustering the following clusters:", set(clusters))
    labeled_dataset = adjust_reclustering(self.data, algorithm, clusters, penalty)
    if labeled_dataset is None or len(labeled_dataset['label'].unique().tolist()) > 50:
      self.revisions -= 1
      if len(labeled_dataset['label'].unique().tolist()) > 50:
        print("Too many clusters! There is a limit of 50 clusters. Please merge some before reclustering.")
      print("Clustering cancelled. Press enter to continue from the last valid clustering.")
      _ = input()
    else:
      # adjust data variables
      self.backup = self.data.copy()
      self.data = labeled_dataset.copy()
      self.clusterlist = []
      self.clicked = {}

      # parameters for plot
      title = self.indv_instance.clustering_name + " | reclustered data-" + str(self.revisions)
      x, y, box, aspect, map, filepath = self.indv_instance.return_plot_parameters(labeled_dataset, title)
      labels = labeled_dataset['label'].values.tolist()

      # create plot
      saveFile = False
      self.create_interactive_plot(x, y, box, aspect, map, filepath, labels, saveFile)

  ########################################################################################################################################################################################################

  # merges the selected clusters
  def merge(self):
    # parameters
    clusters = self.clusterlist
    self.revisions += 1

    print("Merging the following clusters:", set(clusters))

    labeled_dataset = adjust_merge(self.data, clusters)

    # adjust data variables
    self.backup = self.data.copy()
    self.data = labeled_dataset.copy()
    self.clusterlist = []
    self.clicked = {}

    # parameters for plot
    title = self.indv_instance.clustering_name + " | reclustered data-" + str(self.revisions)
    x, y, box, aspect, map, filepath = self.indv_instance.return_plot_parameters(labeled_dataset, title)
    labels = labeled_dataset['label'].values.tolist()

    # create plot
    saveFile = False

    self.create_interactive_plot(x, y, box, aspect, map, filepath, labels, saveFile)

########################################################################################################################################################################################################

  # reverts current data to the backup, if possible
  def undo(self):
    self.clusterlist = []

    if not self.backup.equals(self.data):
      print("Resetting the current labaled dataset to the available backup.")
      self.data = self.backup.copy()
      self.revisions -= 1
    else:
      print("The current backup is identical to the current labeled dataset. You can only undo once per adjustment.")
    
    # parameters for plot
    title = self.indv_instance.clustering_name + " | reclustered data-" + str(self.revisions)
    x, y, box, aspect, map, filepath = self.indv_instance.return_plot_parameters(self.data, title)
    labels = self.data['label'].values.tolist()

    # create plot
    saveFile = False

    self.create_interactive_plot(x, y, box, aspect, map, filepath, labels, saveFile)
  
########################################################################################################################################################################################################

  # prepare to save the current clustering
  def save (self):
    os.system('cls')
    print("Are you sure you wish to end the clustering and save the current labeled data?")
    while True:
      user_input = input("yes/no: ").lower()
      #os.system('cls')
      if user_input == 'yes':
        save_clustering (self.indv_instance, self.data)
        self.end_clustering = True
        self.saved_clustering = True
        print("Stats for this clustering:")
        print("Total adjustments | reclusterings | merges | undos")
        print("{}, {}, {}, {}".format(self.adjustments, self.reclusterings, self.merges, self.undos))
        print("Clustering finished! Press enter to return to the main menu.")
        _ = input()
        return
      elif user_input == 'no':
        break

########################################################################################################################################################################################################

  # cancel the clustering
  def exit (self):
    while True:
      print("Are you sure you wish to end the clustering? All your progress will be deleted.")
      user_input = input("yes/no: ").lower()
      os.system('cls')
      if user_input == 'yes':
        print("Clustering cancelled.")
        self.end_clustering = True
        return
      elif user_input == 'no':
        break

########################################################################################################################################################################################################

  # handles the button event, disconnects previous event connections
  def on_button (self, label, plot):
    # close the plot, doesn't actuall do it for whatever reason
    plt.close(plot)

    # Disconnect event connections before closing the plot
    self.fig.canvas.mpl_disconnect(self.cid)
    for button in self.buttons:
      button.disconnect_events()
    
    if label == 'recluster':
      if len(self.clusterlist) > 0:
        self.adjustments += 1
        self.reclusterings += 1
        self.recluster('dbscan')
      else:
        print("Please select one or more clusters to recluster on.")
    elif label == 'merge':
      if len(self.clusterlist) > 1:
        self.adjustments += 1
        self.merges += 1
        self.merge()
      else:
        print("Please select two or more clusters to merge.")
    elif label == 'undo':
      self.adjustments += 1
      self.undos += 1
      self.undo()
    elif label == 'save':
      self.save()
    else:
      self.exit()

########################################################################################################################################################################################################

  # create a scatter plot of GPS data on top of a map
  def create_interactive_plot (self, x, y, box, aspect, map, filepath, labels, saveFile):
    self.fig, ax = plt.subplots(figsize = (8,7))

    data_per_cluster = return_data_per_cluster(x,y,labels)
    self.cmap = return_color_map(len(set(labels)))

    # create scatter for each cluster
    for label in set(labels):
      x = data_per_cluster[label]['x']
      y = data_per_cluster[label]['y']

      scatter = ax.scatter(x, y, zorder=1, alpha=1, c=self.cmap.colors[label], label=label, s=10, picker=2)
      self.scatters[label] = scatter
    
    ax.set_xlim(box[0],box[1])
    ax.set_ylim(box[2],box[3])

    # source: https://www.openstreetmap.org/export#map=8/31.815/34.887
    map = plt.imread(map)

    ax.imshow(map, zorder=0, extent = box, aspect = aspect)

    plt.xticks([])
    plt.yticks([])

    # save the image
    if saveFile:
      print("Saving plot to", filepath)
      plt.savefig(filepath, bbox_inches='tight', dpi=200)

    else:
      # connect
      self.cid = self.fig.canvas.mpl_connect('pick_event', self.on_click)

      # create text
      self.text = ax.text(0.3, 1.05, 'Selected clusters: ',
                          transform=ax.transAxes,
                          ha='left', va='top')
      text = ax.text(0.0, 1.05, 'Clusters: ' + str(len(set(labels))) + " | ",
                          transform=ax.transAxes,
                          ha='left', va='top')

      # prepare buttons
      button_positions = [(0.25, 0.05), (0.45, 0.05), (0.65, 0.05), (0.80, 0.95), (0.9, 0.95)]
      button_labels = ['recluster', 'merge', 'undo', 'save', 'exit',]

      self.buttons = []
      # create buttons
      for position, label in zip(button_positions, button_labels):
        button_ax = self.fig.add_axes([position[0], position[1], 0.1, 0.05])
        button = Button(button_ax, label)
        button.on_clicked(lambda event, lbl=label, plt=plt.gcf(): self.on_button(lbl, plt))
        self.buttons.append(button)

    plt.show()

  ########################################################################################################################################################################################################